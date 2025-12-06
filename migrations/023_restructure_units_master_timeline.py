import sqlite3
import os
from datetime import datetime

def migrate():
    """
    Restructure units to Master + Timeline architecture
    - units: Master registry (current state, simplified)
    - unit_history: Complete timeline (sq_ft + relationships + all changes)
    """
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database file', 'WeeklyReportDB.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        print("="*80)
        print("MIGRATION 023: Restructure Units to Master + Timeline")
        print("="*80)
        
        # Get counts before migration
        cursor.execute("SELECT COUNT(*) as count FROM units")
        units_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM unit_square_footage")
        usf_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM unit_relationships")
        rel_count = cursor.fetchone()['count']
        
        print(f"\nBefore migration:")
        print(f"  units: {units_count}")
        print(f"  unit_square_footage: {usf_count}")
        print(f"  unit_relationships: {rel_count}")
        
        # ===================================================================
        # STEP 1: Create unit_history table
        # ===================================================================
        print("\n[1/6] Creating unit_history table...")
        cursor.execute("""
            CREATE TABLE unit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_id INTEGER NOT NULL,
                
                -- Attributes that can change over time
                unit_name TEXT,
                unit_type_id INTEGER,
                sq_ft REAL,
                
                -- Temporal tracking
                effective_from DATE NOT NULL,
                effective_to DATE,
                is_current BOOLEAN DEFAULT 0,
                
                -- Event tracking
                event_type TEXT,           -- 'created', 'resized', 'split', 'merge', 'renamed', NULL
                related_unit_ids TEXT,     -- JSON array for splits/merges
                notes TEXT,
                
                -- Audit (import_id will be added in next migration)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                
                FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        cursor.execute("CREATE INDEX idx_unit_history_unit_id ON unit_history(unit_id)")
        cursor.execute("CREATE INDEX idx_unit_history_dates ON unit_history(effective_from, effective_to)")
        cursor.execute("CREATE INDEX idx_unit_history_current ON unit_history(is_current)")
        print("  ✓ unit_history table created with indexes")
        
        # ===================================================================
        # STEP 2: Migrate unit_square_footage → unit_history
        # ===================================================================
        print("\n[2/6] Migrating unit_square_footage to unit_history...")
        cursor.execute("""
            INSERT INTO unit_history (
                unit_id, sq_ft, effective_from, effective_to, is_current,
                event_type, created_at, created_by
            )
            SELECT 
                usf.unit_id,
                usf.sq_ft,
                usf.effective_from,
                usf.effective_to,
                usf.is_current,
                CASE 
                    WHEN usf.effective_from = (
                        SELECT MIN(effective_from) 
                        FROM unit_square_footage usf2 
                        WHERE usf2.unit_id = usf.unit_id
                    ) THEN 'created'
                    ELSE 'resized'
                END as event_type,
                usf.created_at,
                usf.created_by
            FROM unit_square_footage usf
            ORDER BY usf.unit_id, usf.effective_from
        """)
        sqft_migrated = cursor.rowcount
        print(f"  ✓ Migrated {sqft_migrated} square footage records")
        
        # ===================================================================
        # STEP 3: Migrate unit_relationships → unit_history
        # ===================================================================
        print("\n[3/6] Migrating unit_relationships to unit_history...")
        
        # Check if there are any relationships
        cursor.execute("SELECT COUNT(*) as count FROM unit_relationships")
        rel_count_check = cursor.fetchone()['count']
        
        if rel_count_check > 0:
            # Migrate splits (from_unit → to_unit)
            cursor.execute("""
                INSERT INTO unit_history (
                    unit_id, event_type, related_unit_ids, 
                    effective_from, notes,
                    created_at, created_by
                )
                SELECT 
                    ur.to_unit_id as unit_id,
                    'split' as event_type,
                    '["' || ur.from_unit_id || '"]' as related_unit_ids,
                    ur.effective_date as effective_from,
                    COALESCE(ur.notes, 'Split from unit ' || ur.from_unit_id) as notes,
                    ur.created_at,
                    ur.created_by
                FROM unit_relationships ur
                WHERE ur.relationship_type = 'split'
            """)
            splits_migrated = cursor.rowcount
            print(f"  ✓ Migrated {splits_migrated} split relationships")
            
            # Migrate merges (from_unit → to_unit)
            cursor.execute("""
                INSERT INTO unit_history (
                    unit_id, event_type, related_unit_ids,
                    effective_from, notes,
                    created_at, created_by
                )
                SELECT 
                    ur.to_unit_id as unit_id,
                    'merge' as event_type,
                    '["' || ur.from_unit_id || '"]' as related_unit_ids,
                    ur.effective_date as effective_from,
                    COALESCE(ur.notes, 'Merged with unit ' || ur.from_unit_id) as notes,
                    ur.created_at,
                    ur.created_by
                FROM unit_relationships ur
                WHERE ur.relationship_type = 'merge'
            """)
            merges_migrated = cursor.rowcount
            print(f"  ✓ Migrated {merges_migrated} merge relationships")
        else:
            splits_migrated = 0
            merges_migrated = 0
            print(f"  ℹ No unit relationships to migrate")
        
        # ===================================================================
        # STEP 4: Create units_new table
        # ===================================================================
        print("\n[4/6] Creating simplified units_new table...")
        cursor.execute("""
            CREATE TABLE units_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                unit_name TEXT NOT NULL,
                unit_type_id INTEGER,
                
                -- Status tracking
                is_current BOOLEAN DEFAULT 1,
                lifecycle_status TEXT DEFAULT 'active',
                
                -- Audit
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                
                FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                FOREIGN KEY (unit_type_id) REFERENCES unit_types(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        print("  ✓ units_new table created")
        
        # ===================================================================
        # STEP 5: Migrate units → units_new
        # ===================================================================
        print("\n[5/6] Migrating units to units_new (master records)...")
        cursor.execute("""
            INSERT INTO units_new (
                id, building_id, unit_name, unit_type_id,
                is_current, lifecycle_status,
                created_at, created_by, updated_at, updated_by
            )
            SELECT 
                u.id,
                u.building_id,
                u.unit_name,
                u.unit_type_id,
                u.is_current,
                COALESCE(u.lifecycle_status, 
                    CASE 
                        WHEN u.is_current = 1 THEN 'active'
                        ELSE 'inactive'
                    END
                ) as lifecycle_status,
                u.created_at,
                u.created_by,
                u.updated_at,
                u.updated_by
            FROM units u
        """)
        units_migrated = cursor.rowcount
        print(f"  ✓ Migrated {units_migrated} unit master records")
        
        # ===================================================================
        # STEP 6: Replace old tables with new
        # ===================================================================
        print("\n[6/6] Replacing old tables...")
        cursor.execute("DROP TABLE unit_relationships")
        print("  ✓ Dropped unit_relationships")
        
        cursor.execute("DROP TABLE unit_square_footage")
        print("  ✓ Dropped unit_square_footage")
        
        cursor.execute("DROP TABLE units")
        print("  ✓ Dropped old units table")
        
        cursor.execute("ALTER TABLE units_new RENAME TO units")
        print("  ✓ Renamed units_new to units")
        
        # Verify final counts
        cursor.execute("SELECT COUNT(*) as count FROM units")
        final_units = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM unit_history")
        final_history = cursor.fetchone()['count']
        
        conn.commit()
        
        print("\n" + "="*80)
        print("MIGRATION 023 COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nFinal state:")
        print(f"  units (master): {final_units}")
        print(f"  unit_history: {final_history}")
        print(f"\nHistory breakdown:")
        print(f"  - Square footage records: {sqft_migrated}")
        print(f"  - Split records: {splits_migrated}")
        print(f"  - Merge records: {merges_migrated}")
        print(f"  - Total: {sqft_migrated + splits_migrated + merges_migrated}")
        print("="*80)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
