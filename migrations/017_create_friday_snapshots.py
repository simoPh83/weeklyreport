"""
Migration 017: Create friday_snapshots table
Weekly snapshots of letting_progress for week-over-week comparison
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Create friday_snapshots table"""
    db_path = get_db_path()
    
    print(f"Applying migration 017: Create friday_snapshots table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create friday_snapshots table
        print("\n1. Creating friday_snapshots table...")
        cursor.execute("""
            CREATE TABLE friday_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE NOT NULL,
                unit_id INTEGER NOT NULL,
                letting_progress_id INTEGER,
                status TEXT,
                tenant_name TEXT,
                weekly_action TEXT,
                key_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (unit_id) REFERENCES units(id),
                FOREIGN KEY (letting_progress_id) REFERENCES letting_progress(id)
            )
        """)
        print("   ✓ Created friday_snapshots table")
        
        # 2. Create indexes
        print("\n2. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_snapshots_date 
            ON friday_snapshots(snapshot_date)
        """)
        print("   ✓ Created idx_snapshots_date")
        
        cursor.execute("""
            CREATE INDEX idx_snapshots_unit_date 
            ON friday_snapshots(unit_id, snapshot_date)
        """)
        print("   ✓ Created idx_snapshots_unit_date")
        
        cursor.execute("""
            CREATE INDEX idx_snapshots_letting 
            ON friday_snapshots(letting_progress_id)
        """)
        print("   ✓ Created idx_snapshots_letting")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 017 completed successfully")
        print("="*80)
        
        print("\nTable structure:")
        print("  - id: Primary key")
        print("  - snapshot_date: The Friday this snapshot was taken")
        print("  - unit_id: Which unit")
        print("  - letting_progress_id: Active letting at that time (NULL if none)")
        print("  - status: Status at time of snapshot")
        print("  - tenant_name: Tenant name at time of snapshot")
        print("  - weekly_action: The action/update for that week")
        print("  - key_metrics: JSON field for additional data")
        
        print("\nUsage:")
        print("  - Take snapshot every Friday (manual or scheduled)")
        print("  - Compare current vs last Friday to generate 'What Changed' report")
        print("  - Query specific date to see state at that time")
        print("  - key_metrics can store: {rent_psf, days_in_status, etc.}")
        
        print("\nExample query:")
        print("  SELECT * FROM friday_snapshots")
        print("  WHERE snapshot_date = (")
        print("    SELECT MAX(snapshot_date) FROM friday_snapshots")
        print("    WHERE snapshot_date < CURRENT_DATE")
        print("  )")
        
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
