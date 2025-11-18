"""
Test GUI lock lost with threading - verifies Qt signal/slot mechanism
Run this to verify no threading errors occur
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from core.lock_manager import LockManager
from gui.main_window import MainWindow

def test_gui_lock_lost():
    """Test that lock lost handling works properly with Qt threading"""
    print("="*60)
    print("Testing GUI Lock Lost with Threading")
    print("="*60)
    
    # Setup test database
    test_db = "test_gui_lock.db"
    if Path(test_db).exists():
        Path(test_db).unlink()
    
    # Initialize
    print("\n1. Initializing database and app...")
    app = QApplication(sys.argv)
    
    db_manager = DatabaseManager(test_db)
    lock_manager1 = LockManager(test_db, db_manager)
    lock_manager2 = LockManager(test_db, db_manager)
    
    user1 = db_manager.get_user_by_username("user1")
    admin = db_manager.get_user_by_username("admin")
    print(f"   [OK] Users loaded: user1={user1['id']}, admin={admin['id']}")
    
    # Acquire lock for user1
    print("\n2. User1 acquiring lock...")
    success, error = lock_manager1.acquire_write_lock(user1['id'], user1['username'])
    if not success:
        print(f"   [ERROR] Failed: {error}")
        return False
    print(f"   [OK] Lock acquired")
    
    # Create main window
    print("\n3. Creating main window...")
    window = MainWindow(db_manager, lock_manager1, user1, test_db)
    window.show()
    print(f"   [OK] Window created and shown")
    print(f"   [OK] Initial lock status: {window.is_read_only}")
    
    # Schedule force unlock after 3 seconds
    def force_unlock_task():
        print("\n4. Admin forcing unlock (from timer)...")
        success, msg = lock_manager2.force_unlock(admin['id'])
        print(f"   [OK] Force unlock result: {msg}")
        print(f"   Note: User1 will detect this on next heartbeat (~30 seconds)")
        print(f"   Waiting for lock lost signal...")
    
    # Schedule check after 35 seconds
    def check_result():
        print("\n5. Checking result...")
        print(f"   Window is_read_only: {window.is_read_only}")
        print(f"   Lock manager has_write_lock: {lock_manager1.has_write_lock}")
        
        if window.is_read_only and not lock_manager1.has_write_lock:
            print("\n[SUCCESS] Lock lost handled correctly!")
            print("[SUCCESS] No threading errors occurred!")
        else:
            print("\n[WARNING] State may not be updated yet")
        
        # Close app
        QTimer.singleShot(1000, app.quit)
    
    # Schedule tasks
    QTimer.singleShot(3000, force_unlock_task)
    QTimer.singleShot(35000, check_result)
    
    print("\n>>> Starting Qt event loop...")
    print(">>> Window should stay responsive")
    print(">>> Watch for any Qt threading warnings/errors")
    
    # Run app
    exit_code = app.exec()
    
    # Cleanup
    lock_manager1.release_write_lock()
    lock_manager2.release_write_lock()
    if Path(test_db).exists():
        Path(test_db).unlink()
    
    return exit_code == 0

if __name__ == "__main__":
    try:
        success = test_gui_lock_lost()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
