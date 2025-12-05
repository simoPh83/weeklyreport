"""
Migration 020: Add bank_schedule_date to leases table
This field tracks which bank schedule snapshot the lease data came from.
"""

import sqlite3

DB_PATH = "database file/WeeklyReportDB.db"

def migrate():
    """Add bank_schedule_date column to leases table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add bank_schedule_date column
        cursor.execute("""
            ALTER TABLE leases
            ADD COLUMN bank_schedule_date DATE
        """)
        
        conn.commit()
        print("✓ Migration 020 completed successfully")
        print("  - Added bank_schedule_date column to leases table")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"✗ Migration 020 failed: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
