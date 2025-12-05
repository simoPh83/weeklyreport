"""
Migration 015: Create offers table
Tracks multiple offers per letting_progress record
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def apply_migration():
    """Create offers table"""
    db_path = get_db_path()
    
    print(f"Applying migration 015: Create offers table...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create offers table
        print("\n1. Creating offers table...")
        cursor.execute("""
            CREATE TABLE offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                letting_progress_id INTEGER NOT NULL,
                offer_date DATE NOT NULL,
                rent_psf REAL,
                lease_terms TEXT,
                status TEXT NOT NULL CHECK(status IN (
                    'pending', 
                    'accepted', 
                    'rejected'
                )) DEFAULT 'pending',
                is_current BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (letting_progress_id) REFERENCES letting_progress(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        print("   ✓ Created offers table")
        
        # 2. Create indexes
        print("\n2. Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_offers_letting 
            ON offers(letting_progress_id)
        """)
        print("   ✓ Created idx_offers_letting")
        
        cursor.execute("""
            CREATE INDEX idx_offers_status 
            ON offers(status, is_current)
        """)
        print("   ✓ Created idx_offers_status")
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✓ Migration 015 completed successfully")
        print("="*80)
        
        print("\nTable structure:")
        print("  - id: Primary key")
        print("  - letting_progress_id: Links to specific letting cycle")
        print("  - offer_date: When offer was made")
        print("  - rent_psf: Offered rent per square foot")
        print("  - lease_terms: Proposed lease terms (text)")
        print("  - status: pending/accepted/rejected")
        print("  - is_current: Flag for latest offer in this letting")
        print("  - notes: Additional comments")
        
        print("\nUsage:")
        print("  - Multiple offers can exist per letting_progress")
        print("  - Only one offer should have is_current=1 at a time")
        print("  - Status tracks whether offer was accepted/rejected")
        print("  - rent_psf × sq_ft = total annual rent (calculated)")
        
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
