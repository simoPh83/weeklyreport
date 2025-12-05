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
                    unit_type TEXT DEFAULT 'Office',
                    status TEXT DEFAULT 'Vacant',
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
                    INSERT INTO users (username, display_name)
                    VALUES ('admin', 'Administrator')
                """)
                cursor.execute("""
                    INSERT INTO users (username, display_name)
                    VALUES ('user1', 'User One')
                """)
                cursor.execute("""
                    INSERT INTO users (username, display_name)
                    VALUES ('user2', 'User Two')
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
                SELECT id, username, display_name
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
                SELECT id, username, display_name
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
                SELECT id, username, display_name
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
                SELECT id, username, display_name, password_hash
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
                    email: Optional[str] = None) -> int:
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
                INSERT INTO users (username, display_name, password_hash, email)
                VALUES (?, ?, ?, ?)
            """, (username, display_name, password_hash.decode('utf-8'), email))
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
    
    def get_property_snapshot(self, reference_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get complete property snapshot for a specific date.
        Returns hierarchical data with buildings, units, leases, and occupancy %.
        Can be used to populate both buildings tab and units tab.
        
        Args:
            reference_date: Date to query (YYYY-MM-DD format). Defaults to today.
            
        Returns:
            Dictionary with:
            - 'buildings': List of buildings with occupancy stats
            - 'units': List of all units with lease information
        """
        if reference_date is None:
            reference_date = datetime.now().strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get buildings with occupancy calculation
            cursor.execute("""
                SELECT b.id,
                       b.property_code,
                       b.property_name,
                       b.property_address,
                       b.postcode,
                       b.client_code,
                       b.acquisition_date,
                       b.disposal_date,
                       COUNT(DISTINCT u.id) as total_units,
                       COUNT(DISTINCT CASE WHEN l.id IS NOT NULL THEN u.id END) as let_units,
                       ROUND(
                           CAST(COUNT(DISTINCT CASE WHEN l.id IS NOT NULL THEN u.id END) AS REAL) * 100.0 / 
                           NULLIF(COUNT(DISTINCT u.id), 0), 
                           1
                       ) as occupancy_pct,
                       SUM(CASE WHEN l.id IS NOT NULL THEN usf.sq_ft ELSE 0 END) as let_sqft,
                       SUM(usf.sq_ft) as total_sqft,
                       SUM(CASE WHEN l.id IS NOT NULL THEN l.rent_pa ELSE 0 END) as total_rent_pa,
                       cv.valuation_year as latest_valuation_year,
                       cv.valuation_amount as latest_valuation_amount
                FROM buildings b
                LEFT JOIN units u ON b.id = u.building_id AND u.is_current = 1
                LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id 
                    AND (date(?) BETWEEN date(usf.effective_from) AND COALESCE(date(usf.effective_to), '9999-12-31')
                         OR usf.is_current = 1)
                LEFT JOIN leases l ON u.id = l.unit_id 
                    AND date(?) BETWEEN date(l.start_date) AND date(l.expiry_date)
                LEFT JOIN (
                    SELECT building_id, 
                           valuation_year, 
                           valuation_amount,
                           ROW_NUMBER() OVER (PARTITION BY building_id ORDER BY valuation_year DESC) as rn
                    FROM capital_valuations
                ) cv ON b.id = cv.building_id AND cv.rn = 1
                GROUP BY b.id, b.property_code, b.property_name, b.property_address, 
                         b.postcode, b.client_code, b.acquisition_date, b.disposal_date,
                         cv.valuation_year, cv.valuation_amount
                ORDER BY b.property_name
            """, (reference_date, reference_date))
            buildings = cursor.fetchall()
            
            # Get detailed unit and lease information
            cursor.execute("""
                SELECT u.id as unit_id,
                       u.unit_name,
                       usf.sq_ft as unit_square_footage,
                       u.unit_type_id,
                       b.id as building_id,
                       b.property_name,
                       b.property_address,
                       b.property_code,
                       ut.description as unit_type,
                       l.id as lease_id,
                       l.tenant_id,
                       t.tenant_name,
                       l.rent_pa,
                       l.start_date,
                       l.break_date,
                       l.expiry_date
                FROM units u
                JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id
                    AND (date(?) BETWEEN date(usf.effective_from) AND COALESCE(date(usf.effective_to), '9999-12-31')
                         OR usf.is_current = 1)
                LEFT JOIN leases l ON u.id = l.unit_id 
                    AND date(?) BETWEEN date(l.start_date) AND date(l.expiry_date)
                LEFT JOIN tenants t ON l.tenant_id = t.id
                WHERE u.is_current = 1
                ORDER BY b.property_name, u.unit_name
            """, (reference_date, reference_date))
            units = cursor.fetchall()
            
            return {
                'buildings': buildings,
                'units': units,
                'reference_date': reference_date
            }
    
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
                SELECT u.*, 
                       usf.sq_ft,
                       b.property_name as building_name, 
                       ut.description as unit_type_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id AND usf.is_current = 1
                WHERE u.building_id = ?
                ORDER BY u.unit_name
            """, (building_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_units(self) -> List[Dict[str, Any]]:
        """Get all units"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, 
                       usf.sq_ft,
                       b.property_name as building_name, 
                       ut.description as unit_type_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id AND usf.is_current = 1
                ORDER BY b.property_code, u.unit_name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unit_by_id(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """Get unit by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, 
                       usf.sq_ft,
                       b.property_name as building_name, 
                       ut.description as unit_type_name
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                LEFT JOIN unit_square_footage usf ON u.id = usf.unit_id AND usf.is_current = 1
                WHERE u.id = ?
            """, (unit_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_unit(self, data: Dict[str, Any], user_id: int) -> int:
        """Create a new unit"""
        self._verify_write_permission()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create unit record (without sq_ft)
            cursor.execute("""
                INSERT INTO units (
                    building_id, unit_name, unit_type_id, created_by
                ) VALUES (?, ?, ?, ?)
            """, (
                data.get('building_id'),
                data.get('unit_name'),
                data.get('unit_type_id'),
                user_id
            ))
            unit_id = cursor.lastrowid
            
            # Create sq_ft record if provided
            if data.get('sq_ft'):
                cursor.execute("""
                    INSERT INTO unit_square_footage (
                        unit_id, sq_ft, effective_from, is_current, created_by
                    ) VALUES (?, ?, '2020-01-01', 1, ?)
                """, (
                    unit_id,
                    data.get('sq_ft'),
                    user_id
                ))
            
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
            
            # Update unit record (without sq_ft)
            cursor.execute("""
                UPDATE units
                SET building_id = ?, unit_name = ?, unit_type_id = ?,
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (
                data.get('building_id'),
                data.get('unit_name'),
                data.get('unit_type_id'),
                user_id,
                unit_id
            ))
            
            # Update sq_ft if provided and changed
            if data.get('sq_ft') is not None:
                old_sqft = old_data.get('sq_ft') if old_data else None
                if old_sqft != data.get('sq_ft'):
                    # Mark old sq_ft as not current
                    cursor.execute("""
                        UPDATE unit_square_footage
                        SET is_current = 0, effective_to = DATE('now')
                        WHERE unit_id = ? AND is_current = 1
                    """, (unit_id,))
                    
                    # Insert new sq_ft record
                    cursor.execute("""
                        INSERT INTO unit_square_footage (
                            unit_id, sq_ft, effective_from, is_current, created_by
                        ) VALUES (?, ?, DATE('now'), 1, ?)
                    """, (
                        unit_id,
                        data.get('sq_ft'),
                        user_id
                    ))
            
            # Log audit
            self._log_audit(conn, user_id, 'UPDATE', 'units', unit_id, str(old_data), str(data))
            
            conn.commit()
    
    def delete_unit(self, unit_id: int, user_id: int):
        """Delete a unit (CASCADE will delete unit_square_footage records too)"""
        self._verify_write_permission()
        
        old_data = self.get_unit_by_id(unit_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # ON DELETE CASCADE will automatically delete unit_square_footage records
            cursor.execute("DELETE FROM units WHERE id = ?", (unit_id,))
            
            # Log audit
            self._log_audit(conn, user_id, 'DELETE', 'units', unit_id, str(old_data), None)
            
            conn.commit()
    
    # Tenant management
    def get_all_tenants(self) -> List[Dict[str, Any]]:
        """Get all tenants"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tenants
                ORDER BY tenant_name
            """)
            return cursor.fetchall()
    
    def get_tenant_by_id(self, tenant_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific tenant by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
            return cursor.fetchone()
    
    def get_tenant_by_name(self, tenant_name: str) -> Optional[Dict[str, Any]]:
        """Get a tenant by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenants WHERE tenant_name = ?", (tenant_name,))
            return cursor.fetchone()
    
    def create_tenant(self, data: Dict[str, Any], user_id: int) -> int:
        """Create a new tenant"""
        self._verify_write_permission()
        
        now = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tenants (tenant_name, trading_as, b2c, category_id, notes,
                                    created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data['tenant_name'], data.get('trading_as'), data.get('b2c', 0),
                  data.get('category_id'), data.get('notes'),
                  now, user_id))
            
            tenant_id = cursor.lastrowid
            
            # Log audit
            self._log_audit(conn, user_id, 'INSERT', 'tenants', tenant_id, None, str(data))
            
            conn.commit()
            return tenant_id
    
    def update_tenant(self, tenant_id: int, data: Dict[str, Any], user_id: int):
        """Update an existing tenant"""
        self._verify_write_permission()
        
        old_data = self.get_tenant_by_id(tenant_id)
        now = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tenants
                SET tenant_name = ?, trading_as = ?, b2c = ?, category_id = ?, 
                    notes = ?,
                    updated_at = ?, updated_by = ?
                WHERE id = ?
            """, (data['tenant_name'], data.get('trading_as'), data.get('b2c', 0),
                  data.get('category_id'), data.get('notes'),
                  now, user_id, tenant_id))
            
            # Log audit
            self._log_audit(conn, user_id, 'UPDATE', 'tenants', tenant_id, str(old_data), str(data))
            
            conn.commit()
    
    def delete_tenant(self, tenant_id: int, user_id: int):
        """Delete a tenant"""
        self._verify_write_permission()
        
        old_data = self.get_tenant_by_id(tenant_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
            
            # Log audit
            self._log_audit(conn, user_id, 'DELETE', 'tenants', tenant_id, str(old_data), None)
            
            conn.commit()
    
    # Lease management
    def get_leases(self) -> List[Dict[str, Any]]:
        """Get all leases with tenant and unit information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, 
                       t.tenant_name,
                       u.unit_name,
                       b.property_name as building_name
                FROM leases l
                JOIN tenants t ON l.tenant_id = t.id
                JOIN units u ON l.unit_id = u.id
                JOIN buildings b ON u.building_id = b.id
                ORDER BY l.start_date DESC
            """)
            return cursor.fetchall()
    
    def get_active_leases(self, reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get leases active on a specific date (defaults to today)"""
        if reference_date is None:
            reference_date = datetime.now().strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, 
                       t.tenant_name,
                       u.unit_name,
                       b.property_name as building_name
                FROM leases l
                JOIN tenants t ON l.tenant_id = t.id
                JOIN units u ON l.unit_id = u.id
                JOIN buildings b ON u.building_id = b.id
                WHERE date(?) BETWEEN date(l.start_date) AND date(l.expiry_date)
                ORDER BY l.start_date DESC
            """, (reference_date,))
            return cursor.fetchall()
    
    def get_lease_by_id(self, lease_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific lease by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, 
                       t.tenant_name,
                       u.unit_name,
                       b.property_name as building_name
                FROM leases l
                JOIN tenants t ON l.tenant_id = t.id
                JOIN units u ON l.unit_id = u.id
                JOIN buildings b ON u.building_id = b.id
                WHERE l.id = ?
            """, (lease_id,))
            return cursor.fetchone()
    
    def get_leases_by_unit(self, unit_id: int) -> List[Dict[str, Any]]:
        """Get all leases for a specific unit"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, 
                       t.tenant_name
                FROM leases l
                JOIN tenants t ON l.tenant_id = t.id
                WHERE l.unit_id = ?
                ORDER BY l.start_date DESC
            """, (unit_id,))
            return cursor.fetchall()
    
    def get_current_lease_by_unit(self, unit_id: int, reference_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the active lease for a unit on a specific date (defaults to today)"""
        if reference_date is None:
            reference_date = datetime.now().strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, 
                       t.tenant_name
                FROM leases l
                JOIN tenants t ON l.tenant_id = t.id
                WHERE l.unit_id = ?
                  AND date(?) BETWEEN date(l.start_date) AND date(l.expiry_date)
                ORDER BY l.start_date DESC
                LIMIT 1
            """, (unit_id, reference_date))
            return cursor.fetchone()
    
    def get_leases_by_tenant(self, tenant_id: int) -> List[Dict[str, Any]]:
        """Get all leases for a specific tenant"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, 
                       u.unit_name,
                       b.property_name as building_name
                FROM leases l
                JOIN units u ON l.unit_id = u.id
                JOIN buildings b ON u.building_id = b.id
                WHERE l.tenant_id = ?
                ORDER BY l.start_date DESC
            """, (tenant_id,))
            return cursor.fetchall()
    
    def get_units_with_leases(self, reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all current units with their lease information for a specific date (defaults to today)"""
        if reference_date is None:
            reference_date = datetime.now().strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id as unit_id,
                       u.unit_name,
                       u.unit_size,
                       u.unit_type_id,
                       b.id as building_id,
                       b.property_name,
                       b.property_address,
                       ut.type_name as unit_type,
                       l.id as lease_id,
                       l.tenant_id,
                       t.tenant_name,
                       l.rent_pa,
                       l.start_date,
                       l.break_date,
                       l.expiry_date
                FROM units u
                LEFT JOIN buildings b ON u.building_id = b.id
                LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
                LEFT JOIN leases l ON u.id = l.unit_id 
                    AND date(?) BETWEEN date(l.start_date) AND date(l.expiry_date)
                LEFT JOIN tenants t ON l.tenant_id = t.id
                WHERE u.is_current = 1
                ORDER BY b.property_name, u.unit_name
            """, (reference_date,))
            return cursor.fetchall()
    
    def create_lease(self, data: Dict[str, Any], user_id: int) -> int:
        """Create a new lease"""
        self._verify_write_permission()
        
        now = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leases (tenant_id, unit_id, rent_pa, start_date, break_date, expiry_date,
                                   bank_schedule_date, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data['tenant_id'], data['unit_id'], data['rent_pa'], 
                  data['start_date'], data.get('break_date'), data['expiry_date'],
                  data.get('bank_schedule_date'), now, user_id))
            
            lease_id = cursor.lastrowid
            
            # Log audit
            self._log_audit(conn, user_id, 'INSERT', 'leases', lease_id, None, str(data))
            
            conn.commit()
            return lease_id
    
    def update_lease(self, lease_id: int, data: Dict[str, Any], user_id: int):
        """Update an existing lease"""
        self._verify_write_permission()
        
        old_data = self.get_lease_by_id(lease_id)
        now = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leases
                SET tenant_id = ?, unit_id = ?, rent_pa = ?, start_date = ?, 
                    break_date = ?, expiry_date = ?, bank_schedule_date = ?,
                    updated_at = ?, updated_by = ?
                WHERE id = ?
            """, (data['tenant_id'], data['unit_id'], data['rent_pa'], 
                  data['start_date'], data.get('break_date'), data['expiry_date'],
                  data.get('bank_schedule_date'), now, user_id, lease_id))
            
            # Log audit
            self._log_audit(conn, user_id, 'UPDATE', 'leases', lease_id, str(old_data), str(data))
            
            conn.commit()
    
    def delete_lease(self, lease_id: int, user_id: int):
        """Delete a lease"""
        self._verify_write_permission()
        
        old_data = self.get_lease_by_id(lease_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM leases WHERE id = ?", (lease_id,))
            
            # Log audit
            self._log_audit(conn, user_id, 'DELETE', 'leases', lease_id, str(old_data), None)
            
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
    
    def user_has_role(self, user_id: int, role_name: str) -> bool:
        """Check if user has a specific role by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = ? AND r.name = ?
            """, (user_id, role_name))
            result = cursor.fetchone()
            return result['count'] > 0 if result else False
    
    def user_has_permission(self, user_id: int, permission_name: str) -> bool:
        """Check if user has a specific permission through any of their roles"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = ? AND p.name = ?
            """, (user_id, permission_name))
            result = cursor.fetchone()
            return result['count'] > 0 if result else False
