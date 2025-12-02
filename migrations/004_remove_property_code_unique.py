"""
Migration: Remove UNIQUE constraint from buildings.property_code
Recreates buildings table without UNIQUE constraint on property_code
"""
import sqlite3
import sys
from pathlib import Path


def run_migration(db_path: str):
    """
    Remove UNIQUE constraint from property_code column
    
    Args:
        db_path: Path to SQLite database
    """
    print(f"This will remove the UNIQUE constraint from buildings.property_code in: {db_path}")
    print("WARNING: This requires recreating the buildings table!")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled")
        return
    
    print("\nStarting migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Temporarily disable foreign key constraints
        print("Disabling foreign key constraints...")
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create new buildings table without UNIQUE constraint
        print("Creating new buildings table...")
        cursor.execute("""
            CREATE TABLE buildings_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_code TEXT NOT NULL,
                property_name TEXT,
                property_address TEXT NOT NULL,
                postcode TEXT NOT NULL,
                client_code TEXT NOT NULL,
                acquisition_date DATE,
                disposal_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # Copy data from old table to new table
        print("Copying data from old table...")
        cursor.execute("""
            INSERT INTO buildings_new 
            SELECT * FROM buildings
        """)
        
        # Drop old table
        print("Dropping old table...")
        cursor.execute("DROP TABLE buildings")
        
        # Rename new table to original name
        print("Renaming new table...")
        cursor.execute("ALTER TABLE buildings_new RENAME TO buildings")
        
        # Re-enable foreign key constraints
        print("Re-enabling foreign key constraints...")
        cursor.execute("COMMIT")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Verify foreign keys
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        if fk_errors:
            print("WARNING: Foreign key issues detected:")
            for error in fk_errors:
                print(f"  {error}")
        
        print("Migration completed successfully!")
        
        # Show new schema
        print("\nNew buildings table schema:")
        cursor.execute("PRAGMA table_info(buildings)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
    
    except Exception as e:
        cursor.execute("ROLLBACK")
        cursor.execute("PRAGMA foreign_keys = ON")
        print(f"\nError during migration: {e}")
        raise
    
    finally:
        conn.close()


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python 004_remove_property_code_unique.py <database_path>")
        return 1
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return 1
    
    run_migration(db_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
