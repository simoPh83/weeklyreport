"""
Migration: Create tenants and business_categories tables
"""
import sqlite3
import sys
from pathlib import Path


def run_migration(db_path: str):
    """
    Create tenants and business_categories tables
    
    Args:
        db_path: Path to SQLite database
    """
    print(f"This will create tenants and business_categories tables in: {db_path}")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled")
        return
    
    print("\nStarting migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create business_categories table
        print("Creating business_categories table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # Create tenants table
        print("Creating tenants table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_name TEXT NOT NULL,
                trading_as TEXT,
                b2c INTEGER DEFAULT 0,
                category_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (category_id) REFERENCES business_categories(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        print("Migration completed successfully!")
        
        # Show new table schemas
        print("\nNew business_categories table schema:")
        cursor.execute("PRAGMA table_info(business_categories)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
        
        print("\nNew tenants table schema:")
        cursor.execute("PRAGMA table_info(tenants)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
    
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"\nError during migration: {e}")
        raise
    
    finally:
        conn.close()


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python 005_create_tenants_and_categories.py <database_path>")
        return 1
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return 1
    
    run_migration(db_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
