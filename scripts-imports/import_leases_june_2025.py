"""
Import lease data from Excel file [ORIGINAL] Leasing Bank Schedule June 2025.xlsx
Matches Property + Unit Demise to identify correct unit and tenant
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def parse_date(date_value):
    """Parse date from Excel, handling various formats"""
    if pd.isna(date_value):
        return None
    
    # If it's already a datetime object
    if isinstance(date_value, pd.Timestamp):
        return date_value.strftime('%Y-%m-%d')
    
    # If it's a string, try to parse it
    if isinstance(date_value, str):
        date_value = date_value.strip()
        if not date_value:
            return None
        try:
            # Try various date formats
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except:
            return None
    
    return None


def import_leases():
    """Import lease data from Excel file"""
    db_path = get_db_path()
    excel_path = Path(__file__).parent.parent / "data" / "[ORIGINAL] Leasing Bank Schedule June 2025.xlsx"
    
    print(f"Reading Excel file: {excel_path}")
    
    # Read Excel file with headers on row 3 (index 2)
    df = pd.read_excel(excel_path, sheet_name=0, header=2)
    
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
    
    # Bank schedule date for this import
    bank_schedule_date = '2025-06-30'
    
    # Statistics
    total_rows = 0
    matched_units = 0
    matched_tenants = 0
    inserted = 0
    updated = 0
    skipped_no_tenant = 0
    skipped_no_unit = 0
    skipped_no_dates = 0
    errors = []
    
    print("\n" + "="*80)
    print("Processing lease data...")
    print("="*80)
    
    for idx, row in df.iterrows():
        total_rows += 1
        
        # Get values from columns
        property_name = row.get('Property')
        unit_demise = row.get('Unit Demise')
        tenant_name = row.get('Tenant Name')  # Note: 'Tenant Name' not 'Tenant'
        start_date_raw = row.get('Start            Date')
        expiry_date_raw = row.get('Expiry   Date')
        break_date_raw = row.get('Break Date ')
        rent_pa_raw = row.get('Rent PA (£) ')
        
        # Skip rows without unit demise
        if pd.isna(unit_demise):
            continue
        
        # Skip if no property name
        if pd.isna(property_name):
            continue
        
        # Skip if no tenant
        if pd.isna(tenant_name) or str(tenant_name).strip() == '':
            skipped_no_tenant += 1
            continue
        
        # Clean values
        property_name = str(property_name).strip()
        unit_demise = str(unit_demise).strip()
        tenant_name = str(tenant_name).strip()
        
        # Parse dates
        start_date = parse_date(start_date_raw)
        expiry_date = parse_date(expiry_date_raw)
        break_date = parse_date(break_date_raw)
        
        # Skip if no start or expiry date
        if not start_date or not expiry_date:
            skipped_no_dates += 1
            continue
        
        # Parse rent
        try:
            if pd.isna(rent_pa_raw) or rent_pa_raw == 0:
                rent_pa = 0.0
            else:
                rent_pa = float(rent_pa_raw)
        except (ValueError, TypeError):
            errors.append(f"Row {idx+3}: Invalid rent value '{rent_pa_raw}'")
            continue
        
        # Find matching unit in database
        cursor.execute("""
            SELECT u.id, u.unit_name, b.property_address, b.property_name
            FROM units u
            JOIN buildings b ON u.building_id = b.id
            WHERE (b.property_address = ? OR b.property_name = ?)
              AND u.unit_name = ?
              AND u.is_current = 1
        """, (property_name, property_name, unit_demise))
        
        unit_row = cursor.fetchone()
        
        if not unit_row:
            skipped_no_unit += 1
            if idx < 50:  # Only print first 50 for debugging
                print(f"  ✗ No unit match: {property_name} - {unit_demise}")
            continue
        
        unit_id = unit_row['id']
        matched_units += 1
        
        # Find or note tenant
        cursor.execute("""
            SELECT id FROM tenants
            WHERE tenant_name = ?
        """, (tenant_name,))
        
        tenant_row = cursor.fetchone()
        
        if not tenant_row:
            print(f"  ℹ Tenant not found, will skip: '{tenant_name}'")
            skipped_no_tenant += 1
            continue
        
        tenant_id = tenant_row['id']
        matched_tenants += 1
        
        # Check if lease already exists for this unit and dates
        cursor.execute("""
            SELECT id FROM leases
            WHERE unit_id = ?
              AND tenant_id = ?
              AND start_date = ?
              AND expiry_date = ?
        """, (unit_id, tenant_id, start_date, expiry_date))
        
        existing = cursor.fetchone()
        
        lease_data = {
            'tenant_id': tenant_id,
            'unit_id': unit_id,
            'rent_pa': rent_pa,
            'start_date': start_date,
            'break_date': break_date,
            'expiry_date': expiry_date,
            'bank_schedule_date': bank_schedule_date
        }
        
        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE leases
                SET rent_pa = ?,
                    break_date = ?,
                    bank_schedule_date = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = ?
                WHERE id = ?
            """, (rent_pa, break_date, bank_schedule_date, user_id, existing['id']))
            updated += 1
            print(f"  ↻ Updated: {property_name} - {unit_demise} - {tenant_name}: £{rent_pa:,.0f} PA")
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO leases (tenant_id, unit_id, rent_pa, start_date, break_date, 
                                   expiry_date, bank_schedule_date, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (tenant_id, unit_id, rent_pa, start_date, break_date, 
                  expiry_date, bank_schedule_date, user_id))
            inserted += 1
            print(f"  ✓ Inserted: {property_name} - {unit_demise} - {tenant_name}: £{rent_pa:,.0f} PA")
    
    # Commit changes
    conn.commit()
    
    # Print summary
    print("\n" + "="*80)
    print("IMPORT SUMMARY")
    print("="*80)
    print(f"Total rows processed: {total_rows}")
    print(f"Matched units: {matched_units}")
    print(f"Matched tenants: {matched_tenants}")
    print(f"  - Inserted: {inserted}")
    print(f"  - Updated: {updated}")
    print(f"Skipped (no tenant): {skipped_no_tenant}")
    print(f"Skipped (no unit match): {skipped_no_unit}")
    print(f"Skipped (no dates): {skipped_no_dates}")
    
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    # Show some statistics from database
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN date(?) BETWEEN date(start_date) AND date(expiry_date) THEN 1 ELSE 0 END) as active,
               SUM(CASE WHEN date(?) BETWEEN date(start_date) AND date(expiry_date) THEN rent_pa ELSE 0 END) as total_active_rent
        FROM leases
        WHERE bank_schedule_date = ?
    """, (bank_schedule_date, bank_schedule_date, bank_schedule_date))
    
    stats = cursor.fetchone()
    
    print(f"\nDatabase statistics for {bank_schedule_date}:")
    print(f"  Total leases: {stats['total']}")
    print(f"  Active leases: {stats['active']}")
    total_rent = stats['total_active_rent'] if stats['total_active_rent'] else 0.0
    print(f"  Total active rent: £{total_rent:,.2f} PA")
    
    conn.close()
    
    print("\n✓ Import completed successfully")


if __name__ == "__main__":
    import_leases()
