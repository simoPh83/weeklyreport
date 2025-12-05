"""
Migration 016: Create completed_leases table
Append-only archive of successfully completed leases
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Create completed_leases table"""
    db_path = get_db_path()
    
    print(f"Applying migration 016: Create completed_leases table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create completed_leases table
        print("\n1. Creating completed_leases table...")
        cursor.execute("""
            CREATE TABLE completed_leases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                letting_progress_id INTEGER,
                unit_id INTEGER NOT NULL,
                tenant_name TEXT NOT NULL,
                completion_date DATE NOT NULL,
                rent_psf REAL,
                lease_terms TEXT,
                lease_start_date DATE,
                lease_end_date DATE,
                letting_type TEXT CHECK(letting_type IN (
                    'new_letting', 
                    'lease_renewal'
                )),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (letting_progress_id) REFERENCES letting_progress(id),
                FOREIGN KEY (unit_id) REFERENCES units(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created completed_leases table")
        
        # 2. Create indexes
        print("\n2. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_completed_leases_unit 
            ON completed_leases(unit_id)
        """)
        print("   ✓ Created idx_completed_leases_unit")
        
        cursor.execute("""
            CREATE INDEX idx_completed_leases_date 
            ON completed_leases(completion_date)
        """)
        print("   ✓ Created idx_completed_leases_date")
        
        cursor.execute("""
            CREATE INDEX idx_completed_leases_tenant 
            ON completed_leases(tenant_name)
        """)
        print("   ✓ Created idx_completed_leases_tenant")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 016 completed successfully")
        print("="*80)
        
        print("\nTable structure:")
        print("  - id: Primary key")
        print("  - letting_progress_id: Source record (optional FK)")
        print("  - unit_id: Which unit was let")
        print("  - tenant_name: Who took the lease")
        print("  - completion_date: When lease was signed")
        print("  - rent_psf: Final agreed rent per square foot")
        print("  - lease_terms: Final lease terms")
        print("  - lease_start_date: When tenancy begins")
        print("  - lease_end_date: When tenancy expires")
        print("  - letting_type: new_letting or lease_renewal")
        
        print("\nUsage:")
        print("  - Append-only archive (never delete)")
        print("  - Populated when letting_progress.status → 'complete'")
        print("  - Used for 'Completed Deals' section in Friday Report")
        print("  - Can query for historical lease data")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error applying migration: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    apply_migration()
