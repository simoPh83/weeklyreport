"""
Database Manager for Property Management System
Handles all database operations, schema initialization, and queries
"""
import sqlite3
import bcrypt
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import threading


class DatabaseWriteError(Exception):
    """Raised when write operation fails due to lack of write lock"""
    pass


class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str):
        if not hasattr(self, 'initialized'):
            self.db_path = db_path
            self.initialized = True
            self.lock_manager = None  # Will be set by main.py
            self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    password_hash TEXT,
                    email TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Buildings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS buildings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    total_units INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id)
                )
            """)
            
            # Units table (Commercial properties: offices and retail)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    building_id INTEGER NOT NULL,
                    unit_number TEXT NOT NULL,
                    floor INTEGER,
                    unit_type TEXT DEFAULT 'Office',  -- 'Office' or 'Retail'
                    square_feet REAL,
                    rent_amount REAL,
                    status TEXT DEFAULT 'Vacant',
                    tenant_name TEXT,
                    lease_start DATE,
                    lease_end DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id),
                    UNIQUE(building_id, unit_number)
                )
            """)
            
            # Sessions table (database-based locking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_write_lock INTEGER DEFAULT 0,
                    machine_name TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create default admin user if no users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO users (username, display_name, is_admin)
                    VALUES ('admin', 'Administrator', 1)
                """)
                cursor.execute("""
                    INSERT INTO users (username, display_name, is_admin)
                    VALUES ('user1', 'User One', 0)
                """)
                cursor.execute("""
                    INSERT INTO users (username, display_name, is_admin)
                    VALUES ('user2', 'User Two', 0)
                """)
            
            conn.commit()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def set_lock_manager(self, lock_manager):
        """Set the lock manager instance for write verification"""
        self.lock_manager = lock_manager
    
    def _verify_write_permission(self) -> None:
        """
        Verify write lock before any write operation.
        Raises DatabaseWriteError if no valid write lock.
        This is the centralized lock verification point.
        """
        if self.lock_manager is None:
            # During initialization, lock_manager may not be set yet
            return
        
        if not self.lock_manager.verify_write_lock():
            raise DatabaseWriteError(
                "Write operation denied: You no longer have write access to the database. "
                "Your write lock has been removed (possibly by an administrator)."
            )
    
    # User management
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin
                FROM users
                WHERE is_active = 1
                ORDER BY display_name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin
                FROM users
                WHERE id = ? AND is_active = 1
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin
                FROM users
                WHERE username = ? AND is_active = 1
            """, (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username and password
        Returns user dict if authentication successful, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, is_admin, password_hash
                FROM users
                WHERE username = ? AND is_active = 1
            """, (username,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            user = dict(row)
            password_hash = user.pop('password_hash', None)
            
            # If no password hash, allow login (backward compatibility)
            if not password_hash:
                return user
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return user
            
            return None
    
    def set_user_password(self, user_id: int, password: str) -> bool:
        """
        Set or update user password
        """
        # Hash password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET password_hash = ?
                    WHERE id = ?
                """, (password_hash.decode('utf-8'), user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error setting password: {e}")
            return False
    
    def create_user(self, username: str, display_name: str, password: str, 
                    is_admin: bool = False, email: Optional[str] = None) -> int:
        """
        Create new user with password
        Returns user ID
        """
        # Hash password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, display_name, password_hash, email, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, (username, display_name, password_hash.decode('utf-8'), email, 1 if is_admin else 0))
            conn.commit()
            return cursor.lastrowid
    
    # Buildings CRUD
    def get_all_buildings(self) -> List[Dict[str, Any]]:
        """Get all buildings with occupancy percentage (legacy method)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    b.*,
                    u.display_name as created_by_name,
                    0.0 as occupancy
                FROM buildings b
                LEFT JOIN users u ON b.created_by = u.id
                ORDER BY b.property_code
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_current_buildings(self) -> List[Dict[str, Any]]:
        """Get all buildings with most recent capital valuation and occupancy percentage"""
        from datetime import datetime
        import time
        
        start_time = time.time()
        print(f"DEBUG: Starting get_all_current_buildings at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
        current_year = datetime.now().year
        min_year = 2000  # Safety limit
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, get all buildings
            query_start = time.time()
            cursor.execute("""
                SELECT 
                    b.*,
                    u.display_name as created_by_name,
                    0.0 as occupancy
                FROM buildings b
                LEFT JOIN users u ON b.created_by = u.id
                ORDER BY b.property_code
            """)
            buildings = [dict(row) for row in cursor.fetchall()]
            query_time = time.time() - query_start
            print(f"DEBUG: Fetched {len(buildings)} buildings in {query_time:.3f}s")
            
            # OPTIMIZED: Get all latest valuations in a single query using subquery
            valuation_start = time.time()
            cursor.execute("""
                SELECT 
                    cv.building_id,
                    cv.valuation_year,
                    cv.valuation_amount
                FROM capital_valuations cv
                INNER JOIN (
                    SELECT building_id, MAX(valuation_year) as max_year
                    FROM capital_valuations
                    WHERE valuation_year BETWEEN ? AND ?
                    GROUP BY building_id
                ) latest ON cv.building_id = latest.building_id 
                    AND cv.valuation_year = latest.max_year
            """, (min_year, current_year))
            
            # Create a lookup dictionary for quick access
            valuations_map = {}
            for row in cursor.fetchall():
                valuations_map[row['building_id']] = {
                    'latest_valuation_year': row['valuation_year'],
                    'latest_valuation_amount': row['valuation_amount']
                }
            
            valuation_time = time.time() - valuation_start
            print(f"DEBUG: Fetched valuations in {valuation_time:.3f}s (1 optimized query)")
            
            # Merge valuations into buildings
            merge_start = time.time()
            missing_count = 0
            for building in buildings:
                building_id = building['id']
                if building_id in valuations_map:
                    building.update(valuations_map[building_id])
                else:
                    missing_count += 1
                    print(f"DEBUG: No capital valuation found for building ID {building_id} "
                          f"(property_code: {building.get('property_code', 'N/A')}, "
                          f"property_name: {building.get('property_name', 'N/A')}) "
                          f"between years {min_year} and {current_year}")
                    building['latest_valuation_year'] = None
                    building['latest_valuation_amount'] = None
            
            merge_time = time.time() - merge_start
            print(f"DEBUG: Merged data in {merge_time:.3f}s ({missing_count} buildings without valuations)")
            
            total_time = time.time() - start_time
            print(f"DEBUG: Total get_all_current_buildings time: {total_time:.3f}s")
            
            return buildings
    
    def get_building_by_id(self, building_id: int) -> Optional[Dict[str, Any]]:
        """Get building by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, u.display_name as created_by_name
                FROM buildings b
                LEFT JOIN users u ON b.created_by = u.id
                WHERE b.id = ?
            """, (building_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_building(self, data: Dict[str, Any], user_id: int) -> int:
        """Create a new building"""
        self._verify_write_permission()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO buildings (
                    property_code, property_name, property_address, postcode, 
                    client_code, acquisition_date, disposal_date, notes, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('property_code'),
                data.get('property_name'),
                data.get('property_address'),
                data.get('postcode'),
                data.get('client_code'),
                data.get('acquisition_date'),
                data.get('disposal_date'),
                data.get('notes'),
                user_id
            ))
            building_id = cursor.lastrowid
            
            # Log audit
            self._log_audit(conn, user_id, 'CREATE', 'buildings', building_id, None, str(data))
            
            conn.commit()
            return building_id
    
    def update_building(self, building_id: int, data: Dict[str, Any], user_id: int):
        """Update an existing building"""
        self._verify_write_permission()
        
        old_data = self.get_building_by_id(building_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE buildings
                SET property_code = ?, property_name = ?, property_address = ?, 
                    postcode = ?, client_code = ?, acquisition_date = ?, 
                    disposal_date = ?, notes = ?, 
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (
                data.get('property_code'),
                data.get('property_name'),
                data.get('property_address'),
                data.get('postcode'),
                data.get('client_code'),
                data.get('acquisition_date'),
                data.get('disposal_date'),
                data.get('notes'),
                user_id,
                building_id
            ))
            
            # Log audit
            self._log_audit(conn, user_id, 'UPDATE', 'buildings', building_id, str(old_data), str(data))
            
            conn.commit()
    
    def delete_building(self, building_id: int, user_id: int):
        """Delete a building"""
        self._verify_write_permission()
        
        old_data = self.get_building_by_id(building_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM buildings WHERE id = ?", (building_id,))
            
            # Log audit
            self._log_audit(conn, user_id, 'DELETE', 'buildings', building_id, str(old_data), None)
            
            conn.commit()
    
    # Units CRUD
    def get_units_by_building(self, building_id: int) -> List[Dict[str, Any]]:
        """Get all units for a building"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, b.property_name as building_name, ut.description as unit_type_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                WHERE u.building_id = ?
                ORDER BY u.unit_name
            """, (building_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_units(self) -> List[Dict[str, Any]]:
        """Get all units"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, b.property_name as building_name, ut.description as unit_type_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                ORDER BY b.property_code, u.unit_name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unit_by_id(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """Get unit by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, b.property_name as building_name, ut.description as unit_type_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                WHERE u.id = ?
            """, (unit_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_unit(self, data: Dict[str, Any], user_id: int) -> int:
        """Create a new unit"""
        self._verify_write_permission()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO units (
                    building_id, unit_name, sq_ft, unit_type_id, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get('building_id'),
                data.get('unit_name'),
                data.get('sq_ft'),
                data.get('unit_type_id'),
                data.get('notes'),
                user_id
            ))
            unit_id = cursor.lastrowid
            
            # Log audit
            self._log_audit(conn, user_id, 'CREATE', 'units', unit_id, None, str(data))
            
            conn.commit()
            return unit_id
    
    def update_unit(self, unit_id: int, data: Dict[str, Any], user_id: int):
        """Update an existing unit"""
        self._verify_write_permission()
        
        old_data = self.get_unit_by_id(unit_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE units
                SET building_id = ?, unit_name = ?, sq_ft = ?, unit_type_id = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (
                data.get('building_id'),
                data.get('unit_name'),
                data.get('sq_ft'),
                data.get('unit_type_id'),
                data.get('floor'),
                data.get('unit_type', 'Office'),
                data.get('square_feet'),
                data.get('rent_amount'),
                data.get('status', 'Vacant'),
                data.get('tenant_name'),
                data.get('lease_start'),
                data.get('sq_ft'),
                data.get('unit_type_id'),
                data.get('notes'),
                user_id,
                unit_id
            ))
            
            # Log audit
            self._log_audit(conn, user_id, 'UPDATE', 'units', unit_id, str(old_data), str(data))
            
            conn.commit()
    
    def delete_unit(self, unit_id: int, user_id: int):
        """Delete a unit"""
        self._verify_write_permission()
        
        old_data = self.get_unit_by_id(unit_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM units WHERE id = ?", (unit_id,))
            
            # Log audit
            self._log_audit(conn, user_id, 'DELETE', 'units', unit_id, str(old_data), None)
            
            conn.commit()
    
    # Audit logging
    def _log_audit(self, conn: sqlite3.Connection, user_id: int, action: str,
                   table_name: str, record_id: Optional[int],
                   old_values: Optional[str], new_values: Optional[str]):
        """Log an audit entry"""
        user = self.get_user_by_id(user_id)
        username = user['username'] if user else 'unknown'
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (user_id, username, action, table_name, record_id, old_values, new_values)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, action, table_name, record_id, old_values, new_values))
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # RBAC - Roles and Permissions Management
    def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description, rank
                FROM roles
                ORDER BY rank DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_permissions(self) -> List[Dict[str, Any]]:
        """Get all permissions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description, category
                FROM permissions
                ORDER BY category, name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_role_permissions(self) -> List[Dict[str, Any]]:
        """Get all role-permission mappings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    r.id as role_id,
                    r.name as role_name,
                    p.id as permission_id,
                    p.name as permission_name
                FROM role_permissions rp
                JOIN roles r ON rp.role_id = r.id
                JOIN permissions p ON rp.permission_id = p.id
                ORDER BY r.rank DESC, p.category, p.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def grant_role_permission(self, role_id: int, permission_id: int, user_id: int) -> bool:
        """Grant a permission to a role"""
        self._verify_write_permission()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id, granted_by)
                    VALUES (?, ?, ?)
                """, (role_id, permission_id, user_id))
                
                # Log audit
                self._log_audit(conn, user_id, 'GRANT_PERMISSION', 'role_permissions', 
                              None, None, f"role_id={role_id}, permission_id={permission_id}")
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error granting permission: {e}")
            return False
    
    def revoke_role_permission(self, role_id: int, permission_id: int, user_id: int) -> bool:
        """Revoke a permission from a role"""
        self._verify_write_permission()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM role_permissions
                    WHERE role_id = ? AND permission_id = ?
                """, (role_id, permission_id))
                
                # Log audit
                self._log_audit(conn, user_id, 'REVOKE_PERMISSION', 'role_permissions',
                              None, f"role_id={role_id}, permission_id={permission_id}", None)
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error revoking permission: {e}")
            return False
    
    def get_user_roles(self) -> List[Dict[str, Any]]:
        """Get all user-role assignments"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    u.id as user_id,
                    u.username,
                    u.display_name,
                    r.id as role_id,
                    r.name as role_name
                FROM user_roles ur
                JOIN users u ON ur.user_id = u.id
                JOIN roles r ON ur.role_id = r.id
                WHERE u.is_active = 1
                ORDER BY u.display_name, r.rank DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def assign_user_role(self, user_id: int, role_id: int, assigned_by: int) -> bool:
        """Assign a role to a user"""
        self._verify_write_permission()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO user_roles (user_id, role_id, assigned_by)
                    VALUES (?, ?, ?)
                """, (user_id, role_id, assigned_by))
                
                # Log audit
                self._log_audit(conn, assigned_by, 'ASSIGN_ROLE', 'user_roles',
                              None, None, f"user_id={user_id}, role_id={role_id}")
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error assigning role: {e}")
            return False
    
    def unassign_user_role(self, user_id: int, role_id: int, unassigned_by: int) -> bool:
        """Unassign a role from a user"""
        self._verify_write_permission()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM user_roles
                    WHERE user_id = ? AND role_id = ?
                """, (user_id, role_id))
                
                # Log audit
                self._log_audit(conn, unassigned_by, 'UNASSIGN_ROLE', 'user_roles',
                              None, f"user_id={user_id}, role_id={role_id}", None)
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error unassigning role: {e}")
            return False
