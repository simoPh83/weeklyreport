"""
Lock Manager for Property Management System
Handles hybrid file-based and database-based locking with heartbeat and timeout
"""
import os
import socket
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import threading


class LockManager:
    """Manages database access locks using hybrid file and database approach"""
    
    LOCK_TIMEOUT_MINUTES = 10
    HEARTBEAT_INTERVAL_SECONDS = 30
    
    def __init__(self, db_path: str, db_manager):
        """
        Initialize LockManager
        
        Args:
            db_path: Path to the database file
            db_manager: Instance of DatabaseManager
        """
        self.db_path = db_path
        self.db_manager = db_manager
        self.lock_file_path = db_path + '.lock'
        self.current_session_id = None
        self.current_user_id = None
        self.current_username = None
        self.has_write_lock = False
        self._heartbeat_thread = None
        self._stop_heartbeat = threading.Event()
        self.machine_name = socket.gethostname()
        self._lock_lost_callback = None
    
    def acquire_write_lock(self, user_id: int, username: str) -> Tuple[bool, Optional[str]]:
        """
        Attempt to acquire write lock for the database
        
        Args:
            user_id: ID of the user requesting the lock
            username: Username of the user requesting the lock
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Clean up stale locks first
        self._cleanup_stale_locks()
        
        # Check for existing locks
        existing_lock = self._get_current_lock_holder()
        if existing_lock:
            return False, f"Database is locked by {existing_lock['username']} on {existing_lock['machine_name']}"
        
        # Try to create file lock
        try:
            # Check if lock file already exists
            if os.path.exists(self.lock_file_path):
                return False, "Lock file already exists"
            
            # Create lock file
            with open(self.lock_file_path, 'w') as f:
                f.write(f"{username}@{self.machine_name}\n")
                f.write(f"{datetime.now().isoformat()}\n")
                f.write(f"{user_id}\n")
        except Exception as e:
            return False, f"Failed to create lock file: {str(e)}"
        
        # Create database session entry
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (user_id, username, is_write_lock, machine_name)
                    VALUES (?, ?, 1, ?)
                """, (user_id, username, self.machine_name))
                self.current_session_id = cursor.lastrowid
                conn.commit()
        except Exception as e:
            # Clean up file lock if database insert fails
            try:
                os.remove(self.lock_file_path)
            except:
                pass
            return False, f"Failed to create database session: {str(e)}"
        
        # Successfully acquired lock
        self.current_user_id = user_id
        self.current_username = username
        self.has_write_lock = True
        
        # Start heartbeat thread
        self._start_heartbeat()
        
        return True, None
    
    def release_write_lock(self):
        """Release the write lock if held by current session"""
        if not self.has_write_lock:
            return
        
        # Stop heartbeat
        self._stop_heartbeat_thread()
        
        # Remove file lock
        try:
            if os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
        except Exception as e:
            print(f"Warning: Failed to remove lock file: {e}")
        
        # Remove database session
        if self.current_session_id:
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM sessions WHERE id = ?", (self.current_session_id,))
                    conn.commit()
            except Exception as e:
                print(f"Warning: Failed to remove database session: {e}")
        
        # Reset state
        self.has_write_lock = False
        self.current_session_id = None
        self.current_user_id = None
        self.current_username = None
    
    def check_write_permission(self) -> Tuple[bool, Optional[str]]:
        """
        Check if current session has write permission
        
        Returns:
            Tuple of (has_permission: bool, lock_holder_info: Optional[str])
        """
        if self.has_write_lock:
            return True, None
        
        # Clean up stale locks
        self._cleanup_stale_locks()
        
        # Check for existing locks
        existing_lock = self._get_current_lock_holder()
        if existing_lock:
            lock_info = f"{existing_lock['username']} on {existing_lock['machine_name']}"
            return False, lock_info
        
        return True, None
    
    def verify_write_lock(self) -> bool:
        """
        Verify that current session still has valid write lock.
        This should be called immediately before any write operation.
        
        Returns:
            bool: True if still holding valid write lock, False otherwise
        """
        if not self.has_write_lock or not self.current_session_id:
            return False
        
        # Check if our session still exists in database
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM sessions 
                    WHERE id = ? AND is_write_lock = 1
                """, (self.current_session_id,))
                
                if cursor.fetchone():
                    # Session still exists
                    return True
                else:
                    # Session was removed - trigger lock lost handling
                    print(f"WARNING: Write lock verification failed - session {self.current_session_id} no longer exists")
                    self._handle_lock_lost()
                    return False
        except Exception as e:
            print(f"Error verifying write lock: {e}")
            return False
    
    def force_unlock(self, admin_user_id: int) -> Tuple[bool, str]:
        """
        Force unlock the database (admin only)
        
        Args:
            admin_user_id: ID of the admin user forcing unlock
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Verify admin privileges
        user = self.db_manager.get_user_by_id(admin_user_id)
        if not user or not user.get('is_admin'):
            return False, "Only administrators can force unlock"
        
        unlocked_items = []
        
        # Remove file lock
        try:
            if os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
                unlocked_items.append("file lock")
        except Exception as e:
            return False, f"Failed to remove lock file: {str(e)}"
        
        # Remove all write lock sessions from database
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE is_write_lock = 1")
                deleted_count = cursor.rowcount
                conn.commit()
                if deleted_count > 0:
                    unlocked_items.append(f"{deleted_count} database session(s)")
        except Exception as e:
            return False, f"Failed to remove database sessions: {str(e)}"
        
        if unlocked_items:
            return True, f"Removed: {', '.join(unlocked_items)}"
        else:
            return True, "No locks found to remove"
    
    def _get_current_lock_holder(self) -> Optional[dict]:
        """Get information about current lock holder"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, machine_name, last_heartbeat
                    FROM sessions
                    WHERE is_write_lock = 1
                    ORDER BY session_start DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            print(f"Error checking lock holder: {e}")
        
        return None
    
    def _cleanup_stale_locks(self):
        """Remove locks that have timed out"""
        timeout_threshold = datetime.now() - timedelta(minutes=self.LOCK_TIMEOUT_MINUTES)
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find stale sessions
                cursor.execute("""
                    SELECT id, username FROM sessions
                    WHERE is_write_lock = 1
                    AND datetime(last_heartbeat) < datetime(?)
                """, (timeout_threshold.isoformat(),))
                
                stale_sessions = cursor.fetchall()
                
                if stale_sessions:
                    # Remove stale sessions
                    cursor.execute("""
                        DELETE FROM sessions
                        WHERE is_write_lock = 1
                        AND datetime(last_heartbeat) < datetime(?)
                    """, (timeout_threshold.isoformat(),))
                    conn.commit()
                    
                    print(f"Cleaned up {len(stale_sessions)} stale lock(s)")
                    
                    # Also remove file lock if exists
                    if os.path.exists(self.lock_file_path):
                        try:
                            os.remove(self.lock_file_path)
                        except:
                            pass
        
        except Exception as e:
            print(f"Error cleaning up stale locks: {e}")
    
    def _update_heartbeat(self):
        """Update the heartbeat timestamp for current session"""
        if not self.current_session_id:
            return
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, check if our session still exists
                cursor.execute("""
                    SELECT id FROM sessions WHERE id = ? AND is_write_lock = 1
                """, (self.current_session_id,))
                
                if not cursor.fetchone():
                    # Session was removed (likely by admin force unlock)
                    print(f"WARNING: Session {self.current_session_id} no longer exists - lock was removed!")
                    self._handle_lock_lost()
                    return
                
                # Update heartbeat
                cursor.execute("""
                    UPDATE sessions
                    SET last_heartbeat = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (self.current_session_id,))
                conn.commit()
        except Exception as e:
            print(f"Error updating heartbeat: {e}")
    
    def _start_heartbeat(self):
        """Start the heartbeat thread"""
        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        self._heartbeat_thread.start()
    
    def _heartbeat_worker(self):
        """Worker function for heartbeat thread"""
        while not self._stop_heartbeat.is_set():
            self._update_heartbeat()
            # Wait for the interval or until stop is signaled
            self._stop_heartbeat.wait(self.HEARTBEAT_INTERVAL_SECONDS)
    
    def _stop_heartbeat_thread(self):
        """Stop the heartbeat thread"""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._stop_heartbeat.set()
            self._heartbeat_thread.join(timeout=2)
    
    def set_lock_lost_callback(self, callback):
        """Set callback to be called when lock is lost unexpectedly"""
        self._lock_lost_callback = callback
    
    def _handle_lock_lost(self):
        """Handle situation where lock was lost (e.g., admin force unlock)"""
        # Stop heartbeat immediately
        self._stop_heartbeat.set()
        
        # Update internal state
        self.has_write_lock = False
        old_session_id = self.current_session_id
        self.current_session_id = None
        self.current_user_id = None
        self.current_username = None
        
        # Remove lock file if it exists
        try:
            if os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
        except Exception as e:
            print(f"Warning: Could not remove lock file: {e}")
        
        # Notify via callback
        if self._lock_lost_callback:
            try:
                self._lock_lost_callback(old_session_id)
            except Exception as e:
                print(f"Error in lock lost callback: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.release_write_lock()
