"""
Migration 007: Create ERVs table
ERV = Estimated Rental Value - tracks property valuation over years
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Apply the ERVs table migration"""
    db_path = get_db_path()
    
    print(f"Applying migration 007: Create ERVs table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create ERVs table
        print("Creating ERVs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ervs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_id INTEGER NOT NULL,
                value REAL NOT NULL,
                year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id),
                UNIQUE(unit_id, year)
            )
        """)
        
        # Create index for faster lookups
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ervs_unit_id 
            ON ervs(unit_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ervs_year 
            ON ervs(year)
        """)
        
        conn.commit()
        print("✓ ERVs table created successfully")
        print("✓ Indexes created successfully")
        
        # Verify table was created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ervs'
        """)
        if cursor.fetchone():
            print("✓ Migration 007 completed successfully")
            return True
        else:
            print("✗ ERVs table was not created")
            return False
            
    except sqlite3.Error as e:
        print(f"✗ Error applying migration: {e}")
        return False
    finally:
        if conn:
            conn.close()


def rollback_migration():
    """Rollback the ERVs table migration"""
    db_path = get_db_path()
    
    print(f"Rolling back migration 007: Drop ERVs table...")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop indexes
        print("Dropping indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_ervs_unit_id")
        cursor.execute("DROP INDEX IF EXISTS idx_ervs_year")
        
        # Drop table
        print("Dropping ERVs table...")
        cursor.execute("DROP TABLE IF EXISTS ervs")
        
        conn.commit()
        print("✓ Migration 007 rolled back successfully")
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error rolling back migration: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        apply_migration()
