"""
Import Capital Valuations from Excel Spreadsheet
Reads NEW_bankSchedule.xlsx "Buildings" sheet and imports 2024 valuations
"""
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import sys
from openpyxl import load_workbook


def get_building_id_by_name(cursor: sqlite3.Cursor) -> dict:
    """
    Get mapping of property_name to building_id
    
    Args:
        cursor: Database cursor
        
    Returns:
        Dictionary mapping property_name to building_id
    """
    cursor.execute("SELECT id, property_name FROM buildings")
    return {row[1]: row[0] for row in cursor.fetchall()}


def import_capital_valuations(excel_path: str, db_path: str, user_id: int = 1):
    """
    Import capital valuations from Excel file into SQLite database
    
    Args:
        excel_path: Path to Excel file
        db_path: Path to SQLite database
        user_id: User ID for created_by field (default: 1 for admin)
    """
    print(f"Reading Excel file: {excel_path}")
    print(f"Target database: {db_path}")
    print("-" * 80)
    
    # Read Excel file - use openpyxl engine to get calculated formula values
    try:
        # Load workbook with data_only=True to get formula results
        wb = load_workbook(excel_path, data_only=True)
        ws = wb["Buildings"]
        
        # Convert to pandas DataFrame
        data = ws.values
        cols = next(data)
        df = pd.DataFrame(data, columns=cols)
        
        print(f"✓ Successfully read {len(df)} rows from 'Buildings' sheet")
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return
    
    # Check required columns exist
    if 'Building' not in df.columns:
        print(f"✗ Missing 'Building' column")
        print(f"Available columns: {', '.join([str(c) for c in df.columns])}")
        return
    
    # Find the 2024 valuation column
    valuation_col = None
    for col in df.columns:
        col_str = str(col)
        if '2024' in col_str and ('Cap' in col_str or 'Valn' in col_str or 'Valuation' in col_str):
            valuation_col = col
            break
    
    if not valuation_col:
        print(f"✗ Could not find 2024 Capital Valuation column")
        print(f"Available columns: {', '.join([str(c) for c in df.columns])}")
        return
    
    print(f"✓ Found valuation column: '{valuation_col}'")
    print("-" * 80)
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"✓ Connected to database")
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return
    
    # Get building name to ID mapping
    print("Loading building names...")
    building_map = get_building_id_by_name(cursor)
    print(f"✓ Found {len(building_map)} buildings in database")
    print()
    
    # Prepare insert statement
    insert_sql = """
        INSERT INTO capital_valuations (
            building_id, valuation_year, valuation_amount, notes, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?)
    """
    
    imported_count = 0
    skipped_count = 0
    errors = []
    
    print("-" * 80)
    print("Importing valuations:")
    print()
    
    for idx, row in df.iterrows():
        # Skip rows with no Building name
        if pd.isna(row.get('Building')):
            continue
        
        building_name = str(row['Building']).strip()
        
        # Skip if no building name
        if not building_name or building_name == 'nan':
            continue
        
        # Get valuation amount
        valuation = row.get(valuation_col)
        if pd.isna(valuation):
            print(f"⚠ Skipping '{building_name}' - No valuation value")
            skipped_count += 1
            continue
        
        try:
            valuation_amount = float(valuation)
        except (ValueError, TypeError):
            print(f"⚠ Skipping '{building_name}' - Invalid valuation: '{valuation}'")
            skipped_count += 1
            errors.append(f"Invalid valuation for {building_name}: {valuation}")
            continue
        
        # Use 0 as default if valuation is 0 or negative
        if valuation_amount <= 0:
            valuation_amount = 0.0
        
        # Get building_id
        if building_name not in building_map:
            print(f"⚠ Warning: '{building_name}' not found in buildings table - using building_id=0")
            building_id = 0
            errors.append(f"Building not found: {building_name}")
        else:
            building_id = building_map[building_name]
        
        try:
            # Check if valuation already exists for this building and year
            cursor.execute(
                "SELECT id FROM capital_valuations WHERE building_id = ? AND valuation_year = ?",
                (building_id, 2024)
            )
            if cursor.fetchone():
                print(f"⚠ Skipping '{building_name}' - 2024 valuation already exists")
                skipped_count += 1
                continue
            
            # Insert valuation
            cursor.execute(insert_sql, (
                building_id,
                2024,
                valuation_amount,
                None,  # notes
                datetime.now().isoformat(),
                user_id
            ))
            
            print(f"✓ Imported: {building_name} - £{valuation_amount:,.2f}")
            imported_count += 1
            
        except Exception as e:
            print(f"✗ Error importing '{building_name}': {e}")
            errors.append(f"Error importing {building_name}: {e}")
            skipped_count += 1
    
    # Commit changes
    try:
        conn.commit()
        print()
        print("-" * 80)
        print("Import Summary:")
        print(f"  Total rows in Excel: {len(df)}")
        print(f"  Successfully imported: {imported_count}")
        print(f"  Skipped/Errors: {skipped_count}")
        
        if errors:
            print()
            print("Issues encountered:")
            for error in errors[:20]:
                print(f"  - {error}")
            if len(errors) > 20:
                print(f"  ... and {len(errors) - 20} more issues")
        
        print()
        print("✓ Changes committed to database")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error committing changes: {e}")
        print("✗ Changes rolled back")
    
    finally:
        conn.close()
        print("Database connection closed")


def main():
    """Main entry point"""
    excel_file = "data/NEW_bankSchedule.xlsx"
    db_file = "database file/WeeklyReportDB.db"
    
    # Check if Excel file exists
    if not Path(excel_file).exists():
        print(f"Error: Excel file not found: {excel_file}")
        return 1
    
    # Check if database exists
    if not Path(db_file).exists():
        print(f"Error: Database file not found: {db_file}")
        return 1
    
    # Confirm before proceeding
    print("=" * 80)
    print("Capital Valuations Import Script")
    print("=" * 80)
    print(f"Source: {excel_file} (Sheet: 'Buildings')")
    print(f"Target: {db_file}")
    print()
    print("This will import 2024 capital valuations into the database.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Import cancelled")
        return 0
    
    print()
    print("=" * 80)
    
    # Run import
    import_capital_valuations(excel_file, db_file, user_id=1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
