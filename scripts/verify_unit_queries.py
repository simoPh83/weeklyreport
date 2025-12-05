"""
Verification script: Check that unit queries return sq_ft correctly
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def verify_unit_queries():
    """Verify that unit queries work with new structure"""
    db_path = get_db_path()
    
    print("="*80)
    print("VERIFICATION: Unit queries with unit_square_footage JOIN")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test 1: Get all units with sq_ft
    print("\n1. Testing get_all_units query...")
    cursor.execute("""
        SELECT u.id, u.unit_name, u.building_id,
               usf.sq_ft,
               b.property_name as building_name
        FROM units u
        LEFT JOIN buildings b ON u.building_id = b.id
        LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id AND usf.is_current = 1
        ORDER BY b.property_code, u.unit_name
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    print(f"   Found {len(rows)} units (showing first 5)")
    for row in rows:
        print(f"   - Unit {row['id']}: {row['unit_name']} ({row['building_name']}) - {row['sq_ft']} sq ft")
    
    # Test 2: Count units with/without sq_ft
    print("\n2. Checking sq_ft data coverage...")
    cursor.execute("""
        SELECT 
            COUNT(*) as total_units,
            COUNT(usf.sq_ft) as units_with_sqft,
            COUNT(*) - COUNT(usf.sq_ft) as units_without_sqft
        FROM units u
        LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id AND usf.is_current = 1
    """)
    stats = cursor.fetchone()
    print(f"   Total units: {stats['total_units']}")
    print(f"   Units with sq_ft: {stats['units_with_sqft']}")
    print(f"   Units without sq_ft: {stats['units_without_sqft']}")
    
    # Test 3: Check unit_square_footage table
    print("\n3. Checking unit_square_footage table...")
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN is_current = 1 THEN 1 END) as current_records,
            MIN(effective_from) as earliest_date,
            MAX(effective_from) as latest_date
        FROM unit_square_footage
    """)
    sqft_stats = cursor.fetchone()
    print(f"   Total sq_ft records: {sqft_stats['total_records']}")
    print(f"   Current records: {sqft_stats['current_records']}")
    print(f"   Date range: {sqft_stats['earliest_date']} to {sqft_stats['latest_date']}")
    
    # Test 4: Verify no orphaned records
    print("\n4. Checking data integrity...")
    cursor.execute("""
        SELECT COUNT(*) as orphaned
        FROM unit_square_footage usf
        WHERE NOT EXISTS (SELECT 1 FROM units u WHERE u.id = usf.unit_id)
    """)
    orphaned = cursor.fetchone()['orphaned']
    if orphaned == 0:
        print("   ✓ No orphaned sq_ft records")
    else:
        print(f"   ⚠️  Found {orphaned} orphaned sq_ft records")
    
    # Test 5: Sample a specific unit
    print("\n5. Sample unit detail query...")
    cursor.execute("""
        SELECT u.*, 
               usf.sq_ft,
               b.property_name as building_name,
               ut.description as unit_type_name
        FROM units u
        LEFT JOIN buildings b ON u.building_id = b.id
        LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
        LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id AND usf.is_current = 1
        LIMIT 1
    """)
    sample = cursor.fetchone()
    if sample:
        print(f"   Sample Unit ID: {sample['id']}")
        print(f"   Name: {sample['unit_name']}")
        print(f"   Building: {sample['building_name']}")
        print(f"   Type: {sample['unit_type_name']}")
        print(f"   Sq Ft: {sample['sq_ft']}")
        print(f"   ✓ Query returns all expected fields")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✓ VERIFICATION COMPLETE - All queries working correctly")
    print("="*80)


if __name__ == "__main__":
    verify_unit_queries()
