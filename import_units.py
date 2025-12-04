"""
Import Units and Unit Types from Excel Spreadsheet
Reads NEW_bankSchedule.xlsx "Units" sheet and imports data
"""
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import sys


def import_unit_types(df: pd.DataFrame, cursor: sqlite3.Cursor) -> dict:
    """
    Import unique unit types from DataFrame
    
    Args:
        df: DataFrame with Unit Type column
        cursor: Database cursor
        
    Returns:
        Dictionary mapping unit type description to id
    """
    print("=" * 80)
    print("STEP 1: Importing Unit Types")
    print("=" * 80)
    
    # Get unique unit types
    unique_types = df['Unit Type'].dropna().unique()
    print(f"Found {len(unique_types)} unique unit types")
    print()
    
    type_map = {}
    imported_count = 0
    
    for unit_type in sorted(unique_types):
        unit_type_str = str(unit_type).strip()
        if not unit_type_str:
            continue
        
        try:
            # Check if already exists
            cursor.execute("SELECT id FROM unit_types WHERE description = ?", (unit_type_str,))
            existing = cursor.fetchone()
            
            if existing:
                type_map[unit_type_str] = existing[0]
                print(f"  Already exists: {unit_type_str} (ID: {existing[0]})")
            else:
                cursor.execute("INSERT INTO unit_types (description) VALUES (?)", (unit_type_str,))
                type_id = cursor.lastrowid
                type_map[unit_type_str] = type_id
                print(f"✓ Imported: {unit_type_str} (ID: {type_id})")
                imported_count += 1
        
        except Exception as e:
            print(f"✗ Error importing unit type '{unit_type_str}': {e}")
    
    print()
    print(f"Unit types imported: {imported_count}")
    print()
    
    return type_map


def get_building_id_map(cursor: sqlite3.Cursor) -> dict:
    """
    Get mapping of property_code to building_id
    
    Args:
        cursor: Database cursor
        
    Returns:
        Dictionary mapping property_code to building_id
    """
    cursor.execute("SELECT id, property_code FROM buildings")
    return {row[1]: row[0] for row in cursor.fetchall()}


