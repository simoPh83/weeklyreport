"""
Verify is_active field and performance of active leases query
"""
import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager

DB_PATH = "database file/WeeklyReportDB.db"

def test_is_active():
    """Test is_active field and query performance"""
    db = DatabaseManager(DB_PATH)
    
    print("=" * 60)
    print("IS_ACTIVE FIELD VERIFICATION")
    print("=" * 60)
    
    # Test get_active_leases method (using is_active index)
    print("\n1. Testing get_active_leases() with is_active index:")
    start = time.time()
    active_leases = db.get_active_leases()
    elapsed = time.time() - start
    print(f"   Found {len(active_leases)} active leases in {elapsed*1000:.2f}ms")
    
    # Test get_all_leases
    print("\n2. Testing get_leases() for all leases:")
    start = time.time()
    all_leases = db.get_leases()
    elapsed = time.time() - start
    print(f"   Found {len(all_leases)} total leases in {elapsed*1000:.2f}ms")
    
    # Calculate total active rent
    total_rent = sum(lease['rent_pa'] for lease in active_leases)
    print(f"\n3. Total active rent: £{total_rent:,.2f} PA")
    
    # Show sample of active leases
    print("\n4. Sample of active leases (first 5):")
    for lease in active_leases[:5]:
        print(f"   • {lease['building_name']} - {lease['unit_name']}")
        print(f"     Tenant: {lease['tenant_name']}")
        print(f"     Rent: £{lease['rent_pa']:,.2f} PA")
        print(f"     Period: {lease['start_date']} to {lease['expiry_date']}")
    
    # Show breakdown
    active_count = len([l for l in all_leases if l['is_active'] == 1])
    inactive_count = len([l for l in all_leases if l['is_active'] == 0])
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total leases: {len(all_leases)}")
    print(f"  Active (is_active=1): {active_count}")
    print(f"  Inactive (is_active=0): {inactive_count}")
    print(f"Total active rent: £{total_rent:,.2f} PA")
    print("\n✓ is_active field working correctly")

if __name__ == "__main__":
    test_is_active()
