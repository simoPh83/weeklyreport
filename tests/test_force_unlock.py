"""
Test force unlock scenario to verify lock lost detection
"""
import sys
import time
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from core.lock_manager import LockManager

def test_force_unlock_detection():
    """Test that a locked user detects when admin force unlocks"""
    print("="*60)
    print("Testing Force Unlock Detection")
    print("="*60)
    
    # Setup test database
    test_db = "test_force_unlock.db"
    if Path(test_db).exists():
        Path(test_db).unlink()
    
    # Initialize database
    print("\n1. Initializing database...")
    db_manager = DatabaseManager(test_db)
    print("   [OK] Database initialized")
    
    # Create two lock managers (simulating two users)
    print("\n2. Creating two lock manager instances...")
    lock_manager1 = LockManager(test_db, db_manager)
    lock_manager2 = LockManager(test_db, db_manager)
    
    # Get admin user (for force unlock)
    admin = db_manager.get_user_by_username("admin")
    user1 = db_manager.get_user_by_username("user1")
    print(f"   [OK] Admin ID: {admin['id']}, User1 ID: {user1['id']}")
    
    # User1 acquires lock
    print("\n3. User1 acquiring write lock...")
    success, error = lock_manager1.acquire_write_lock(user1['id'], user1['username'])
    if not success:
        print(f"   [ERROR] Failed to acquire lock: {error}")
        return False
    print(f"   [OK] User1 has lock: {lock_manager1.has_write_lock}")
    
    # Verify lock file exists
    lock_file = test_db + '.lock'
    if not Path(lock_file).exists():
        print(f"   [ERROR] Lock file not created")
        return False
    print(f"   [OK] Lock file created: {lock_file}")
    
    # Wait for first heartbeat
    print("\n4. Waiting for first heartbeat (2 seconds)...")
    time.sleep(2)
    
    # Check database session
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE is_write_lock = 1")
        sessions = cursor.fetchall()
        print(f"   [OK] Active sessions: {len(sessions)}")
        if sessions:
            print(f"   [OK] Session ID: {sessions[0]['id']}, User: {sessions[0]['username']}")
    
    # Setup callback to detect lock loss
    lock_lost_detected = {'value': False, 'session_id': None}
    def on_lock_lost(session_id):
        print(f"\n   >>> CALLBACK TRIGGERED (from thread): Lock lost! Session ID: {session_id}")
        lock_lost_detected['value'] = True
        lock_lost_detected['session_id'] = session_id
    
    lock_manager1.set_lock_lost_callback(on_lock_lost)
    print("\n5. Lock lost callback registered")
    
    # Admin forces unlock
    print("\n6. Admin forcing unlock...")
    success, message = lock_manager2.force_unlock(admin['id'])
    if not success:
        print(f"   [ERROR] Force unlock failed: {message}")
        return False
    print(f"   [OK] Force unlock: {message}")
    
    # Check that lock file is removed
    if Path(lock_file).exists():
        print(f"   [ERROR] Lock file still exists after force unlock")
        return False
    print(f"   [OK] Lock file removed")
    
    # Check database sessions
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE is_write_lock = 1")
        sessions = cursor.fetchall()
        print(f"   [OK] Active sessions after force unlock: {len(sessions)}")
    
    # Wait for next heartbeat to detect lock loss
    print("\n7. Waiting for next heartbeat to detect lock loss (35 seconds max)...")
    print("   (Heartbeat runs every 30 seconds)")
    
    for i in range(35):
        time.sleep(1)
        if lock_lost_detected['value']:
            print(f"\n   [SUCCESS] Lock loss detected after {i+1} seconds!")
            break
        if (i + 1) % 5 == 0:
            print(f"   ... waiting {i+1}s (callback: {lock_lost_detected['value']})")
    
    # Verify results
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    if lock_lost_detected['value']:
        print("[SUCCESS] Lock lost callback was triggered")
        print(f"[SUCCESS] User1 has_write_lock: {lock_manager1.has_write_lock} (should be False)")
        print(f"[SUCCESS] User1 session_id: {lock_manager1.current_session_id} (should be None)")
        
        if not lock_manager1.has_write_lock and lock_manager1.current_session_id is None:
            print("\n[PASS] All checks passed! Force unlock detection works correctly.")
            return True
        else:
            print("\n[FAIL] Lock state not properly cleaned up")
            return False
    else:
        print("[FAIL] Lock lost callback was NOT triggered")
        print(f"[FAIL] User1 still thinks it has lock: {lock_manager1.has_write_lock}")
        return False
    
    # Cleanup
    lock_manager1.release_write_lock()
    lock_manager2.release_write_lock()
    Path(test_db).unlink()

if __name__ == "__main__":
    try:
        success = test_force_unlock_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
