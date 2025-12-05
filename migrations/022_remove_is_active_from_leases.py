import sqlite3
import os
from datetime import datetime

def migrate():
    """Remove is_active field from leases table"""
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database file', 'WeeklyReportDB.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting migration 022: Remove is_active from leases table...")
        
        # SQLite doesn't support DROP COLUMN directly, need to recreate table
        # 1. Create new table without is_active
        cursor.execute("""
            CREATE TABLE leases_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                unit_id INTEGER NOT NULL,
                rent_pa REAL NOT NULL,
                start_date DATE NOT NULL,
                break_date DATE,
                expiry_date DATE NOT NULL,
                bank_schedule_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        print("✓ Created new leases table without is_active")
        
        # 2. Copy data from old table to new (excluding is_active)
        cursor.execute("""
            INSERT INTO leases_new (
                id, tenant_id, unit_id, rent_pa, start_date, break_date, 
                expiry_date, bank_schedule_date, created_at, created_by, 
                updated_at, updated_by
            )
            SELECT 
                id, tenant_id, unit_id, rent_pa, start_date, break_date, 
                expiry_date, bank_schedule_date, created_at, created_by, 
                updated_at, updated_by
            FROM leases
        """)
        rows_copied = cursor.rowcount
        print(f"✓ Copied {rows_copied} rows to new table")
        
        # 3. Drop old table
        cursor.execute("DROP TABLE leases")
        print("✓ Dropped old leases table")
        
        # 4. Rename new table to leases
        cursor.execute("ALTER TABLE leases_new RENAME TO leases")
        print("✓ Renamed new table to leases")
        
        # 5. Recreate indexes (excluding is_active index)
        cursor.execute("CREATE INDEX idx_leases_unit_id ON leases(unit_id)")
        cursor.execute("CREATE INDEX idx_leases_tenant_id ON leases(tenant_id)")
        cursor.execute("CREATE INDEX idx_leases_expiry_date ON leases(expiry_date)")
        print("✓ Recreated indexes")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("MIGRATION 022 COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Migrated {rows_copied} lease records")
        print("Removed is_active field and index")
        print("="*60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
