"""
Import 2023 ERV values from Excel file
Matches Property + Unit Demise to identify correct unit
"""
import sqlite3
import pandas as pd
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def import_ervs_2023():
    """Import 2023 ERV data from Excel file"""
    db_path = get_db_path()
    excel_path = Path(__file__).parent.parent / "data" / "31 August 2025 Bank Schedule.xlsx"
    
    print(f"Reading Excel file: {excel_path}")
    
    # Read Excel file with correct header row
    df = pd.read_excel(excel_path, sheet_name='Units', header=1)
    
    print(f"Total rows in Excel: {len(df)}")
    print(f"\nColumns found: {df.columns.tolist()}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Get current user (admin for script import)
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    user_row = cursor.fetchone()
    user_id = user_row['id'] if user_row else 1
    
    # Statistics
    total_rows = 0
    matched = 0
    inserted = 0
    updated = 0
    skipped_no_value = 0
    skipped_no_match = 0
    errors = []
    
    print("\n" + "="*80)
    print("Processing ERV data...")
    print("="*80)
    
    for idx, row in df.iterrows():
        total_rows += 1
        property_name = row.get('Property')
        unit_demise = row.get('Unit Demise')
        erv_2023 = row.get('  2023 ERV (£)')  # Note the leading spaces
        
        # Skip if no property or unit
        if pd.isna(property_name) or pd.isna(unit_demise):
            continue
            
        # Skip if no ERV value
        if pd.isna(erv_2023) or erv_2023 == 0:
            skipped_no_value += 1
            continue
        
        # Clean property name (strip whitespace)
        property_name = str(property_name).strip()
        unit_demise = str(unit_demise).strip()
        
        try:
            erv_value = float(erv_2023)
        except (ValueError, TypeError):
            errors.append(f"Row {idx+2}: Invalid ERV value '{erv_2023}'")
            continue
        
        # Find matching unit in database
        # Match on buildings.property_address and units.unit_name
        cursor.execute("""
            SELECT u.id, u.unit_name, b.property_address as building_name
            FROM units u
            JOIN buildings b ON u.building_id = b.id
            WHERE b.property_address = ? AND u.unit_name = ?
        """, (property_name, unit_demise))
        
        unit_row = cursor.fetchone()
        
        if not unit_row:
            skipped_no_match += 1
            print(f"  ✗ No match: Property='{property_name}', Unit='{unit_demise}'")
            continue
        
        unit_id = unit_row['id']
        matched += 1
        
        # Check if ERV record already exists for this unit and year
        cursor.execute("""
            SELECT id FROM ervs
            WHERE unit_id = ? AND year = 2023
        """, (unit_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE ervs
                SET value = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = ?
                WHERE id = ?
            """, (erv_value, user_id, existing['id']))
            updated += 1
            print(f"  ↻ Updated: {property_name} - {unit_demise}: £{erv_value:,.0f}")
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO ervs (unit_id, value, year, created_by)
                VALUES (?, ?, 2023, ?)
            """, (unit_id, erv_value, user_id))
            inserted += 1
            print(f"  ✓ Inserted: {property_name} - {unit_demise}: £{erv_value:,.0f}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    # Print summary
    print("\n" + "="*80)
    print("IMPORT SUMMARY")
    print("="*80)
    print(f"Total rows processed: {total_rows}")
    print(f"Matched units: {matched}")
    print(f"  - Inserted: {inserted}")
    print(f"  - Updated: {updated}")
    print(f"Skipped (no ERV value): {skipped_no_value}")
    print(f"Skipped (no match): {skipped_no_match}")
    
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    print("\n✓ Import completed successfully")
    
    # Show some statistics
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM ervs WHERE year = 2023")
    total_2023 = cursor.fetchone()[0]
    print(f"\nTotal 2023 ERV records in database: {total_2023}")
    conn.close()


if __name__ == "__main__":
    import_ervs_2023()
