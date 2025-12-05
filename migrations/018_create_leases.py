"""
Migration 018: Create leases table
This table tracks active and historical leases for units, including rent and key dates.
"""

import sqlite3
from datetime import datetime

DB_PATH = "database file/WeeklyReportDB.db"

def migrate():
    """Create leases table with tenant, unit, rent, and date tracking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create leases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                unit_id INTEGER NOT NULL,
                rent_pa REAL NOT NULL,
                start_date TEXT NOT NULL,
                break_date TEXT,
                expiry_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                updated_at TEXT,
                updated_by TEXT,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
            )
        """)
        
        # Create index on unit_id for fast lookups of current leases
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_leases_unit_id 
            ON leases(unit_id)
        """)
        
        # Create index on tenant_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_leases_tenant_id 
            ON leases(tenant_id)
        """)
        
        # Create index on expiry_date for finding active leases
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_leases_expiry_date 
            ON leases(expiry_date)
        """)
        
        conn.commit()
        print("✓ Migration 018 completed successfully")
        print("  - Created leases table")
        print("  - Created indexes on unit_id, tenant_id, and expiry_date")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"✗ Migration 018 failed: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
