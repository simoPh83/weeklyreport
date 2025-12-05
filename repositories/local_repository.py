"""
Local Repository Implementation
Wraps existing DatabaseManager and LockManager for local SQLite mode
"""
import socket
from typing import List, Optional
from datetime import datetime

from repositories.base_repository import BaseRepository
from models import User, Building, Unit, Session, AuditLog, LockStatus
from database.db_manager import DatabaseManager, DatabaseWriteError
from core.lock_manager import LockManager
from config import USE_FILE_LOCK


class LocalRepository(BaseRepository):
    """Local SQLite + file lock implementation"""
    
    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.lock_manager = LockManager(db_path, self.db_manager)
        # Link them together (existing pattern)
        self.db_manager.set_lock_manager(self.lock_manager)
    
    def _get_local_ip(self) -> str:
        """Get local machine IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    # ==================== Authentication ====================
    
    def get_all_users(self) -> List[dict]:
        """Get all users (returns raw dicts for backward compatibility)"""
        return self.db_manager.get_all_users()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        row = self.db_manager.get_user_by_username(username)
        if row:
            return User(**dict(row))
        return None
    
    def authenticate_user(self, username: str, password: Optional[str] = None) -> Optional[User]:
        """
        Authenticate user
        Local mode: Verifies password if provided, otherwise backward compatible
        """
        if password:
            # Authenticate with password
            user_dict = self.db_manager.authenticate_user(username, password)
            if user_dict:
                return User(**user_dict)
            return None
        else:
            # Backward compatibility: no password required
            return self.get_user_by_username(username)
    
    # ==================== Lock Management ====================
    
    def acquire_lock(self, user_id: int, username: str, ip_address: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """Acquire write lock (bypassed if USE_FILE_LOCK is False)"""
        if not USE_FILE_LOCK:
            return True, "file_lock_disabled"
        
        success, error_msg = self.lock_manager.acquire_write_lock(user_id, username)
        if success:
            return True, str(self.lock_manager.current_session_id)
        return False, error_msg
    
    def release_lock(self, session_id: str) -> bool:
        """Release write lock (bypassed if USE_FILE_LOCK is False)"""
        if not USE_FILE_LOCK:
            return True
        
        self.lock_manager.release_write_lock()
        return True
    
    def get_lock_status(self) -> LockStatus:
        """Get current lock status (bypassed if USE_FILE_LOCK is False)"""
        if not USE_FILE_LOCK:
            return LockStatus(is_locked=False, can_force_unlock=False)
        
        lock_holder = self.lock_manager._get_current_lock_holder()
        
        if lock_holder:
            return LockStatus(
                is_locked=True,
                locked_by=lock_holder.get('username'),
                locked_since=None,  # Can add timestamp parsing if needed
                can_force_unlock=False  # Will be set by service based on current user
            )
        
        return LockStatus(is_locked=False, can_force_unlock=False)
    
    def force_unlock(self, admin_user_id: int) -> bool:
        """Force release lock (admin only)"""
        success, msg = self.lock_manager.force_unlock(admin_user_id)
        return success
    
    def update_heartbeat(self, session_id: str) -> bool:
        """Update session heartbeat - handled automatically by lock manager"""
        # Heartbeat is automatic in current implementation
        return True
    
    def verify_session(self, session_id: str) -> bool:
        """Verify session is still valid (bypassed if USE_FILE_LOCK is False)"""
        if not USE_FILE_LOCK:
            return True
        
        return self.lock_manager.verify_write_lock()
    
    # ==================== Buildings ====================
    
    def get_buildings(self) -> List[Building]:
        """Get all buildings"""
        rows = self.db_manager.get_all_buildings()
        return [Building(**dict(row)) for row in rows]
    
    def get_all_buildings(self) -> List[dict]:
        """Get all buildings (returns raw dicts for backward compatibility)"""
        return self.db_manager.get_all_buildings()
    
    def get_all_current_buildings(self) -> List[dict]:
        """Get all buildings with current capital valuations (returns raw dicts)"""
        return self.db_manager.get_all_current_buildings()
    
    def get_property_snapshot(self, reference_date: Optional[str] = None) -> dict:
        """Get complete property snapshot with buildings, units, leases, and occupancy"""
        return self.db_manager.get_property_snapshot(reference_date)
    
    def get_building_by_id(self, building_id: int) -> Optional[dict]:
        """Get building by ID"""
        row = self.db_manager.get_building_by_id(building_id)
        if row:
            return dict(row)
        return None
    
    def create_building(self, building_data: dict, user_id: int) -> int:
        """Create new building"""
        # building_data is already a dict, just pass it through
        building_id = self.db_manager.create_building(
            data=building_data,
            user_id=user_id
        )
        
        return building_id
    
    def update_building(self, building_id: int, building_data: dict, user_id: int) -> bool:
        """Update existing building"""
        # building_data is already a dict, just pass it through
        self.db_manager.update_building(
            building_id=building_id,
            data=building_data,
            user_id=user_id
        )
        
        return True
    
    def delete_building(self, building_id: int, user_id: int) -> bool:
        """Delete building"""
        self.db_manager.delete_building(building_id, user_id)
        return True
    
    # ==================== Unit CRUD ====================
    
    def get_units(self, building_id: Optional[int] = None) -> List[Unit]:
        """Get all units, optionally filtered by building"""
        if building_id:
            rows = self.db_manager.get_units_by_building(building_id)
        else:
            rows = self.db_manager.get_all_units()
        
        return [Unit(**dict(row)) for row in rows]
    
    def get_all_units(self) -> List[dict]:
        """Get all units (returns raw dicts for backward compatibility)"""
        return self.db_manager.get_all_units()
    
    def get_units_by_building(self, building_id: int) -> List[dict]:
        """Get units by building (returns raw dicts for backward compatibility)"""
        return self.db_manager.get_units_by_building(building_id)
    
    def get_unit_by_id(self, unit_id: int) -> Optional[dict]:
        """Get unit by ID"""
        row = self.db_manager.get_unit_by_id(unit_id)
        if row:
            return dict(row)
        return None
    
    def create_unit(self, unit_data: dict, user_id: int) -> int:
        """Create new unit"""
        # unit_data is already a dict, just pass it through
        unit_id = self.db_manager.create_unit(
            data=unit_data,
            user_id=user_id
        )
        
        return unit_id
    
    def update_unit(self, unit_id: int, unit_data: dict, user_id: int) -> bool:
        """Update existing unit"""
        # unit_data is already a dict, just pass it through
        self.db_manager.update_unit(
            unit_id=unit_id,
            data=unit_data,
            user_id=user_id
        )
        
        return True
    
    def delete_unit(self, unit_id: int, user_id: int) -> bool:
        """Delete unit"""
        self.db_manager.delete_unit(unit_id, user_id)
        return True
    
    # ==================== Audit Log ====================
    
    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        rows = self.db_manager.get_audit_log(limit)  # Note: method is get_audit_log not get_audit_logs
        return [AuditLog(**dict(row)) for row in rows]
    
    def get_audit_log(self, limit: int = 100) -> List[dict]:
        """Get audit log entries (returns raw dicts for backward compatibility)"""
        return self.db_manager.get_audit_log(limit)
    
    # ==================== RBAC - Roles and Permissions ====================
    
    def get_all_roles(self) -> List[dict]:
        """Get all roles"""
        return self.db_manager.get_all_roles()
    
    def get_all_permissions(self) -> List[dict]:
        """Get all permissions"""
        return self.db_manager.get_all_permissions()
    
    def get_role_permissions(self) -> List[dict]:
        """Get all role-permission mappings"""
        return self.db_manager.get_role_permissions()
    
    def grant_role_permission(self, role_id: int, permission_id: int, user_id: int) -> bool:
        """Grant a permission to a role"""
        return self.db_manager.grant_role_permission(role_id, permission_id, user_id)
    
    def revoke_role_permission(self, role_id: int, permission_id: int, user_id: int) -> bool:
        """Revoke a permission from a role"""
        return self.db_manager.revoke_role_permission(role_id, permission_id, user_id)
    
    def get_user_roles(self) -> List[dict]:
        """Get all user-role assignments"""
        return self.db_manager.get_user_roles()
    
    def assign_user_role(self, user_id: int, role_id: int, assigned_by: int) -> bool:
        """Assign a role to a user"""
        return self.db_manager.assign_user_role(user_id, role_id, assigned_by)
    
    def unassign_user_role(self, user_id: int, role_id: int, unassigned_by: int) -> bool:
        """Unassign a role from a user"""
        return self.db_manager.unassign_user_role(user_id, role_id, unassigned_by)
    
    def user_has_role(self, user_id: int, role_name: str) -> bool:
        """Check if user has a specific role"""
        return self.db_manager.user_has_role(user_id, role_name)
    
    def user_has_permission(self, user_id: int, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        return self.db_manager.user_has_permission(user_id, permission_name)
    
    # ==================== Cleanup ====================
    
    def cleanup_stale_sessions(self, timeout_minutes: int = 10) -> int:
        """Clean up stale sessions"""
        # Call lock manager's cleanup
        self.lock_manager._cleanup_stale_locks()
        return 0  # Lock manager doesn't return count
    
    def close(self):
        """Close connections and cleanup resources"""
        if self.lock_manager:
            self.lock_manager.release_write_lock()
