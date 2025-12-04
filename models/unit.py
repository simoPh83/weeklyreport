"""Unit model"""
from typing import Optional
from pydantic import BaseModel, Field


class Unit(BaseModel):
    """Unit model - database agnostic"""
    id: Optional[int] = None
    building_id: int
    unit_name: str = Field(..., min_length=1)
    sq_ft: Optional[float] = None
    unit_type_id: int
    notes: Optional[str] = None
    
    # For display purposes (joined data)
    building_name: Optional[str] = None
    unit_type_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UnitCreate(BaseModel):
    """Unit creation request"""
    building_id: int
    unit_name: str = Field(..., min_length=1)
    sq_ft: Optional[float] = None
    unit_type_id: int
    notes: Optional[str] = None


class UnitUpdate(UnitCreate):
    """Unit update request"""
    id: int
