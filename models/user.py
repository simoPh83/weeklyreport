"""User model"""
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """User model - works with both SQLite and Supabase"""
    id: Optional[int] = None
    username: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    is_admin: bool = False
    
    # For Supabase mode (future)
    email: Optional[str] = None
    auth_id: Optional[str] = None  # Supabase UUID
    
    class Config:
        from_attributes = True  # Allow ORM mode for SQLite rows


class UserLogin(BaseModel):
    """Login request model"""
    username: str
    password: Optional[str] = None  # Only for server mode
    
    
class UserSession(BaseModel):
    """User session information"""
    user: User
    session_id: Optional[str] = None
    token: Optional[str] = None  # JWT for server mode
