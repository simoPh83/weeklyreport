"""
Find unit IDs for unmatched ERV records
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# The four unmatched units
unmatched = [
    ('51-53 Margaret Street', 'Basement & Ground Floor (East)'),
    ('50-60 Eastcastle Street', 'First Floor'),
    ('50-60 Eastcastle Street', 'Second Floor'),
    ('50-60 Eastcastle Street', 'Third Floor (303 & 320)')
]

print("="*80)
print("SEARCHING FOR UNMATCHED UNITS")
print("="*80)

for property_name, unit_demise in unmatched:
    print(f"\n{'='*80}")
    print(f"Property: {property_name}")
    print(f"Looking for unit: {unit_demise}")
    print("-"*80)
    
    # Find all units in this property
    cursor.execute("""
        SELECT u.id, u.unit_name, b.property_address
        FROM units u
        JOIN buildings b ON u.building_id = b.id
        WHERE b.property_address = ?
        ORDER BY u.unit_name
    """, (property_name,))
    
    results = cursor.fetchall()
    
    if results:
        print(f"Available units in '{property_name}':")
        for row in results:
            print(f"  ID: {row['id']:3d} | Unit: {row['unit_name']}")
    else:
        print(f"  ⚠️  No units found in database for this property!")

conn.close()

print("\n" + "="*80)
print("DONE")
print("="*80)
