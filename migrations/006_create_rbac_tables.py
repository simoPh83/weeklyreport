"""
Migration: Create RBAC (Role-Based Access Control) tables
Creates roles, permissions, role_permissions, and user_roles tables
"""
import sqlite3
import sys
from pathlib import Path


def run_migration(db_path: str):
    """
    Create RBAC tables: roles, permissions, role_permissions, user_roles
    
    Args:
        db_path: Path to SQLite database
    """
    print(f"This will create RBAC tables in: {db_path}")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled")
        return
    
    print("\nStarting migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create roles table
        print("Creating roles table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                rank INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # Create permissions table
        print("Creating permissions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # Create role_permissions mapping table
        print("Creating role_permissions mapping table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                granted_by INTEGER,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
                FOREIGN KEY (granted_by) REFERENCES users(id)
            )
        """)
        
        # Create user_roles mapping table
        print("Creating user_roles mapping table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_by INTEGER,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users(id)
            )
        """)
        
        # Insert predefined roles
        print("Inserting predefined roles...")
        roles = [
            ('Admin', 'System administrator with full access', 100),
            ('Asset Manager', 'Manages property assets and portfolio', 90),
            ('Accounting', 'Financial and accounting operations', 80),
            ('Leasing Manager', 'Manages leasing operations and approvals', 70),
            ('Agent', 'Leasing agent handling day-to-day operations', 60),
            ('Marketing', 'Marketing and promotional activities', 50),
            ('FM', 'Facilities management operations', 40),
            ('Stakeholder', 'External stakeholder with limited view access', 10)
        ]
        
        for name, description, rank in roles:
            cursor.execute("""
                INSERT INTO roles (name, description, rank)
                VALUES (?, ?, ?)
            """, (name, description, rank))
        
        # Insert predefined permissions
        print("Inserting predefined permissions...")
        permissions = [
            ('read_viewings', 'View property viewings', 'viewings'),
            ('write_viewings', 'Create and edit property viewings', 'viewings'),
            ('read_letting_progress', 'View letting progress reports', 'letting'),
            ('write_letting_progress', 'Update letting progress', 'letting'),
            ('view_lease_terms', 'View lease terms and agreements', 'leasing')
        ]
        
        for name, description, category in permissions:
            cursor.execute("""
                INSERT INTO permissions (name, description, category)
                VALUES (?, ?, ?)
            """, (name, description, category))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        print("Migration completed successfully!")
        
        # Show created tables
        print("\nRoles table schema:")
        cursor.execute("PRAGMA table_info(roles)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
        
        print("\nPermissions table schema:")
        cursor.execute("PRAGMA table_info(permissions)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
        
        print("\nRole-Permissions mapping table schema:")
        cursor.execute("PRAGMA table_info(role_permissions)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
        
        print("\nUser-Roles mapping table schema:")
        cursor.execute("PRAGMA table_info(user_roles)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
        
        # Show inserted data
        print("\nInserted roles:")
        cursor.execute("SELECT id, name, rank FROM roles ORDER BY rank DESC")
        for row in cursor.fetchall():
            print(f"  [{row[0]}] {row[1]} (rank: {row[2]})")
        
        print("\nInserted permissions:")
        cursor.execute("SELECT id, name, category FROM permissions ORDER BY category, name")
        for row in cursor.fetchall():
            print(f"  [{row[0]}] {row[1]} ({row[2]})")
    
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"\nError during migration: {e}")
        raise
    
    finally:
        conn.close()


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python 006_create_rbac_tables.py <database_path>")
        return 1
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return 1
    
    run_migration(db_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
