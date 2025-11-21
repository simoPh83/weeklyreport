"""
Repository pattern base interface
All data access must implement this interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from models import User, Building, Unit, Session, AuditLog, LockStatus


class BaseRepository(ABC):
    """Abstract base class for data access"""
    
    # ==================== Authentication ====================
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    def authenticate_user(self, username: str, password: Optional[str] = None) -> Optional[User]:
        """
        Authenticate user
        Local mode: validates password with bcrypt
        Server mode: validates against Supabase auth
        """
        pass
    
    # ==================== Lock Management ====================
    
    @abstractmethod
    def acquire_lock(self, user_id: int, username: str, ip_address: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Acquire write lock
        Returns: (success: bool, session_id: Optional[str])
        """
        pass
    
    @abstractmethod
    def release_lock(self, session_id: str) -> bool:
        """Release write lock"""
        pass
    
    @abstractmethod
    def get_lock_status(self) -> LockStatus:
        """Get current lock status"""
        pass
    
    @abstractmethod
    def force_unlock(self, admin_user_id: int) -> bool:
        """Force release lock (admin only)"""
        pass
    
    @abstractmethod
    def update_heartbeat(self, session_id: str) -> bool:
        """Update session heartbeat"""
        pass
    
    @abstractmethod
    def verify_session(self, session_id: str) -> bool:
        """Verify session is still valid"""
        pass
    
    # ==================== Building CRUD ====================
    
    @abstractmethod
    def get_buildings(self) -> List[Building]:
        """Get all buildings"""
        pass
    
    @abstractmethod
    def get_building_by_id(self, building_id: int) -> Optional[dict]:
        """Get building by ID"""
        pass
    
    @abstractmethod
    def create_building(self, building_data: dict, user_id: int) -> int:
        """Create new building"""
        pass
    
    @abstractmethod
    def update_building(self, building_id: int, building_data: dict, user_id: int) -> bool:
        """Update existing building"""
        pass
    
    @abstractmethod
    def delete_building(self, building_id: int, user_id: int) -> bool:
        """Delete building"""
        pass
    
    # ==================== Unit CRUD ====================
    
    @abstractmethod
    def get_units(self, building_id: Optional[int] = None) -> List[Unit]:
        """Get all units, optionally filtered by building"""
        pass
    
    @abstractmethod
    def get_unit_by_id(self, unit_id: int) -> Optional[dict]:
        """Get unit by ID"""
        pass
    
    @abstractmethod
    def create_unit(self, unit_data: dict, user_id: int) -> int:
        """Create new unit"""
        pass
    
    @abstractmethod
    def update_unit(self, unit_id: int, unit_data: dict, user_id: int) -> bool:
        """Update existing unit"""
        pass
    
    @abstractmethod
    def delete_unit(self, unit_id: int, user_id: int) -> bool:
        """Delete unit"""
        pass
    
    # ==================== Audit Log ====================
    
    @abstractmethod
    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        pass
    
    # ==================== Cleanup ====================
    
    @abstractmethod
    def cleanup_stale_sessions(self, timeout_minutes: int = 10) -> int:
        """Clean up stale sessions, returns count of cleaned sessions"""
        pass
    
    @abstractmethod
    def close(self):
        """Close connections and cleanup resources"""
        pass
