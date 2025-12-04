"""
Grant Admin role all permissions and assign to admin user
"""
import sqlite3
from pathlib import Path


def setup_admin_permissions():
    """Grant all permissions to Admin role and assign to admin user"""
    
    db_file = Path("database file/WeeklyReportDB.db")
    
    if not db_file.exists():
        print(f"Error: Database file not found: {db_file}")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Get Admin role ID
        cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
        admin_role = cursor.fetchone()
        if not admin_role:
            print("Error: Admin role not found!")
            return
        admin_role_id = admin_role[0]
        print(f"Admin role ID: {admin_role_id}")
        
        # Get all permission IDs
        cursor.execute("SELECT id, name FROM permissions")
        permissions = cursor.fetchall()
        print(f"\nFound {len(permissions)} permissions")
        
        # Grant all permissions to Admin role
        print("\nGranting permissions to Admin role:")
        for perm_id, perm_name in permissions:
            cursor.execute("""
                INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                VALUES (?, ?)
            """, (admin_role_id, perm_id))
            print(f"  ✓ {perm_name}")
        
        conn.commit()
        
        # Verify Admin role permissions
        cursor.execute("""
            SELECT p.name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = ?
        """, (admin_role_id,))
        granted_perms = cursor.fetchall()
        print(f"\nAdmin role now has {len(granted_perms)} permissions")
        
        # Get admin user ID
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            admin_user_id = admin_user[0]
            print(f"\nAdmin user ID: {admin_user_id}")
            
            # Assign Admin role to admin user
            cursor.execute("""
                INSERT OR IGNORE INTO user_roles (user_id, role_id)
                VALUES (?, ?)
            """, (admin_user_id, admin_role_id))
            
            conn.commit()
            
            # Verify admin user roles
            cursor.execute("""
                SELECT r.name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = ?
            """, (admin_user_id,))
            user_roles = cursor.fetchall()
            print(f"\nAdmin user assigned roles:")
            for role in user_roles:
                print(f"  ✓ {role[0]}")
        else:
            print("\nWarning: 'admin' user not found in database!")
        
        print("\n✅ Admin setup complete!")
        
    except Exception as e:
        print(f"\nError: {e}")
        conn.rollback()
    
    finally:
        conn.close()


if __name__ == '__main__':
    setup_admin_permissions()
