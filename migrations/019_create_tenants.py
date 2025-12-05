"""
Migration 019: Create tenants table
This table stores tenant information separately from leases, allowing proper relational structure.
"""

import sqlite3
from datetime import datetime

DB_PATH = "database file/WeeklyReportDB.db"

def migrate():
    """Create tenants table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create tenants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_name TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                updated_at TEXT,
                updated_by TEXT
            )
        """)
        
        conn.commit()  # Commit table creation before creating index
        
        # Create index on name for searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tenants_name 
            ON tenants(name)
        """)
        
        conn.commit()  # Commit index creation
        
        # Migrate existing tenant names from units table (if column exists)
        cursor.execute("PRAGMA table_info(units)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrated_count = 0
        if 'tenant_name' in columns:
            cursor.execute("""
                SELECT DISTINCT tenant_name 
                FROM units 
                WHERE tenant_name IS NOT NULL AND tenant_name != ''
            """)
            
            existing_tenants = cursor.fetchall()
            
            now = datetime.now().isoformat()
            for (tenant_name,) in existing_tenants:
                # Check if tenant already exists
                cursor.execute("SELECT id FROM tenants WHERE name = ?", (tenant_name,))
                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO tenants (name, created_at, created_by)
                        VALUES (?, ?, ?)
                    """, (tenant_name, now, 'migration'))
                    migrated_count += 1
            
            # Remove tenant_name column from units table
            # SQLite requires recreating the table to drop a column
            cursor.execute("""
                CREATE TABLE units_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    building_id INTEGER NOT NULL,
                    unit_number TEXT NOT NULL,
                    floor INTEGER,
                    unit_type TEXT DEFAULT 'Office',
                    status TEXT DEFAULT 'Vacant',
                    lease_start DATE,
                    lease_end DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id),
                    UNIQUE(building_id, unit_number)
                )
            """)
            
            cursor.execute("""
                INSERT INTO units_new 
                SELECT id, building_id, unit_number, floor, unit_type, status, 
                       lease_start, lease_end, notes, created_at, created_by, 
                       updated_at, updated_by
                FROM units
            """)
            
            cursor.execute("DROP TABLE units")
            cursor.execute("ALTER TABLE units_new RENAME TO units")
            
            # Recreate indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_units_building_id 
                ON units(building_id)
            """)
        
        conn.commit()
        print("✓ Migration 019 completed successfully")
        print("  - Created tenants table")
        print("  - Created index on name")
        print(f"  - Migrated {migrated_count} unique tenant names from units table")
        if 'tenant_name' in columns:
            print("  - Removed tenant_name column from units table")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"✗ Migration 019 failed: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
