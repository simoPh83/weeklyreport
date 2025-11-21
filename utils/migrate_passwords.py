"""
Migration utility to set default passwords for existing users
Run this once to add passwords to users that don't have them
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager

DEFAULT_PASSWORD = "password123"  # Change this to your preferred default


def migrate_passwords(db_path: str, default_password: str = DEFAULT_PASSWORD):
    """Set default passwords for all users without passwords"""
    db_manager = DatabaseManager(db_path)
    
    users = db_manager.get_all_users()
    migrated_count = 0
    
    for user in users:
        # Check if user has no password
        if not user.get('password_hash'):
            print(f"Setting password for user: {user['username']} ({user['display_name']})")
            db_manager.set_user_password(user['id'], default_password)
            migrated_count += 1
        else:
            print(f"User {user['username']} already has a password, skipping...")
    
    print(f"\nMigration complete: {migrated_count} users updated")
    return migrated_count


if __name__ == "__main__":
    # Get database path from command line or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = str(Path(__file__).parent.parent / 'weekly_report.db')
    
    print(f"Migrating passwords in database: {db_path}")
    print(f"Default password: {DEFAULT_PASSWORD}")
    print()
    
    migrate_passwords(db_path, DEFAULT_PASSWORD)
    
    print(f"\nIMPORTANT: All migrated users can now log in with password: {DEFAULT_PASSWORD}")
    print("Please ask users to change their passwords after first login.")
