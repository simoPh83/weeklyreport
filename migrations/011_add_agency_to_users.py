"""
Migration 011: Add agency field to users table
Allows tracking of external agents/brokers (LEM, KLM, Bluebook, etc.)
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Add agency column to users table"""
    db_path = get_db_path()
    
    print(f"Applying migration 011: Add agency field to users table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n1. Adding agency column to users table...")
        cursor.execute("""
            ALTER TABLE users ADD COLUMN agency TEXT
        """)
        print("   ✓ Added agency column")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 011 completed successfully")
        print("="*80)
        
        print("\nChanges:")
        print("  ✓ Added users.agency (TEXT, NULL)")
        print("\nUsage:")
        print("  - Internal surveyors: agency = NULL or 'In-House'")
        print("  - External agents: agency = 'LEM', 'KLM', 'Bluebook', etc.")
        
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
