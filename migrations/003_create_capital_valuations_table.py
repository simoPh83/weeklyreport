"""
Migration: Create Capital Valuations table
Stores property valuations with building_id and year as composite unique key
"""
import sqlite3
import sys
from pathlib import Path


def run_migration(db_path: str):
    """
    Create capital_valuations table
    
    Args:
        db_path: Path to SQLite database
    """
    print(f"This will create the capital_valuations table in: {db_path}")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled")
        return
    
    print("\nStarting migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop old table if it exists
        print("Dropping old capital_valuations table if exists...")
        cursor.execute("DROP TABLE IF EXISTS capital_valuations")
        
        # Create capital_valuations table
        print("Creating capital_valuations table...")
        cursor.execute("""
            CREATE TABLE capital_valuations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                valuation_year INTEGER NOT NULL,
                valuation_amount REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                UNIQUE(building_id, valuation_year),
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show new schema
        print("\nNew capital_valuations table schema:")
        cursor.execute("PRAGMA table_info(capital_valuations)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
    
    except Exception as e:
        conn.rollback()
        print(f"\nError during migration: {e}")
        raise
    
    finally:
        conn.close()


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python 003_create_capital_valuations_table.py <database_path>")
        return 1
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return 1
    
    run_migration(db_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
