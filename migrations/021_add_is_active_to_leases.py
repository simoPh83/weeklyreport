"""
Migration 021: Add is_active field and index to leases table
This field indicates whether a lease is currently active (today between start_date and expiry_date).
Includes an index for fast filtering of active leases.
"""

import sqlite3
from datetime import datetime

DB_PATH = "database file/WeeklyReportDB.db"

def migrate():
    """Add is_active column and index to leases table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add is_active column (default to 0/False)
        cursor.execute("""
            ALTER TABLE leases
            ADD COLUMN is_active INTEGER DEFAULT 0
        """)
        
        conn.commit()
        print("✓ Added is_active column to leases table")
        
        # Update is_active for existing records based on current date
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            UPDATE leases
            SET is_active = 1
            WHERE date(?) >= date(start_date)
              AND date(?) <= date(expiry_date)
        """, (today, today))
        
        updated_count = cursor.rowcount
        conn.commit()
        print(f"✓ Updated {updated_count} leases as active")
        
        # Create index on is_active for fast filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_leases_is_active 
            ON leases(is_active)
        """)
        
        conn.commit()
        print("✓ Created index on is_active column")
        
        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM leases WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leases WHERE is_active = 0")
        inactive_count = cursor.fetchone()[0]
        
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Active leases: {active_count}")
        print(f"Inactive/Expired leases: {inactive_count}")
        print(f"Total leases: {active_count + inactive_count}")
        
        print("\n✓ Migration 021 completed successfully")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"✗ Migration 021 failed: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
