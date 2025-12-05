"""
Migration 012: Create building_surveyors table
Links surveyors (users) to buildings with temporal tracking
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Create building_surveyors table"""
    db_path = get_db_path()
    
    print(f"Applying migration 012: Create building_surveyors table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create building_surveyors table
        print("\n1. Creating building_surveyors table...")
        cursor.execute("""
            CREATE TABLE building_surveyors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                effective_from DATE NOT NULL,
                effective_to DATE DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created building_surveyors table")
        
        # 2. Create index
        print("\n2. Creating index...")
        cursor.execute("""
            CREATE INDEX idx_building_surveyors 
            ON building_surveyors(building_id, effective_from, effective_to)
        """)
        print("   ✓ Created idx_building_surveyors")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 012 completed successfully")
        print("="*80)
        
        print("\nChanges:")
        print("  ✓ Created building_surveyors table")
        print("  ✓ Supports temporal tracking (effective_from/effective_to)")
        print("  ✓ Multiple surveyors can be assigned to same building")
        print("\nNext steps:")
        print("  - Populate with current surveyor assignments")
        print("  - Use in inspections queries to get surveyor from building")
        
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