def import_units(df: pd.DataFrame, cursor: sqlite3.Cursor, type_map: dict, building_map: dict, user_id: int = 1):
    """
    Import units from DataFrame
    
    Args:
        df: DataFrame with unit data
        cursor: Database cursor
        type_map: Mapping of unit type description to id
        building_map: Mapping of property_code to building_id
        user_id: User ID for created_by field
    """
    print("=" * 80)
    print("STEP 2: Importing Units")
    print("=" * 80)
    print(f"Total rows in Excel: {len(df)}")
    print()
    
    imported_count = 0
    skipped_count = 0
    errors = []
    
    insert_sql = """
        INSERT INTO units (
            building_id, unit_name, sq_ft, unit_type_id, notes, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    for idx, row in df.iterrows():
        # Skip rows with no Property Number
        if pd.isna(row.get('Property Number')):
            continue
        
        try:
            # Extract and convert property code
            try:
                property_code = str(int(float(row['Property Number']))).zfill(6)
            except (ValueError, TypeError):
                property_code = str(row['Property Number']).strip()
            
            # Get building_id
            if property_code not in building_map:
                print(f"⚠ Skipping row {idx}: Property code {property_code} not found in buildings")
                skipped_count += 1
                errors.append(f"Row {idx}: Property code {property_code} not in buildings table")
                continue
            
            building_id = building_map[property_code]
            
            # Get unit_name (Unit Demise)
            unit_name = str(row.get('Unit Demise', '')).strip()
            if not unit_name or unit_name == 'nan':
                print(f"⚠ Skipping row {idx}: Missing unit name")
                skipped_count += 1
                continue
            
            # Get sq_ft (Net Area)
            sq_ft = row.get('Net Area')
            if pd.isna(sq_ft):
                print(f"⚠ Skipping row {idx}: Missing Net Area for unit {unit_name}")
                skipped_count += 1
                errors.append(f"Row {idx}: Missing Net Area for {unit_name}")
                continue
            
            try:
                sq_ft = float(sq_ft)
            except (ValueError, TypeError):
                print(f"⚠ Skipping row {idx}: Invalid Net Area '{sq_ft}' for unit {unit_name}")
                skipped_count += 1
                errors.append(f"Row {idx}: Invalid Net Area for {unit_name}")
                continue
            
            # Get unit_type_id
            unit_type_desc = str(row.get('Unit Type', '')).strip()
            if not unit_type_desc or unit_type_desc == 'nan' or unit_type_desc not in type_map:
                print(f"⚠ Skipping row {idx}: Invalid or missing unit type for {unit_name}")
                skipped_count += 1
                errors.append(f"Row {idx}: Missing/invalid unit type for {unit_name}")
                continue
            
            unit_type_id = type_map[unit_type_desc]
            
            # Get notes (Remarks)
            notes = row.get('Remarks')
            if pd.isna(notes):
                notes = None
            else:
                notes = str(notes).strip() or None
            
            # Insert unit
            cursor.execute(insert_sql, (
                building_id,
                unit_name,
                sq_ft,
                unit_type_id,
                notes,
                datetime.now().isoformat(),
                user_id
            ))
            
            if imported_count % 50 == 0 and imported_count > 0:
                print(f"  ... {imported_count} units imported")
            
            imported_count += 1
        
        except Exception as e:
            print(f"✗ Error importing row {idx}: {e}")
            errors.append(f"Row {idx}: {e}")
            skipped_count += 1
    
    print()
    print("=" * 80)
    print("Import Summary")
    print("=" * 80)
    print(f"  Total rows processed: {len(df)}")
    print(f"  Successfully imported: {imported_count}")
    print(f"  Skipped/Errors: {skipped_count}")
    
    if errors and len(errors) <= 20:
        print()
        print("Errors encountered:")
        for error in errors[:20]:
            print(f"  - {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")


def main():
    """Main entry point"""
    excel_file = "data/NEW_bankSchedule.xlsx"
    db_file = "database file/WeeklyReportDB.db"
    sheet_name = "Units"
    
    # Check if Excel file exists
    if not Path(excel_file).exists():
        print(f"Error: Excel file not found: {excel_file}")
        return 1
    
    # Check if database exists
    if not Path(db_file).exists():
        print(f"Error: Database file not found: {db_file}")
        return 1
    
    print("=" * 80)
    print("Unit Import Script")
    print("=" * 80)
    print(f"Source: {excel_file} (Sheet: '{sheet_name}')")
    print(f"Target: {db_file}")
    print()
    print("This will import unit types and units into the database.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Import cancelled")
        return 0
    
    print()
    
    # Read Excel file
    try:
        print(f"Reading Excel file: {excel_file}")
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
        print(f"✓ Successfully read {len(df)} rows from '{sheet_name}' sheet")
        print()
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return 1
    
    # Check required columns
    required_columns = ['Property Number', 'Unit Demise', 'Net Area', 'Unit Type']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(f"✗ Missing required columns: {', '.join(missing)}")
        print(f"Available columns: {', '.join([str(c) for c in df.columns])}")
        return 1
    
    print(f"✓ Found required columns")
    print()
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print(f"✓ Connected to database")
        print()
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return 1
    
    try:
        # Import unit types first
        type_map = import_unit_types(df, cursor)
        
        # Get building mapping
        print("Loading building property codes...")
        building_map = get_building_id_map(cursor)
        print(f"✓ Found {len(building_map)} buildings in database")
        print()
        
        # Import units
        import_units(df, cursor, type_map, building_map, user_id=1)
        
        # Commit all changes
        conn.commit()
        print()
        print("✓ All changes committed to database")
    
    except Exception as e:
        conn.rollback()
        print(f"✗ Error during import: {e}")
        print("✗ Changes rolled back")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        conn.close()
        print("Database connection closed")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
