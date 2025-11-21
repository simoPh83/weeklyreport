"""Session model"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class Session(BaseModel):
    """Lock session model"""
    session_id: str
    user_id: int
    username: str
    ip_address: Optional[str] = None
    created_at: datetime
    last_heartbeat: datetime
    
    class Config:
        from_attributes = True


class LockStatus(BaseModel):
    """Lock status information"""
    is_locked: bool
    locked_by: Optional[str] = None  # Username
    locked_since: Optional[datetime] = None
    can_force_unlock: bool = False  # If current user is admin
