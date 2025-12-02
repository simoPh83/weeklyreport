"""
Migration: Restructure Units table and create Unit Types lookup table
Creates unit_types table and restructures units table for UK commercial property format
"""
import sqlite3
import sys
from pathlib import Path


def run_migration(db_path: str):
    """
    Restructure units table and create unit_types lookup table
    
    Args:
        db_path: Path to SQLite database
    """
    print(f"This will restructure the units table and create unit_types table in: {db_path}")
    print("WARNING: This will DELETE all existing unit data!")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled")
        return
    
    print("\nStarting migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop old units table if it exists
        print("Dropping old units table...")
        cursor.execute("DROP TABLE IF EXISTS units")
        
        # Drop old unit_types table if it exists
        print("Dropping old unit_types table if exists...")
        cursor.execute("DROP TABLE IF EXISTS unit_types")
        
        # Create unit_types lookup table
        print("Creating unit_types table...")
        cursor.execute("""
            CREATE TABLE unit_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT UNIQUE NOT NULL
            )
        """)
        
        # Create new units table
        print("Creating new units table...")
        cursor.execute("""
            CREATE TABLE units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                unit_name TEXT NOT NULL,
                sq_ft REAL NOT NULL,
                unit_type_id INTEGER NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (unit_type_id) REFERENCES unit_types(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show new schema
        print("\nNew unit_types table schema:")
        cursor.execute("PRAGMA table_info(unit_types)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
        
        print("\nNew units table schema:")
        cursor.execute("PRAGMA table_info(units)")
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
        print("Usage: python 002_restructure_units_and_unit_types.py <database_path>")
        return 1
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return 1
    
    run_migration(db_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
