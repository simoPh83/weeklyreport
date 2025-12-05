"""Unit model"""
from typing import Optional
from pydantic import BaseModel, Field


class Unit(BaseModel):
    """Unit model - database agnostic"""
    id: Optional[int] = None
    unit_id: Optional[int] = None  # Alias for id from joined queries
    building_id: int
    unit_name: str = Field(..., min_length=1)
    sq_ft: Optional[float] = None
    unit_square_footage: Optional[float] = None  # Actual database column name
    unit_type_id: Optional[int] = None
    notes: Optional[str] = None
    
    # For display purposes (joined data)
    building_name: Optional[str] = None
    unit_type_name: Optional[str] = None
    property_name: Optional[str] = None  # Building property name
    property_address: Optional[str] = None  # Building property address
    property_code: Optional[str] = None  # Building property code
    unit_type: Optional[str] = None  # Alternative name for unit_type_name
    
    # Lease information (joined data)
    lease_id: Optional[int] = None
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    rent_pa: Optional[float] = None
    start_date: Optional[str] = None
    break_date: Optional[str] = None
    expiry_date: Optional[str] = None
    
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
