"""
Migration 024: Add bank_schedule_imports tracking system

This migration implements the infrastructure to track which monthly bank schedule
spreadsheet the current data originated from, and whether modifications have been
made after import.

Creates:
- bank_schedule_imports table: Tracks each monthly spreadsheet import
- Adds import_id to leases table
- Adds import_id to unit_history table
- Creates initial import record for existing data (June 2025)

This enables:
- Showing import filename in GUI title
- [PLUS] indicator for post-import modifications
- Foundation for historical import tracking
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / "database file" / "WeeklyReportDB.db"


def run_migration():
    """Execute migration 024"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*80)
        print("MIGRATION 024: Add bank_schedule_imports tracking system")
        print("="*80)
        
        # Get counts before migration
        cursor.execute("SELECT COUNT(*) FROM leases")
        leases_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM unit_history")
        unit_history_before = cursor.fetchone()[0]
        
        print(f"\nBefore migration:")
        print(f"  Leases: {leases_before}")
        print(f"  Unit history records: {unit_history_before}")
        
        # Step 1: Create bank_schedule_imports table
        print("\n[1/5] Creating bank_schedule_imports table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bank_schedule_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_filename TEXT NOT NULL,
                schedule_date DATE NOT NULL,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_current INTEGER DEFAULT 0,
                imported_by TEXT,
                notes TEXT,
                units_imported INTEGER DEFAULT 0,
                leases_imported INTEGER DEFAULT 0,
                sq_footage_records INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(schedule_filename, schedule_date)
            )
        """)
        print("   ✓ bank_schedule_imports table created")
        
        # Step 2: Add import_id to leases table
        print("\n[2/5] Adding import_id to leases table...")
        try:
            cursor.execute("ALTER TABLE leases ADD COLUMN import_id INTEGER REFERENCES bank_schedule_imports(id)")
            print("   ✓ import_id column added to leases")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ℹ import_id column already exists in leases")
            else:
                raise
        
        # Step 3: Add import_id to unit_history table
        print("\n[3/5] Adding import_id to unit_history table...")
        try:
            cursor.execute("ALTER TABLE unit_history ADD COLUMN import_id INTEGER REFERENCES bank_schedule_imports(id)")
            print("   ✓ import_id column added to unit_history")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ℹ import_id column already exists in unit_history")
            else:
                raise
        
        # Step 4: Create initial import record for existing data
        print("\n[4/5] Creating initial import record for existing data...")
        cursor.execute("""
            INSERT INTO bank_schedule_imports (
                schedule_filename,
                schedule_date,
                is_current,
                imported_by,
                notes,
                leases_imported,
                sq_footage_records
            ) VALUES (
                'Leasing Bank Schedule June 2025.xlsx',
                '2025-06-30',
                1,
                'system',
                'Initial import record created during migration 024',
                ?,
                ?
            )
        """, (leases_before, unit_history_before))
        
        initial_import_id = cursor.lastrowid
        print(f"   ✓ Created import record ID {initial_import_id} for June 2025 data")
        
        # Step 5: Link existing records to initial import
        print("\n[5/5] Linking existing records to initial import...")
        
        # Update all existing leases
        cursor.execute("""
            UPDATE leases 
            SET import_id = ? 
            WHERE import_id IS NULL
        """, (initial_import_id,))
        leases_updated = cursor.rowcount
        print(f"   ✓ Linked {leases_updated} leases to initial import")
        
        # Update all existing unit_history records
        cursor.execute("""
            UPDATE unit_history 
            SET import_id = ? 
            WHERE import_id IS NULL
        """, (initial_import_id,))
        unit_history_updated = cursor.rowcount
        print(f"   ✓ Linked {unit_history_updated} unit_history records to initial import")
        
        # Create indexes for performance
        print("\n[6/6] Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bank_schedule_imports_current ON bank_schedule_imports(is_current)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bank_schedule_imports_date ON bank_schedule_imports(schedule_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leases_import_id ON leases(import_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_unit_history_import_id ON unit_history(import_id)")
        print("   ✓ Indexes created")
        
        # Commit transaction
        conn.commit()
        
        # Verify final state
        cursor.execute("SELECT COUNT(*) FROM bank_schedule_imports")
        imports_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leases WHERE import_id IS NOT NULL")
        leases_linked = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM unit_history WHERE import_id IS NOT NULL")
        unit_history_linked = cursor.fetchone()[0]
        
        print("\n" + "="*80)
        print("MIGRATION 024 COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Bank schedule imports: {imports_count}")
        print(f"Leases linked to import: {leases_linked} / {leases_before}")
        print(f"Unit history linked to import: {unit_history_linked} / {unit_history_before}")
        print("\nCurrent import: Leasing Bank Schedule June 2025.xlsx (2025-06-30)")
        print("="*80)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
