"""
Import tenants from Excel file
Reads unique tenant names from Units sheet and populates tenants table
"""
import sqlite3
import pandas as pd
from pathlib import Path


def import_tenants():
    """Import unique tenants from Excel Units sheet"""
    
    # File paths
    excel_file = Path("data/31 August 2025 Bank Schedule.xlsx")
    db_file = Path("database file/WeeklyReportDB.db")
    
    if not excel_file.exists():
        print(f"Error: Excel file not found: {excel_file}")
        return
    
    if not db_file.exists():
        print(f"Error: Database file not found: {db_file}")
        return
    
    print(f"Reading tenant data from {excel_file}...")
    
    # Read Units sheet
    df = pd.read_excel(excel_file, sheet_name="Units", header=1)
    
    print(f"Total rows in Excel: {len(df)}")
    
    # Get unique tenant names from column J (Tenant Name)
    tenant_names = df.iloc[:, 9].dropna().unique()  # Column J is index 9 (0-based)
    
    # Filter out "Vacant" and empty strings
    tenant_names = [
        name.strip() for name in tenant_names 
        if pd.notna(name) and str(name).strip() and str(name).strip().lower() != 'vacant'
    ]
    
    print(f"Found {len(tenant_names)} unique tenants (excluding 'Vacant')")
    
    # Connect to database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # First, ensure we have a default business category
    cursor.execute("""
        INSERT OR IGNORE INTO business_categories (id, description)
        VALUES (1, 'Unclassified')
    """)
    
    imported_count = 0
    skipped_count = 0
    
    for tenant_name in sorted(tenant_names):
        try:
            # Check if tenant already exists
            cursor.execute(
                "SELECT id FROM tenants WHERE tenant_name = ?",
                (tenant_name,)
            )
            
            if cursor.fetchone():
                print(f"Skipped (already exists): {tenant_name}")
                skipped_count += 1
                continue
            
            # Insert tenant
            cursor.execute("""
                INSERT INTO tenants (tenant_name, trading_as, b2c, category_id, notes)
                VALUES (?, NULL, 0, 1, NULL)
            """, (tenant_name,))
            
            print(f"Imported: {tenant_name}")
            imported_count += 1
            
        except Exception as e:
            print(f"Error importing {tenant_name}: {e}")
            skipped_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nImport complete!")
    print(f"Successfully imported: {imported_count}")
    print(f"Skipped/Errors: {skipped_count}")


if __name__ == '__main__':
    response = input("This will import tenants from Excel. Continue? (yes/no): ").strip().lower()
    if response == 'yes':
        import_tenants()
    else:
        print("Import cancelled")
