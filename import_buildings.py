"""
Import Buildings from Excel Spreadsheet
Reads NEW_bankSchedule.xlsx and imports unique properties into Buildings table
"""
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import sys


def import_buildings_from_excel(excel_path: str, db_path: str, user_id: int = 1):
    """
    Import buildings from Excel file into SQLite database
    
    Args:
        excel_path: Path to Excel file
        db_path: Path to SQLite database
        user_id: User ID for created_by field (default: 1 for admin)
    """
    print(f"Reading Excel file: {excel_path}")
    print(f"Target database: {db_path}")
    print("-" * 80)
    
    # Read Excel file
    try:
        df = pd.read_excel(excel_path, sheet_name="Bank Schedule", header=2)
        print(f"✓ Successfully read {len(df)} rows from 'Bank Schedule' sheet")
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return
    
    # Check required columns exist
    required_columns = ['Property', 'Property Number', 'Client']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(f"✗ Missing required columns: {', '.join(missing)}")
        print(f"Available columns: {', '.join(df.columns)}")
        return
    
    print(f"✓ Found required columns: {', '.join(required_columns)}")
    print("-" * 80)
    
    # Get unique properties
    # Group by Property and take first occurrence for Property Number and Client
    unique_properties = df.groupby('Property').agg({
        'Property Number': 'first',
        'Client': 'first'
    }).reset_index()
    
    print(f"Found {len(unique_properties)} unique properties to import:")
    print()
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"✓ Connected to database")
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return
    
    # Prepare insert statement
    insert_sql = """
        INSERT INTO buildings (
            property_code, property_name, property_address, postcode, client_code,
            acquisition_date, disposal_date, notes, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    imported_count = 0
    skipped_count = 0
    errors = []
    
    print("-" * 80)
    print("Importing properties:")
    print()
    
    for idx, row in unique_properties.iterrows():
        property_address = str(row['Property']).strip()
        
        # Convert property_code - handle both float and string
        try:
            property_code = str(int(float(row['Property Number']))).zfill(6)
        except (ValueError, TypeError):
            property_code = str(row['Property Number']).strip()
        
        client_code = str(row['Client']).strip()
        
        # Validate property_code is 6 digits
        if not property_code.isdigit() or len(property_code) != 6:
            print(f"⚠ Skipping '{property_address}' - Invalid property code: '{property_code}' (must be 6 digits)")
            skipped_count += 1
            errors.append(f"Invalid property code '{property_code}' for {property_address}")
            continue
        
        # Check if property_code already exists
        cursor.execute("SELECT id FROM buildings WHERE property_code = ?", (property_code,))
        if cursor.fetchone():
            print(f"⚠ Skipping '{property_address}' - Property code {property_code} already exists")
            skipped_count += 1
            continue
        
        try:
            # Use property_address for both property_name and property_address
            cursor.execute(insert_sql, (
                property_code,           # property_code
                property_address,        # property_name (duplicated)
                property_address,        # property_address
                "TBD",                   # postcode (placeholder until we get real postcodes)
                client_code,             # client_code
                None,                    # acquisition_date
                None,                    # disposal_date
                None,                    # notes
                datetime.now().isoformat(),  # created_at
                user_id                  # created_by
            ))
            
            print(f"✓ Imported: {property_code} - {property_address} (Client: {client_code})")
            imported_count += 1
            
        except Exception as e:
            print(f"✗ Error importing '{property_address}': {e}")
            errors.append(f"Error importing {property_address}: {e}")
            skipped_count += 1
    
    # Commit changes
    try:
        conn.commit()
        print()
        print("-" * 80)
        print("Import Summary:")
        print(f"  Total unique properties in Excel: {len(unique_properties)}")
        print(f"  Successfully imported: {imported_count}")
        print(f"  Skipped/Errors: {skipped_count}")
        
        if errors:
            print()
            print("Errors encountered:")
            for error in errors:
                print(f"  - {error}")
        
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
    # Default paths
    excel_file = "data/NEW_bankSchedule.xlsx"
    db_file = "database file/WeeklyReportDB.db"
    
    # Check if Excel file exists
    if not Path(excel_file).exists():
        print(f"Error: Excel file not found: {excel_file}")
        print("Please ensure NEW_bankSchedule.xlsx is in the current directory")
        return 1
    
    # Check if database exists
    if not Path(db_file).exists():
        print(f"Error: Database file not found: {db_file}")
        return 1
    
    # Confirm before proceeding
    print("=" * 80)
    print("Building Import Script")
    print("=" * 80)
    print(f"Source: {excel_file} (Sheet: 'Bank Schedule')")
    print(f"Target: {db_file}")
    print()
    print("This will import unique properties into the Buildings table.")
    print("Properties with existing property codes will be skipped.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Import cancelled")
        return 0
    
    print()
    print("=" * 80)
    
    # Run import
    import_buildings_from_excel(excel_file, db_file, user_id=1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
