"""Audit log model"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class AuditLog(BaseModel):
    """Audit log entry"""
    id: Optional[int] = None
    timestamp: datetime
    username: str
    action: str  # CREATE, UPDATE, DELETE
    table_name: str  # buildings, units
    record_id: int
    details: Optional[str] = None
    
    class Config:
        from_attributes = True
