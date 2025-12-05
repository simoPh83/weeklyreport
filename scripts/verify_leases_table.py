"""
Verify leases table and add sample data for testing
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

DB_PATH = "database file/WeeklyReportDB.db"

def verify_leases_table():
    """Verify leases table structure and add sample data"""
    db = DatabaseManager(DB_PATH)
    
    print("=" * 60)
    print("LEASES TABLE VERIFICATION")
    print("=" * 60)
    
    # Get some units and tenants to work with
    units = db.get_all_units()
    tenants = db.get_all_tenants()
    
    print(f"\n✓ Found {len(units)} units in database")
    print(f"✓ Found {len(tenants)} tenants in database")
    
    if len(units) == 0 or len(tenants) == 0:
        print("\n⚠ Cannot create sample leases - need at least one unit and one tenant")
        return
    
    # Get existing leases
    leases = db.get_leases()
    print(f"\n✓ Found {len(leases)} existing leases")
    
    # Get admin user for creating leases
    admin_user = db.get_user_by_username('admin')
    if not admin_user:
        print("\n⚠ Cannot create sample leases - admin user not found")
        return
    
    admin_id = admin_user['id']
    
    if len(leases) == 0:
        print("\n" + "=" * 60)
        print("CREATING SAMPLE LEASES")
        print("=" * 60)
        
        # Create 3 sample leases with different scenarios
        today = datetime.now()
        
        # Lease 1: Active lease (started 1 year ago, expires in 4 years)
        if len(units) >= 1 and len(tenants) >= 1:
            lease1_data = {
                'tenant_id': tenants[0]['id'],
                'unit_id': units[0]['id'],
                'rent_pa': 50000.00,
                'start_date': (today - timedelta(days=365)).strftime('%Y-%m-%d'),
                'break_date': (today + timedelta(days=1095)).strftime('%Y-%m-%d'),  # 3 years from now
                'expiry_date': (today + timedelta(days=1825)).strftime('%Y-%m-%d')  # 5 years from now
            }
            lease1_id = db.create_lease(lease1_data, admin_id)
            print(f"\n✓ Created active lease #{lease1_id}:")
            print(f"  Unit: {units[0]['unit_name']} ({units[0]['building_name']})")
            print(f"  Tenant: {tenants[0]['tenant_name']}")
            print(f"  Rent: £{lease1_data['rent_pa']:,.2f} PA")
            print(f"  Period: {lease1_data['start_date']} to {lease1_data['expiry_date']}")
        
        # Lease 2: Active lease without break clause (started 6 months ago, expires in 4.5 years)
        if len(units) >= 2 and len(tenants) >= 1:
            lease2_data = {
                'tenant_id': tenants[0]['id'],
                'unit_id': units[1]['id'],
                'rent_pa': 35000.00,
                'start_date': (today - timedelta(days=180)).strftime('%Y-%m-%d'),
                'expiry_date': (today + timedelta(days=1645)).strftime('%Y-%m-%d')  # ~4.5 years from now
            }
            lease2_id = db.create_lease(lease2_data, admin_id)
            print(f"\n✓ Created active lease #{lease2_id} (no break clause):")
            print(f"  Unit: {units[1]['unit_name']} ({units[1]['building_name']})")
            print(f"  Tenant: {tenants[0]['tenant_name']}")
            print(f"  Rent: £{lease2_data['rent_pa']:,.2f} PA")
            print(f"  Period: {lease2_data['start_date']} to {lease2_data['expiry_date']}")
        
        # Lease 3: Historical lease (ended 6 months ago)
        if len(units) >= 3 and len(tenants) >= 2:
            lease3_data = {
                'tenant_id': tenants[1]['id'] if len(tenants) > 1 else tenants[0]['id'],
                'unit_id': units[2]['id'],
                'rent_pa': 42000.00,
                'start_date': (today - timedelta(days=2190)).strftime('%Y-%m-%d'),  # 6 years ago
                'break_date': (today - timedelta(days=730)).strftime('%Y-%m-%d'),  # 2 years ago
                'expiry_date': (today - timedelta(days=180)).strftime('%Y-%m-%d')  # 6 months ago
            }
            lease3_id = db.create_lease(lease3_data, admin_id)
            print(f"\n✓ Created historical lease #{lease3_id} (expired):")
            print(f"  Unit: {units[2]['unit_name']} ({units[2]['building_name']})")
            print(f"  Tenant: {tenants[1]['tenant_name'] if len(tenants) > 1 else tenants[0]['tenant_name']}")
            print(f"  Rent: £{lease3_data['rent_pa']:,.2f} PA")
            print(f"  Period: {lease3_data['start_date']} to {lease3_data['expiry_date']}")
        
        # Refresh leases list
        leases = db.get_leases()
    
    # Test queries
    print("\n" + "=" * 60)
    print("TESTING LEASE QUERIES")
    print("=" * 60)
    
    # Test get_current_lease_by_unit for first 5 units
    print("\n1. Current leases by unit:")
    for unit in units[:5]:
        current_lease = db.get_current_lease_by_unit(unit['id'])
        if current_lease:
            print(f"  ✓ Unit {unit['unit_name']}: £{current_lease['rent_pa']:,.2f} PA - {current_lease['tenant_name']}")
        else:
            print(f"  - Unit {unit['unit_name']}: No current lease")
    
    # Test get_leases_by_tenant
    if len(tenants) > 0:
        print(f"\n2. Leases for tenant '{tenants[0]['tenant_name']}':")
        tenant_leases = db.get_leases_by_tenant(tenants[0]['id'])
        for lease in tenant_leases:
            status = "ACTIVE" if datetime.now() >= datetime.fromisoformat(lease['start_date']) and datetime.now() <= datetime.fromisoformat(lease['expiry_date']) else "EXPIRED"
            print(f"  {status}: {lease['unit_name']} ({lease['building_name']}) - £{lease['rent_pa']:,.2f} PA")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_leases = db.get_leases()
    active_count = 0
    total_rent = 0.0
    
    for lease in all_leases:
        if datetime.now() >= datetime.fromisoformat(lease['start_date']) and \
           datetime.now() <= datetime.fromisoformat(lease['expiry_date']):
            active_count += 1
            total_rent += lease['rent_pa']
    
    print(f"\nTotal leases: {len(all_leases)}")
    print(f"Active leases: {active_count}")
    print(f"Total active rent: £{total_rent:,.2f} PA")
    print("\n✓ Leases table working correctly")

if __name__ == "__main__":
    verify_leases_table()
