"""
Database Migration: Restructure Buildings Table
Migration Date: December 2, 2025
Description: Update buildings table schema to match production UK property management system
"""
import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str):
    """Migrate buildings table to new schema"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting migration...")
        
        # Drop old buildings table (data is fictional, safe to drop)
        print("Dropping old buildings table...")
        cursor.execute("DROP TABLE IF EXISTS buildings")
        
        # Create new buildings table with updated schema
        print("Creating new buildings table...")
        cursor.execute("""
            CREATE TABLE buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_code TEXT UNIQUE NOT NULL,
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
        
        # Update units table if needed - building_id foreign key is still valid
        # (units table references buildings.id which is still INTEGER PRIMARY KEY)
        
        conn.commit()
        print("Migration completed successfully!")
        
        # Show new schema
        cursor.execute("PRAGMA table_info(buildings)")
        columns = cursor.fetchall()
        print("\nNew buildings table schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        return False
        
    finally:
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default to asking user
        db_path = input("Enter path to database file: ").strip()
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)
    
    # Confirm before running
    print(f"\nThis will restructure the buildings table in: {db_path}")
    print("WARNING: This will DELETE all existing building data!")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        success = migrate_database(db_path)
        sys.exit(0 if success else 1)
    else:
        print("Migration cancelled.")
        sys.exit(0)
