"""
Database Manager for Property Management System
Handles all database operations, schema initialization, and queries
"""
import sqlite3
import bcrypt
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import threading


class DatabaseWriteError(Exception):
    """Raised when write operation fails due to lack of write lock"""
    pass


class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str):
        if not hasattr(self, 'initialized'):
            self.db_path = db_path
            self.initialized = True
            self.lock_manager = None  # Will be set by main.py
            self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    password_hash TEXT,
                    email TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Buildings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS buildings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    total_units INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id)
                )
            """)
            
            # Units table (Commercial properties: offices and retail)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    building_id INTEGER NOT NULL,
                    unit_number TEXT NOT NULL,
                    floor INTEGER,
                    unit_type TEXT DEFAULT 'Office',  -- 'Office' or 'Retail'
                    square_feet REAL,
                    rent_amount REAL,
                    status TEXT DEFAULT 'Vacant',
                    tenant_name TEXT,
                    lease_start DATE,
                    lease_end DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id),
                    UNIQUE(building_id, unit_number)
                )
            """)
            
            # Sessions table (database-based locking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_write_lock INTEGER DEFAULT 0,
                    machine_name TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create default admin user if no users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO users (username, display_name, is_admin)
                    VALUES ('admin', 'Administrator', 1)
                """)
                cursor.execute("""
                    INSERT INTO users (username, display_name, is_admin)
                    VALUES ('user1', 'User One', 0)
                """)
                cursor.execute("""
                    INSERT INTO users (username, display_name, is_admin)
                    VALUES ('user2', 'User Two', 0)
                """)
            
            conn.commit()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def set_lock_manager(self, lock_manager):
        """Set the lock manager instance for write verification"""
        self.lock_manager = lock_manager
    
    def _verify_write_permission(self) -> None:
        """
        Verify write lock before any write operation.
        Raises DatabaseWriteError if no valid write lock.
        This is the centralized lock verification point.
        """
        if self.lock_manager is None:
            # During initialization, lock_manager may not be set yet
            return
        
        if not self.lock_manager.verify_write_lock():
            raise DatabaseWriteError(
                "Write operation denied: You no longer have write access to the database. "
                "Your write lock has been removed (possibly by an administrator)."
            )
    
    # User management
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin
                FROM users
                WHERE is_active = 1
                ORDER BY display_name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin
                FROM users
                WHERE id = ? AND is_active = 1
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin
                FROM users
                WHERE username = ? AND is_active = 1
            """, (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username and password
        Returns user dict if authentication successful, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin, password_hash
                FROM users
                WHERE username = ? AND is_active = 1
            """, (username,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            user = dict(row)
            password_hash = user.pop('password_hash', None)
            
            # If no password hash, allow login (backward compatibility)
            if not password_hash:
                return user
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return user
            
            return None
    
    def set_user_password(self, user_id: int, password: str) -> bool:
        """
        Set or update user password
        """
        # Hash password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET password_hash = ?
                    WHERE id = ?
                """, (password_hash.decode('utf-8'), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error setting password: {e}")
            return False
    
    def create_user(self, username: str, display_name: str, password: str, 
                    is_admin: bool = False, email: Optional[str] = None) -> int:
        """
        Create new user with password
        Returns user ID
        """
        # Hash password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, display_name, password_hash, email, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, (username, display_name, password_hash.decode('utf-8'), email, 1 if is_admin else 0))
            conn.commit()
            return cursor.lastrowid
    
    # Buildings CRUD
    def get_all_buildings(self) -> List[Dict[str, Any]]:
        """Get all buildings with occupancy percentage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    b.*,
                    u.display_name as created_by_name,
                    -- Calculate occupancy percentage
                    CASE 
                        WHEN COUNT(unit.id) = 0 THEN 0
                        ELSE ROUND(
                            (SUM(CASE WHEN unit.status = 'Let' THEN 1 ELSE 0 END) * 100.0) 
                            / COUNT(unit.id), 
                            1
                        )
                    END as occupancy
                FROM buildings b
                LEFT JOIN users u ON b.created_by = u.id
                LEFT JOIN units unit ON unit.building_id = b.id
                GROUP BY b.id, b.name, b.address, b.city, b.state, b.zip_code, 
                         b.total_units, b.notes, 
                         b.created_by, b.created_at, b.updated_at, b.updated_by, u.display_name
                ORDER BY b.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_building_by_id(self, building_id: int) -> Optional[Dict[str, Any]]:
        """Get building by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, u.display_name as created_by_name
                FROM buildings b
                LEFT JOIN users u ON b.created_by = u.id
                WHERE b.id = ?
            """, (building_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_building(self, data: Dict[str, Any], user_id: int) -> int:
        """Create a new building"""
        self._verify_write_permission()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO buildings (name, address, city, state, zip_code, total_units, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name'),
                data.get('address'),
                data.get('city'),
                data.get('state'),
                data.get('zip_code'),
                data.get('total_units', 0),
                data.get('notes'),
                user_id
            ))
            building_id = cursor.lastrowid
            
            # Log audit
            self._log_audit(conn, user_id, 'CREATE', 'buildings', building_id, None, str(data))
            
            conn.commit()
            return building_id
    
    def update_building(self, building_id: int, data: Dict[str, Any], user_id: int):
        """Update an existing building"""
        self._verify_write_permission()
        
        old_data = self.get_building_by_id(building_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE buildings
                SET name = ?, address = ?, city = ?, state = ?, zip_code = ?,
                    total_units = ?, notes = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('address'),
                data.get('city'),
                data.get('state'),
                data.get('zip_code'),
                data.get('total_units', 0),
                data.get('notes'),
                user_id,
                building_id
            ))
            
            # Log audit
            self._log_audit(conn, user_id, 'UPDATE', 'buildings', building_id, str(old_data), str(data))
            
            conn.commit()
    
    def delete_building(self, building_id: int, user_id: int):
        """Delete a building"""
        self._verify_write_permission()
        
        old_data = self.get_building_by_id(building_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM buildings WHERE id = ?", (building_id,))
            
            # Log audit
            self._log_audit(conn, user_id, 'DELETE', 'buildings', building_id, str(old_data), None)
            
            conn.commit()
    
    # Units CRUD
    def get_units_by_building(self, building_id: int) -> List[Dict[str, Any]]:
        """Get all units for a building"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, b.name as building_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                WHERE u.building_id = ?
                ORDER BY u.unit_number
            """, (building_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_units(self) -> List[Dict[str, Any]]:
        """Get all units"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, b.name as building_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                ORDER BY b.name, u.unit_number
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unit_by_id(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """Get unit by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, b.name as building_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                WHERE u.id = ?
            """, (unit_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_unit(self, data: Dict[str, Any], user_id: int) -> int:
        """Create a new unit"""
        self._verify_write_permission()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO units (
                    building_id, unit_number, floor, unit_type,
                    square_feet, rent_amount, status, tenant_name,
                    lease_start, lease_end, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('building_id'),
                data.get('unit_number'),
                data.get('floor'),
                data.get('unit_type', 'Office'),
                data.get('square_feet'),
                data.get('rent_amount'),
                data.get('status', 'Vacant'),
                data.get('tenant_name'),
                data.get('lease_start'),
                data.get('lease_end'),
                data.get('notes'),
                user_id
            ))
            unit_id = cursor.lastrowid
            
            # Log audit
            self._log_audit(conn, user_id, 'CREATE', 'units', unit_id, None, str(data))
            
            conn.commit()
            return unit_id
    
    def update_unit(self, unit_id: int, data: Dict[str, Any], user_id: int):
        """Update an existing unit"""
        self._verify_write_permission()
        
        old_data = self.get_unit_by_id(unit_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE units
                SET building_id = ?, unit_number = ?, floor = ?, unit_type = ?,
                    square_feet = ?, rent_amount = ?, status = ?, tenant_name = ?,
                    lease_start = ?, lease_end = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (
                data.get('building_id'),
                data.get('unit_number'),
                data.get('floor'),
                data.get('unit_type', 'Office'),
                data.get('square_feet'),
                data.get('rent_amount'),
                data.get('status', 'Vacant'),
                data.get('tenant_name'),
                data.get('lease_start'),
                data.get('lease_end'),
                data.get('notes'),
                user_id,
                unit_id
            ))
            
            # Log audit
            self._log_audit(conn, user_id, 'UPDATE', 'units', unit_id, str(old_data), str(data))
            
            conn.commit()
    
    def delete_unit(self, unit_id: int, user_id: int):
        """Delete a unit"""
        self._verify_write_permission()
        
        old_data = self.get_unit_by_id(unit_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM units WHERE id = ?", (unit_id,))
            
            # Log audit
            self._log_audit(conn, user_id, 'DELETE', 'units', unit_id, str(old_data), None)
            
            conn.commit()
    
    # Audit logging
    def _log_audit(self, conn: sqlite3.Connection, user_id: int, action: str,
                   table_name: str, record_id: Optional[int],
                   old_values: Optional[str], new_values: Optional[str]):
        """Log an audit entry"""
        user = self.get_user_by_id(user_id)
        username = user['username'] if user else 'unknown'
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (user_id, username, action, table_name, record_id, old_values, new_values)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, action, table_name, record_id, old_values, new_values))
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
