"""
Migration 013: Create letting_progress table
Main table for tracking active lettings from inspections to completion
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Create letting_progress table"""
    db_path = get_db_path()
    
    print(f"Applying migration 013: Create letting_progress table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create letting_progress table
        print("\n1. Creating letting_progress table...")
        cursor.execute("""
            CREATE TABLE letting_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN (
                    'inspections', 
                    'negotiations', 
                    'agreed', 
                    'complete', 
                    'dead_duck'
                )),
                status_since DATE NOT NULL,
                letting_type TEXT NOT NULL CHECK(letting_type IN (
                    'new_letting', 
                    'lease_renewal'
                )),
                tenant_name TEXT,
                
                -- Offer details (current/latest)
                offered_rent_psf REAL,
                lease_terms TEXT,
                
                -- Solicitor details (when status = agreed)
                solicitor_instructed_date DATE,
                solicitor_ours TEXT,
                solicitor_theirs TEXT,
                
                -- Weekly reporting
                weekly_action TEXT,
                surveyor_id INTEGER,
                
                -- Outcome
                completed_date DATE,
                dead_duck_reason TEXT,
                
                -- Audit fields
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                
                FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (surveyor_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created letting_progress table")
        
        # 2. Create indexes
        print("\n2. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_letting_progress_status 
            ON letting_progress(status, status_since)
        """)
        print("   ✓ Created idx_letting_progress_status")
        
        cursor.execute("""
            CREATE INDEX idx_letting_progress_unit 
            ON letting_progress(unit_id)
        """)
        print("   ✓ Created idx_letting_progress_unit")
        
        cursor.execute("""
            CREATE INDEX idx_letting_progress_surveyor 
            ON letting_progress(surveyor_id)
        """)
        print("   ✓ Created idx_letting_progress_surveyor")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 013 completed successfully")
        print("="*80)
        
        print("\nTable structure:")
        print("  - Core: id, unit_id, status, status_since, letting_type, tenant_name")
        print("  - Offer: offered_rent_psf, lease_terms")
        print("  - Solicitors: instructed_date, solicitor_ours, solicitor_theirs")
        print("  - Reporting: weekly_action, surveyor_id")
        print("  - Outcome: completed_date, dead_duck_reason")
        
        print("\nStatus values:")
        print("  - inspections: Unit being shown to potential tenants")
        print("  - negotiations: Offers on the table")
        print("  - agreed: In solicitors' hands")
        print("  - complete: Lease completed")
        print("  - dead_duck: Deal fell through")
        
        print("\nLetting types:")
        print("  - new_letting: New tenant")
        print("  - lease_renewal: Existing tenant renewal")
        
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
