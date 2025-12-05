"""
Migration 010: Create unit_square_footage table with temporal tracking
Migrates existing units.sq_ft data and drops the column from units table
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Create unit_square_footage table and migrate data"""
    db_path = get_db_path()
    
    print(f"Applying migration 010: Create unit_square_footage table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create unit_square_footage table
        print("\n1. Creating unit_square_footage table...")
        cursor.execute("""
            CREATE TABLE unit_square_footage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_id INTEGER NOT NULL,
                sq_ft REAL NOT NULL,
                effective_from DATE NOT NULL,
                effective_to DATE DEFAULT NULL,
                is_current BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created unit_square_footage table")
        
        # 2. Create indexes
        print("\n2. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_unit_sqft_temporal 
            ON unit_square_footage(unit_id, effective_from, effective_to)
        """)
        print("   ✓ Created idx_unit_sqft_temporal")
        
        cursor.execute("""
            CREATE INDEX idx_unit_sqft_current 
            ON unit_square_footage(unit_id, is_current)
        """)
        print("   ✓ Created idx_unit_sqft_current")
        
        # 3. Migrate existing data from units.sq_ft
        print("\n3. Migrating existing sq_ft data from units table...")
        cursor.execute("""
            INSERT INTO unit_square_footage (
                unit_id, sq_ft, effective_from, effective_to, is_current, created_at
            )
            SELECT 
                id, 
                sq_ft, 
                '2020-01-01',
                NULL,
                1,
                CURRENT_TIMESTAMP
            FROM units
            WHERE sq_ft IS NOT NULL
        """)
        rows_migrated = cursor.rowcount
        print(f"   ✓ Migrated {rows_migrated} rows")
        
        # 4. Drop sq_ft column from units table
        print("\n4. Dropping sq_ft column from units table...")
        print("   ℹ️  SQLite doesn't support DROP COLUMN directly")
        print("   Creating new units table without sq_ft...")
        
        # Get current units schema (without sq_ft)
        cursor.execute("""
            CREATE TABLE units_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                unit_name TEXT NOT NULL,
                unit_type_id INTEGER NOT NULL,
                bank_schedule_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                effective_from DATE NOT NULL DEFAULT '2020-01-01',
                effective_to DATE DEFAULT NULL,
                is_current BOOLEAN DEFAULT 1,
                lifecycle_status TEXT DEFAULT 'active',
                parent_unit_id INTEGER DEFAULT NULL,
                superseded_by TEXT DEFAULT NULL,
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (unit_type_id) REFERENCES unit_types(id),
                FOREIGN KEY (parent_unit_id) REFERENCES units_new(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created units_new table")
        
        # Copy data (excluding sq_ft)
        print("\n5. Copying data to units_new...")
        cursor.execute("""
            INSERT INTO units_new (
                id, building_id, unit_name, unit_type_id, bank_schedule_date,
                created_at, created_by, updated_at, updated_by,
                effective_from, effective_to, is_current,
                lifecycle_status, parent_unit_id, superseded_by
            )
            SELECT 
                id, building_id, unit_name, unit_type_id, bank_schedule_date,
                created_at, created_by, updated_at, updated_by,
                effective_from, effective_to, is_current,
                lifecycle_status, parent_unit_id, superseded_by
            FROM units
        """)
        rows_copied = cursor.rowcount
        print(f"   ✓ Copied {rows_copied} rows")
        
        # Drop old units table
        print("\n6. Dropping old units table...")
        cursor.execute("DROP TABLE units")
        print("   ✓ Dropped old units table")
        
        # Rename new table
        print("\n7. Renaming units_new to units...")
        cursor.execute("ALTER TABLE units_new RENAME TO units")
        print("   ✓ Renamed table")
        
        # Recreate indexes on units table
        print("\n8. Recreating indexes on units table...")
        cursor.execute("""
            CREATE INDEX idx_units_temporal 
            ON units(building_id, effective_from, effective_to)
        """)
        print("   ✓ Created idx_units_temporal")
        
        cursor.execute("""
            CREATE INDEX idx_units_current 
            ON units(building_id, is_current)
        """)
        print("   ✓ Created idx_units_current")
        
        cursor.execute("""
            CREATE INDEX idx_units_parent 
            ON units(parent_unit_id)
        """)
        print("   ✓ Created idx_units_parent")
        
        cursor.execute("""
            CREATE INDEX idx_units_bank_schedule 
            ON units(bank_schedule_date)
        """)
        print("   ✓ Created idx_units_bank_schedule")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 010 completed successfully")
        print("="*80)
        
        print("\nChanges:")
        print(f"  ✓ Created unit_square_footage table with {rows_migrated} records")
        print("  ✓ Created temporal indexes for efficient queries")
        print("  ✗ Removed units.sq_ft column")
        print("\nNote: Use unit_square_footage with is_current=1 to get current sq_ft")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error applying migration: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    apply_migration()
