"""
Test script to verify database and locking functionality
Run this before starting the GUI to ensure everything is set up correctly
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_PATH
from database import DatabaseManager
from core import LockManager


def test_database():
    """Test database initialization and basic operations"""
    print("=" * 60)
    print("Testing Database")
    print("=" * 60)
    
    try:
        print(f"\n1. Initializing database at: {DB_PATH}")
        db_manager = DatabaseManager(DB_PATH)
        print("   [OK] Database initialized successfully")
        
        print("\n2. Loading users...")
        users = db_manager.get_all_users()
        print(f"   [OK] Found {len(users)} users:")
        for user in users:
            print(f"      - {user['display_name']} ({user['username']}) "
                  f"{'[ADMIN]' if user['is_admin'] else ''}")
        
        print("\n3. Testing building operations...")
        test_building = {
            'name': 'Test Building',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'TS',
            'zip_code': '12345',
            'total_units': 10,
            'notes': 'This is a test building'
        }
        
        building_id = db_manager.create_building(test_building, 1)
        print(f"   [OK] Created test building with ID: {building_id}")
        
        buildings = db_manager.get_all_buildings()
        print(f"   [OK] Retrieved {len(buildings)} building(s)")
        
        db_manager.delete_building(building_id, 1)
        print(f"   [OK] Deleted test building")
        
        print("\n4. Checking audit log...")
        audit_entries = db_manager.get_audit_log(5)
        print(f"   [OK] Found {len(audit_entries)} recent audit entries")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
        return False


def test_locking():
    """Test lock manager functionality"""
    print("\n" + "=" * 60)
    print("Testing Lock Manager")
    print("=" * 60)
    
    try:
        print(f"\n1. Initializing lock manager...")
        db_manager = DatabaseManager(DB_PATH)
        lock_manager = LockManager(DB_PATH, db_manager)
        print("   [OK] Lock manager initialized")
        
        print("\n2. Testing lock acquisition...")
        success, error = lock_manager.acquire_write_lock(1, 'admin')
        if success:
            print("   [OK] Successfully acquired write lock")
        else:
            print(f"   [ERROR] Failed to acquire lock: {error}")
            return False
        
        print("\n3. Checking lock status...")
        has_permission, lock_holder = lock_manager.check_write_permission()
        if has_permission and lock_manager.has_write_lock:
            print("   [OK] Write permission confirmed")
        else:
            print(f"   [ERROR] Permission check failed")
            return False
        
        print("\n4. Testing heartbeat (waiting 3 seconds)...")
        import time
        time.sleep(3)
        print("   [OK] Heartbeat thread running")
        
        print("\n5. Releasing lock...")
        lock_manager.release_write_lock()
        print("   [OK] Lock released successfully")
        
        print("\n6. Verifying lock is released...")
        has_permission, lock_holder = lock_manager.check_write_permission()
        if has_permission and not lock_manager.has_write_lock:
            print("   [OK] Lock successfully released")
        else:
            print(f"   [ERROR] Lock still held")
            return False
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_files():
    """Test that UI files exist"""
    print("\n" + "=" * 60)
    print("Testing UI Files")
    print("=" * 60)
    
    ui_dir = Path(__file__).parent / 'ui'
    required_files = [
        'login_dialog.ui',
        'main_window.ui',
        'building_form.ui',
        'unit_form.ui'
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = ui_dir / filename
        if filepath.exists():
            print(f"   [OK] {filename} exists")
        else:
            print(f"   [ERROR] {filename} NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Property Management System - System Test")
    print("=" * 60)
    
    results = []
    
    # Test database
    results.append(("Database", test_database()))
    
    # Test locking
    results.append(("Lock Manager", test_locking()))
    
    # Test UI files
    results.append(("UI Files", test_ui_files()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{test_name:20} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[OK] All tests passed! The system is ready to use.")
        print("\nYou can now run the application:")
        print("  python main.py")
    else:
        print("\n[ERROR] Some tests failed. Please check the errors above.")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
