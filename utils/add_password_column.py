"""
Add password_hash and email columns to existing users table
Run this once to update your database schema
"""
import sqlite3
import sys
from pathlib import Path

def add_password_columns(db_path: str):
    """Add password_hash and email columns to users table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add password_hash column if not exists
        if 'password_hash' not in columns:
            print("Adding password_hash column...")
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            print("✓ password_hash column added")
        else:
            print("✓ password_hash column already exists")
        
        # Add email column if not exists
        if 'email' not in columns:
            print("Adding email column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            print("✓ email column added")
        else:
            print("✓ email column already exists")
        
        conn.commit()
        print("\nDatabase schema updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    # Get database path from command line or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = str(Path(__file__).parent.parent / 'weekly_report.db')
    
    print(f"Updating database schema: {db_path}\n")
    add_password_columns(db_path)
    print("\nNow run: python utils\\migrate_passwords.py")
