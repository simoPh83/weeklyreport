"""
Authentication Service
Handles user authentication, sessions, and lock management
"""
from typing import Optional, Tuple, List, Dict, Any
from repositories import BaseRepository
from models import User


class AuthService:
    """Service for authentication and session management"""
    
    def __init__(self, repository: BaseRepository):
        self.repository = repository
        self._current_user: Optional[User] = None
        self._session_id: Optional[int] = None
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password
        Returns User object if successful, None otherwise
        """
        user_result = self.repository.authenticate_user(username, password)
        if user_result:
            # Check if it's already a User object or a dict
            if isinstance(user_result, User):
                self._current_user = user_result
            else:
                # It's a dict, convert to User
                self._current_user = User(
                    id=user_result['id'],
                    username=user_result['username'],
                    display_name=user_result['display_name'],
                    is_admin=user_result.get('is_admin', False)
                )
            return self._current_user
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all active users"""
        users_data = self.repository.get_all_users()
        return [User(
            id=u['id'],
            username=u['username'],
            display_name=u['display_name'],
            is_admin=u.get('is_admin', False)
        ) for u in users_data]
    
    def acquire_write_lock(self, user_id: int, username: str) -> Tuple[bool, str]:
        """
        Acquire write lock for user
        Returns (success, message/session_id)
        """
        success, result = self.repository.acquire_lock(user_id, username)
        if success and result:
            try:
                self._session_id = int(result) if isinstance(result, (int, str)) else None
            except (ValueError, TypeError):
                pass
        return success, result or ""
    
    def release_write_lock(self, user_id: int) -> bool:
        """Release write lock for user"""
        if self._session_id:
            # Repository expects string session_id
            return self.repository.release_lock(str(self._session_id))
        return False
    
    def verify_write_lock(self) -> bool:
        """Verify current user still has write lock"""
        # Access via LocalRepository if available
        try:
            from repositories import LocalRepository
            if isinstance(self.repository, LocalRepository):
                return self.repository.lock_manager.verify_write_lock()
        except Exception:
            pass
        return False
    
    def get_current_user(self) -> Optional[User]:
        """Get currently authenticated user"""
        return self._current_user
    
    def set_current_user(self, user: User, session_id: Optional[int] = None):
        """Set current user (for session restoration)"""
        self._current_user = user
        self._session_id = session_id
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        # Access via LocalRepository if available
        try:
            from repositories import LocalRepository
            if isinstance(self.repository, LocalRepository):
                return self.repository.get_active_sessions()
        except Exception:
            pass
        return []
    
    def get_write_lock_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current write lock holder"""
        # Access via LocalRepository if available
        try:
            from repositories import LocalRepository
            if isinstance(self.repository, LocalRepository):
                return self.repository.get_write_lock_info()
        except Exception:
            pass
        return None
    
    def force_release_lock(self, user_id: int, admin_user_id: int) -> bool:
        """
        Force release write lock (admin only)
        Returns True if successful
        """
        # Access via LocalRepository if available
        try:
            from repositories import LocalRepository
            if isinstance(self.repository, LocalRepository):
                success, message = self.repository.lock_manager.force_unlock(admin_user_id)
                if not success:
                    print(f"Force unlock failed: {message}")
                return success
        except Exception as e:
            print(f"Exception in force_release_lock: {e}")
        return False
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self._current_user.is_admin if self._current_user else False
    
    def logout(self):
        """Logout current user"""
        if self._current_user and self._session_id:
            self.release_write_lock(self._current_user.id)
        self._current_user = None
        self._session_id = None
