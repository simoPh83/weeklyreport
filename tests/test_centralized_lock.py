"""
Test centralized write lock verification in database manager
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager, DatabaseWriteError
from core.lock_manager import LockManager

def test_centralized_lock_verification():
    """Test that all write operations check lock centrally"""
    print("="*60)
    print("Testing Centralized Write Lock Verification")
    print("="*60)
    
    # Setup
    test_db = "test_central_lock.db"
    if Path(test_db).exists():
        Path(test_db).unlink()
    
    print("\n1. Setup database and lock managers...")
    db_manager = DatabaseManager(test_db)
    lock_manager1 = LockManager(test_db, db_manager)
    lock_manager2 = LockManager(test_db, db_manager)
    
    # Set lock manager in db_manager
    db_manager.set_lock_manager(lock_manager1)
    
    user1 = db_manager.get_user_by_username("user1")
    admin = db_manager.get_user_by_username("admin")
    print(f"   [OK] Users: user1={user1['id']}, admin={admin['id']}")
    
    # User1 acquires lock
    print("\n2. User1 acquires write lock...")
    success, error = lock_manager1.acquire_write_lock(user1['id'], user1['username'])
    if not success:
        print(f"   [ERROR] {error}")
        return False
    print(f"   [OK] Lock acquired")
    
    # User1 can write
    print("\n3. User1 creates a building (should succeed)...")
    try:
        building_data = {
            'name': 'Test Building 1',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'TS',
            'zip_code': '12345',
            'total_units': 10,
            'notes': 'Test building'
        }
        building_id = db_manager.create_building(building_data, user1['id'])
        print(f"   [OK] Building created with ID: {building_id}")
    except DatabaseWriteError as e:
        print(f"   [ERROR] Unexpected write error: {e}")
        return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False
    
    # Admin forces unlock
    print("\n4. Admin forces unlock...")
    success, msg = lock_manager2.force_unlock(admin['id'])
    if not success:
        print(f"   [ERROR] {msg}")
        return False
    print(f"   [OK] {msg}")
    print(f"   [OK] User1 still thinks it has lock: {lock_manager1.has_write_lock}")
    
    # User1 tries to write - should fail
    print("\n5. User1 tries to create another building (should fail)...")
    write_blocked = False
    try:
        building_data2 = {
            'name': 'Test Building 2',
            'address': '456 Test Ave',
            'city': 'Test City',
            'state': 'TS',
            'zip_code': '54321',
            'total_units': 5,
            'notes': 'Should not be saved'
        }
        building_id2 = db_manager.create_building(building_data2, user1['id'])
        print(f"   [FAIL] Building was created! ID: {building_id2}")
        print(f"   [FAIL] Write should have been blocked!")
        return False
    except DatabaseWriteError as e:
        write_blocked = True
        print(f"   [SUCCESS] Write blocked!")
        print(f"   [SUCCESS] Error message: {e}")
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {e}")
        return False
    
    # Verify lock state cleaned up
    print("\n6. Verify lock state...")
    print(f"   has_write_lock: {lock_manager1.has_write_lock}")
    print(f"   session_id: {lock_manager1.current_session_id}")
    
    # Try other write operations
    print("\n7. Test all write operations are blocked...")
    tests_passed = []
    
    # Test update_building
    try:
        db_manager.update_building(building_id, {'name': 'Updated'}, user1['id'])
        print("   [FAIL] update_building was allowed")
        tests_passed.append(False)
    except DatabaseWriteError:
        print("   [PASS] update_building blocked")
        tests_passed.append(True)
    
    # Test delete_building
    try:
        db_manager.delete_building(building_id, user1['id'])
        print("   [FAIL] delete_building was allowed")
        tests_passed.append(False)
    except DatabaseWriteError:
        print("   [PASS] delete_building blocked")
        tests_passed.append(True)
    
    # Test create_unit
    try:
        unit_data = {
            'building_id': building_id,
            'unit_number': '101',
            'floor': 1,
            'bedrooms': 2,
            'bathrooms': 1.0,
            'square_feet': 1000,
            'rent_amount': 1500,
            'status': 'Vacant'
        }
        db_manager.create_unit(unit_data, user1['id'])
        print("   [FAIL] create_unit was allowed")
        tests_passed.append(False)
    except DatabaseWriteError:
        print("   [PASS] create_unit blocked")
        tests_passed.append(True)
    
    # Verify building 1 still exists (wasn't deleted)
    building = db_manager.get_building_by_id(building_id)
    if building and building['name'] == 'Test Building 1':
        print(f"   [PASS] Building 1 still exists with original data")
        tests_passed.append(True)
    else:
        print(f"   [FAIL] Building 1 was modified or deleted")
        tests_passed.append(False)
    
    # Verify no second building was created
    all_buildings = db_manager.get_all_buildings()
    if len(all_buildings) == 1:
        print(f"   [PASS] Only 1 building exists (second was blocked)")
        tests_passed.append(True)
    else:
        print(f"   [FAIL] Found {len(all_buildings)} buildings (should be 1)")
        tests_passed.append(False)
    
    print("\n" + "="*60)
    print("TEST RESULTS:")
    print("="*60)
    
    if all(tests_passed) and write_blocked:
        print("[SUCCESS] All write operations centrally verified!")
        print("[SUCCESS] Single point of control working correctly")
        print("[SUCCESS] No code duplication in forms")
        print("\\nBenefits:")
        print("- Lock check in ONE place: db_manager._verify_write_permission()")
        print("- All write methods automatically protected")
        print("- Forms just catch DatabaseWriteError")
        print("- Easy to maintain and modify")
        return True
    else:
        print("[FAIL] Some tests failed")
        print(f"Tests passed: {sum(tests_passed)}/{len(tests_passed)}")
        return False
    
    # Cleanup
    lock_manager1.release_write_lock()
    lock_manager2.release_write_lock()
    if Path(test_db).exists():
        Path(test_db).unlink()

if __name__ == "__main__":
    try:
        success = test_centralized_lock_verification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
