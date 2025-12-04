"""
Migration 009: Replace units.notes with units.bank_schedule_date
Links each unit to the specific Bank Schedule version it was imported from
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Replace notes field with bank_schedule_date"""
    db_path = get_db_path()
    
    print(f"Applying migration 009: Replace notes with bank_schedule_date...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\nℹ️  SQLite doesn't support DROP COLUMN or ALTER COLUMN")
        print("   Creating new table with corrected schema...\n")
        
        # Get current table schema (without notes, with bank_schedule_date)
        print("1. Creating new units_new table...")
        cursor.execute("""
            CREATE TABLE units_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                unit_name TEXT NOT NULL,
                sq_ft REAL NOT NULL,
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
        
        # Copy data (excluding notes)
        print("\n2. Copying data from units to units_new...")
        cursor.execute("""
            INSERT INTO units_new (
                id, building_id, unit_name, sq_ft, unit_type_id,
                created_at, created_by, updated_at, updated_by,
                effective_from, effective_to, is_current,
                lifecycle_status, parent_unit_id, superseded_by
            )
            SELECT 
                id, building_id, unit_name, sq_ft, unit_type_id,
                created_at, created_by, updated_at, updated_by,
                effective_from, effective_to, is_current,
                lifecycle_status, parent_unit_id, superseded_by
            FROM units
        """)
        rows_copied = cursor.rowcount
        print(f"   ✓ Copied {rows_copied} rows")
        
        # Drop old table
        print("\n3. Dropping old units table...")
        cursor.execute("DROP TABLE units")
        print("   ✓ Dropped old units table")
        
        # Rename new table
        print("\n4. Renaming units_new to units...")
        cursor.execute("ALTER TABLE units_new RENAME TO units")
        print("   ✓ Renamed table")
        
        # Recreate indexes
        print("\n5. Recreating indexes...")
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
        print("   ✓ Created idx_units_bank_schedule (NEW)")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 009 completed successfully")
        print("="*80)
        
        print("\nChanges:")
        print("  ✗ Removed: units.notes field")
        print("  ✓ Added: units.bank_schedule_date (DATE)")
        print("  ✓ Added: idx_units_bank_schedule index")
        
        print(f"\n{rows_copied} units migrated successfully")
        print("⚠️  Old 'notes' data has been discarded as requested")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error applying migration: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def rollback_migration():
    """Rollback by recreating original schema"""
    db_path = get_db_path()
    
    print(f"Rolling back migration 009...")
    print("⚠️  This will restore the 'notes' field but data will be lost")
    print("⚠️  This operation requires manually recreating the table")
    print("\nRollback not implemented - please restore from backup if needed")
    
    return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        # Confirm before running
        print("="*80)
        print("⚠️  WARNING: This will DROP and recreate the units table")
        print("⚠️  All 'notes' data will be permanently lost")
        print("="*80)
        response = input("\nType 'yes' to continue: ")
        
        if response.lower() == 'yes':
            apply_migration()
        else:
            print("Migration cancelled")
