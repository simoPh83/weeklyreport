"""
Verify letting_progress permissions setup
"""
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path"""
    return Path(__file__).parent.parent / "database file" / "WeeklyReportDB.db"


def verify_permissions():
    """Verify letting progress permissions exist and check role assignments"""
    db_path = get_db_path()
    
    print("="*80)
    print("LETTING PROGRESS PERMISSIONS VERIFICATION")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Check if permissions exist
    print("\n1. Checking permissions existence...")
    cursor.execute("""
        SELECT id, name, description
        FROM permissions
        WHERE name IN ('read_letting_progress', 'write_letting_progress')
        ORDER BY name
    """)
    permissions = cursor.fetchall()
    
    if len(permissions) == 2:
        print("   ✓ Both permissions exist:")
        for perm in permissions:
            print(f"     - {perm['name']}: {perm['description']}")
    else:
        print(f"   ⚠️  Expected 2 permissions, found {len(permissions)}")
    
    # 2. Check role assignments
    print("\n2. Checking role assignments...")
    cursor.execute("""
        SELECT r.name as role_name, p.name as permission_name
        FROM role_permissions rp
        JOIN roles r ON rp.role_id = r.id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE p.name IN ('read_letting_progress', 'write_letting_progress')
        ORDER BY r.name, p.name
    """)
    role_perms = cursor.fetchall()
    
    if role_perms:
        print(f"   Found {len(role_perms)} role-permission assignments:")
        for rp in role_perms:
            print(f"     - {rp['role_name']}: {rp['permission_name']}")
    else:
        print("   ⚠️  No roles have been assigned letting_progress permissions yet")
        print("\n   To assign permissions:")
        print("   1. Log in as admin")
        print("   2. Go to 'User Permissions' tab")
        print("   3. Check the boxes for desired roles")
        print("   4. Click 'Set Role Permissions'")
    
    # 3. Check which users have access
    print("\n3. Checking user access...")
    cursor.execute("""
        SELECT DISTINCT u.username, u.display_name, p.name as permission_name
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE p.name IN ('read_letting_progress', 'write_letting_progress')
        ORDER BY u.username, p.name
    """)
    user_perms = cursor.fetchall()
    
    if user_perms:
        print(f"   Users with access:")
        current_user = None
        for up in user_perms:
            if up['username'] != current_user:
                current_user = up['username']
                print(f"\n     {up['display_name']} ({up['username']}):")
            print(f"       - {up['permission_name']}")
    else:
        print("   ⚠️  No users have letting_progress permissions yet")
    
    # 4. Check admin users (check via admin role instead of is_admin column)
    print("\n4. Admins (automatic access to all features)...")
    cursor.execute("""
        SELECT DISTINCT u.username, u.display_name
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'Admin'
    """)
    admins = cursor.fetchall()
    
    if admins:
        for admin in admins:
            print(f"   - {admin['display_name']} ({admin['username']})")
    else:
        print("   No admin users found")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✓ VERIFICATION COMPLETE")
    print("="*80)
    print("\nThe Letting Progress tab will be:")
    print("  - VISIBLE if user has 'read_letting_progress' permission or is admin")
    print("  - EDITABLE if user has 'write_letting_progress' permission or is admin")


if __name__ == "__main__":
    verify_permissions()
