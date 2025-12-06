"""
Script to verify bank_schedule_imports tracking system

Tests:
1. Check bank_schedule_imports table exists with correct structure
2. Verify initial import record was created
3. Check leases have import_id linked
4. Check unit_history has import_id linked
5. Test get_current_import() method
6. Test get_current_import_display() method
7. Test has_modifications_after() method
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager

DB_PATH = project_root / "database file" / "WeeklyReportDB.db"


def main():
    print("\n" + "="*80)
    print("VERIFICATION: Bank Schedule Imports Tracking System")
    print("="*80)
    
    db_manager = DatabaseManager(str(DB_PATH))
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Test 1: Check bank_schedule_imports table structure
    print("\n1. Checking bank_schedule_imports table structure...")
    cursor.execute("PRAGMA table_info(bank_schedule_imports)")
    columns = cursor.fetchall()
    column_names = [col['name'] for col in columns]
    print(f"   Columns: {', '.join(column_names)}")
    
    expected_columns = ['id', 'schedule_filename', 'schedule_date', 'import_date', 
                       'is_current', 'imported_by', 'notes', 'units_imported', 
                       'leases_imported', 'sq_footage_records', 'created_at']
    missing = set(expected_columns) - set(column_names)
    if missing:
        print(f"   ⚠️  Missing columns: {missing}")
    else:
        print("   ✓ All expected columns present")
    
    # Test 2: Check initial import record
    print("\n2. Checking initial import record...")
    cursor.execute("""
        SELECT id, schedule_filename, schedule_date, is_current, 
               leases_imported, sq_footage_records
        FROM bank_schedule_imports
    """)
    imports = cursor.fetchall()
    print(f"   Total import records: {len(imports)}")
    for imp in imports:
        current_marker = " [CURRENT]" if imp['is_current'] else ""
        print(f"   - ID {imp['id']}: {imp['schedule_filename']} "
              f"({imp['schedule_date']}){current_marker}")
        print(f"     Leases: {imp['leases_imported']}, "
              f"Unit History: {imp['sq_footage_records']}")
    
    # Test 3: Check leases have import_id
    print("\n3. Checking leases import_id linkage...")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(import_id) as with_import_id,
            COUNT(*) - COUNT(import_id) as without_import_id
        FROM leases
    """)
    lease_stats = cursor.fetchone()
    print(f"   Total leases: {lease_stats['total']}")
    print(f"   With import_id: {lease_stats['with_import_id']}")
    print(f"   Without import_id: {lease_stats['without_import_id']}")
    if lease_stats['without_import_id'] == 0:
        print("   ✓ All leases linked to import")
    else:
        print(f"   ⚠️  {lease_stats['without_import_id']} leases not linked")
    
    # Test 4: Check unit_history has import_id
    print("\n4. Checking unit_history import_id linkage...")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(import_id) as with_import_id,
            COUNT(*) - COUNT(import_id) as without_import_id
        FROM unit_history
    """)
    history_stats = cursor.fetchone()
    print(f"   Total unit_history records: {history_stats['total']}")
    print(f"   With import_id: {history_stats['with_import_id']}")
    print(f"   Without import_id: {history_stats['without_import_id']}")
    if history_stats['without_import_id'] == 0:
        print("   ✓ All unit_history records linked to import")
    else:
        print(f"   ⚠️  {history_stats['without_import_id']} records not linked")
    
    # Test 5: Test get_current_import() method
    print("\n5. Testing get_current_import() method...")
    current_import = db_manager.get_current_import()
    if current_import:
        print(f"   ✓ Current import found:")
        print(f"     ID: {current_import['id']}")
        print(f"     Filename: {current_import['schedule_filename']}")
        print(f"     Date: {current_import['schedule_date']}")
        print(f"     Import Date: {current_import['import_date']}")
        print(f"     Leases: {current_import['leases_imported']}")
    else:
        print("   ⚠️  No current import found")
    
    # Test 6: Test get_current_import_display() method
    print("\n6. Testing get_current_import_display() method...")
    display_text = db_manager.get_current_import_display()
    print(f"   Display text: '{display_text}'")
    if "[PLUS]" in display_text:
        print("   ℹ [PLUS] indicator present - modifications detected")
    else:
        print("   ℹ No [PLUS] indicator - no modifications after import")
    
    # Test 7: Test has_modifications_after() method
    print("\n7. Testing has_modifications_after() method...")
    if current_import:
        has_mods = db_manager.has_modifications_after(
            current_import['id'], 
            current_import['import_date']
        )
        print(f"   Has modifications: {has_mods}")
        
        # Show sample of records created after import
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM leases
            WHERE created_at > ? OR updated_at > ?
        """, (current_import['import_date'], current_import['import_date']))
        leases_after = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM unit_history
            WHERE created_at > ?
        """, (current_import['import_date'],))
        history_after = cursor.fetchone()['count']
        
        print(f"   Leases created/updated after import: {leases_after}")
        print(f"   Unit history created after import: {history_after}")
    
    # Test 8: Check indexes were created
    print("\n8. Checking indexes...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type = 'index' 
        AND name LIKE '%import%'
        ORDER BY name
    """)
    indexes = cursor.fetchall()
    print(f"   Import-related indexes found: {len(indexes)}")
    for idx in indexes:
        print(f"   - {idx['name']}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
