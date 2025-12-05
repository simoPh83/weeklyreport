"""
Migration 014: Create inspections table
Append-only log of unit viewings/inspections
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Create inspections table"""
    db_path = get_db_path()
    
    print(f"Applying migration 014: Create inspections table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create inspections table
        print("\n1. Creating inspections table...")
        cursor.execute("""
            CREATE TABLE inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_id INTEGER NOT NULL,
                inspection_date DATE NOT NULL,
                tenant_name TEXT,
                agent_id INTEGER,
                proposed_terms TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (agent_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created inspections table")
        
        # 2. Create indexes
        print("\n2. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_inspections_date 
            ON inspections(inspection_date)
        """)
        print("   ✓ Created idx_inspections_date")
        
        cursor.execute("""
            CREATE INDEX idx_inspections_unit 
            ON inspections(unit_id)
        """)
        print("   ✓ Created idx_inspections_unit")
        
        cursor.execute("""
            CREATE INDEX idx_inspections_agent 
            ON inspections(agent_id)
        """)
        print("   ✓ Created idx_inspections_agent")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 014 completed successfully")
        print("="*80)
        
        print("\nTable structure:")
        print("  - id: Primary key")
        print("  - unit_id: Which unit was inspected")
        print("  - inspection_date: When the viewing happened")
        print("  - tenant_name: Potential tenant's name")
        print("  - agent_id: Agent/broker who conducted inspection (links to users.id)")
        print("  - proposed_terms: What terms were discussed")
        print("  - remarks: Feedback/comments from inspection")
        print("  - created_at, created_by: Audit fields")
        
        print("\nNote:")
        print("  - agent_id links to users table (includes external agents with agency field)")
        print("  - Surveyor retrieved via unit → building → building_surveyors")
        print("  - Append-only: inspections are never deleted, only added")
        
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
