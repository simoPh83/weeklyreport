"""
Migration 008: Add temporal tracking to units table
Enables tracking of unit splits, merges, and reconfigurations over time
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Add temporal and lifecycle fields to units table"""
    db_path = get_db_path()
    
    print(f"Applying migration 008: Add temporal tracking to units...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("\n1. Adding temporal tracking fields to units table...")
        
        # Add effective_from (when this unit configuration started)
        cursor.execute("""
            ALTER TABLE units 
            ADD COLUMN effective_from DATE NOT NULL DEFAULT '2020-01-01'
        """)
        print("   ✓ Added effective_from")
        
        # Add effective_to (when this unit configuration ended, NULL = still current)
        cursor.execute("""
            ALTER TABLE units 
            ADD COLUMN effective_to DATE DEFAULT NULL
        """)
        print("   ✓ Added effective_to")
        
        # Add is_current (quick filter for active units)
        cursor.execute("""
            ALTER TABLE units 
            ADD COLUMN is_current BOOLEAN DEFAULT 1
        """)
        print("   ✓ Added is_current")
        
        print("\n2. Adding lifecycle tracking fields...")
        
        # Add lifecycle_status (track what happened to this unit)
        cursor.execute("""
            ALTER TABLE units 
            ADD COLUMN lifecycle_status TEXT DEFAULT 'active'
        """)
        print("   ✓ Added lifecycle_status (active/split/merged/reconfigured)")
        
        # Add parent_unit_id (link to unit this was split from)
        cursor.execute("""
            ALTER TABLE units 
            ADD COLUMN parent_unit_id INTEGER DEFAULT NULL
        """)
        print("   ✓ Added parent_unit_id")
        
        # Add superseded_by (JSON array of unit IDs that replaced this one)
        cursor.execute("""
            ALTER TABLE units 
            ADD COLUMN superseded_by TEXT DEFAULT NULL
        """)
        print("   ✓ Added superseded_by (JSON format)")
        
        print("\n3. Creating indexes for temporal queries...")
        
        # Critical index for "units that existed during date range" queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_units_temporal 
            ON units(building_id, effective_from, effective_to)
        """)
        print("   ✓ Created idx_units_temporal (building_id, effective_from, effective_to)")
        
        # Critical index for "current units only" queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_units_current 
            ON units(building_id, is_current)
        """)
        print("   ✓ Created idx_units_current (building_id, is_current)")
        
        # Optional but useful: index for finding children of a parent unit
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_units_parent 
            ON units(parent_unit_id)
        """)
        print("   ✓ Created idx_units_parent (for tracing splits)")
        
        print("\n4. Creating unit_relationships table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unit_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_unit_id INTEGER NOT NULL,
                to_unit_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                effective_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (from_unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (to_unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created unit_relationships table")
        
        # Index for finding what a unit became
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unit_rel_from 
            ON unit_relationships(from_unit_id, effective_date)
        """)
        print("   ✓ Created idx_unit_rel_from (for lineage queries)")
        
        # Index for finding where a unit came from
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unit_rel_to 
            ON unit_relationships(to_unit_id, effective_date)
        """)
        print("   ✓ Created idx_unit_rel_to (for ancestry queries)")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 008 completed successfully")
        print("="*80)
        
        # Show summary
        print("\nNew fields added to units table:")
        print("  - effective_from: When this configuration started")
        print("  - effective_to: When this configuration ended (NULL = current)")
        print("  - is_current: Quick filter for active units")
        print("  - lifecycle_status: active/split/merged/reconfigured")
        print("  - parent_unit_id: Link to parent if this was split from another")
        print("  - superseded_by: JSON array of units that replaced this one")
        
        print("\nNew table created:")
        print("  - unit_relationships: Tracks splits, merges, reconfigurations")
        
        print("\nIndexes created:")
        print("  - idx_units_temporal: Fast temporal queries")
        print("  - idx_units_current: Fast current-units-only queries")
        print("  - idx_units_parent: Fast parent-child lookups")
        print("  - idx_unit_rel_from: Fast lineage tracing")
        print("  - idx_unit_rel_to: Fast ancestry tracing")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error applying migration: {e}")
        return False
    finally:
        if conn:
            conn.close()


def rollback_migration():
    """Rollback the temporal tracking migration"""
    db_path = get_db_path()
    
    print(f"Rolling back migration 008...")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n⚠️  WARNING: SQLite doesn't support DROP COLUMN")
        print("To fully rollback, you would need to:")
        print("  1. Create new units table without temporal fields")
        print("  2. Copy data")
        print("  3. Drop old table")
        print("  4. Rename new table")
        print("\nFor now, just dropping the relationships table and indexes...")
        
        cursor.execute("DROP INDEX IF EXISTS idx_units_temporal")
        cursor.execute("DROP INDEX IF EXISTS idx_units_current")
        cursor.execute("DROP INDEX IF EXISTS idx_units_parent")
        cursor.execute("DROP INDEX IF EXISTS idx_unit_rel_from")
        cursor.execute("DROP INDEX IF EXISTS idx_unit_rel_to")
        cursor.execute("DROP TABLE IF EXISTS unit_relationships")
        
        conn.commit()
        print("✓ Indexes and unit_relationships table dropped")
        print("⚠️  New columns remain in units table (SQLite limitation)")
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error rolling back migration: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        apply_migration()
