"""
Add letting_progress permissions to the database
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def add_letting_permissions():
    """Add read_letting_progress and write_letting_progress permissions"""
    db_path = get_db_path()
    
    print(f"Adding letting_progress permissions...")
    print(f"Database path: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing permissions
        cursor.execute("SELECT name FROM permissions ORDER BY name")
        existing = [row[0] for row in cursor.fetchall()]
        print(f"\nExisting permissions: {', '.join(existing)}")
        
        # Add new permissions
        permissions_to_add = [
            ('read_letting_progress', 'View letting progress data and reports'),
            ('write_letting_progress', 'Create and modify letting progress records')
        ]
        
        print("\nAdding new permissions:")
        for name, description in permissions_to_add:
            if name in existing:
                print(f"  - {name}: Already exists")
            else:
                cursor.execute("""
                    INSERT INTO permissions (name, description)
                    VALUES (?, ?)
                """, (name, description))
                print(f"  ✓ Added: {name}")
        
        conn.commit()
        
        # Show all permissions now
        cursor.execute("SELECT id, name, description FROM permissions ORDER BY name")
        print("\n" + "="*80)
        print("ALL PERMISSIONS:")
        print("="*80)
        for row in cursor.fetchall():
            print(f"{row[0]:3d}. {row[1]:30s} - {row[2]}")
        
        conn.close()
        
        print("\n✓ Permissions setup complete")
        print("\nNext steps:")
        print("  - Assign permissions to roles using the Permissions tab in GUI")
        print("  - Or run SQL: INSERT INTO role_permissions (role_id, permission_id, granted_by)")
        print("                VALUES (1, (SELECT id FROM permissions WHERE name='read_letting_progress'), 1)")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    add_letting_permissions()
