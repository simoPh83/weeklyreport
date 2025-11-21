"""
API Repository Implementation (Future - for FastAPI backend)
This is a stub showing the structure for when migrating to client/server
"""
from typing import List, Optional
import httpx
from repositories.base_repository import BaseRepository
from models import User, Building, Unit, Session, AuditLog, LockStatus


class APIRepository(BaseRepository):
    """
    FastAPI + Supabase implementation (FUTURE)
    
    When ready to migrate:
    1. Set USE_LOCAL_MODE = False in config.py
    2. Implement these methods with httpx HTTP calls
    3. Add WebSocket listener for real-time notifications
    4. Use Supabase JWT tokens for authentication
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": api_key} if api_key else {},
            timeout=30.0
        )
        self.token = None  # JWT token from Supabase
        self.ws = None  # WebSocket connection
    
    # ==================== Authentication ====================
    
    def get_users(self) -> List[User]:
        """GET /api/users"""
        raise NotImplementedError("API mode not yet implemented")
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """GET /api/users/{username}"""
        raise NotImplementedError("API mode not yet implemented")
    
    def authenticate_user(self, username: str, password: Optional[str] = None) -> Optional[User]:
        """
        POST /api/auth/login
        Returns User with JWT token from Supabase
        """
        raise NotImplementedError("API mode not yet implemented")
    
    # ==================== Lock Management ====================
    
    def acquire_lock(self, user_id: int, username: str, ip_address: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """POST /api/lock/acquire"""
        raise NotImplementedError("API mode not yet implemented")
    
    def release_lock(self, session_id: str) -> bool:
        """POST /api/lock/release"""
        raise NotImplementedError("API mode not yet implemented")
    
    def get_lock_status(self) -> LockStatus:
        """GET /api/lock/status"""
        raise NotImplementedError("API mode not yet implemented")
    
    def force_unlock(self, admin_user_id: int) -> bool:
        """POST /api/lock/force-unlock (admin only)"""
        raise NotImplementedError("API mode not yet implemented")
    
    def update_heartbeat(self, session_id: str) -> bool:
        """POST /api/lock/heartbeat"""
        raise NotImplementedError("API mode not yet implemented")
    
    def verify_session(self, session_id: str) -> bool:
        """GET /api/session/verify"""
        raise NotImplementedError("API mode not yet implemented")
    
    # ==================== Building CRUD ====================
    
    def get_buildings(self) -> List[Building]:
        """GET /api/buildings"""
        raise NotImplementedError("API mode not yet implemented")
    
    def get_building_by_id(self, building_id: int) -> Optional[Building]:
        """GET /api/buildings/{id}"""
        raise NotImplementedError("API mode not yet implemented")
    
    def create_building(self, building: Building, user_id: int) -> Building:
        """POST /api/buildings"""
        raise NotImplementedError("API mode not yet implemented")
    
    def update_building(self, building: Building, user_id: int) -> Building:
        """PUT /api/buildings/{id}"""
        raise NotImplementedError("API mode not yet implemented")
    
    def delete_building(self, building_id: int, user_id: int) -> bool:
        """DELETE /api/buildings/{id}"""
        raise NotImplementedError("API mode not yet implemented")
    
    # ==================== Unit CRUD ====================
    
    def get_units(self, building_id: Optional[int] = None) -> List[Unit]:
        """GET /api/units?building_id={id}"""
        raise NotImplementedError("API mode not yet implemented")
    
    def get_unit_by_id(self, unit_id: int) -> Optional[Unit]:
        """GET /api/units/{id}"""
        raise NotImplementedError("API mode not yet implemented")
    
    def create_unit(self, unit: Unit, user_id: int) -> Unit:
        """POST /api/units"""
        raise NotImplementedError("API mode not yet implemented")
    
    def update_unit(self, unit: Unit, user_id: int) -> Unit:
        """PUT /api/units/{id}"""
        raise NotImplementedError("API mode not yet implemented")
    
    def delete_unit(self, unit_id: int, user_id: int) -> bool:
        """DELETE /api/units/{id}"""
        raise NotImplementedError("API mode not yet implemented")
    
    # ==================== Audit Log ====================
    
    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """GET /api/audit?limit={limit}"""
        raise NotImplementedError("API mode not yet implemented")
    
    # ==================== Cleanup ====================
    
    def cleanup_stale_sessions(self, timeout_minutes: int = 10) -> int:
        """POST /api/sessions/cleanup (admin only)"""
        raise NotImplementedError("API mode not yet implemented")
    
    def close(self):
        """Close HTTP client and WebSocket"""
        if self.ws:
            # Close WebSocket
            pass
        self.client.close()


# Example WebSocket usage (future):
"""
async def listen_for_notifications(api_repo: APIRepository, callback):
    '''Listen for real-time notifications from server'''
    async with websockets.connect(f"{api_repo.base_url}/ws") as ws:
        # Send auth token
        await ws.send(json.dumps({"type": "auth", "token": api_repo.token}))
        
        # Listen for messages
        async for message in ws:
            data = json.dumps(message)
            if data['type'] == 'lock_removed':
                callback('lock_lost')
            elif data['type'] == 'force_unlock':
                callback('force_unlock')
"""
