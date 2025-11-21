"""Unit model"""
from typing import Optional
from pydantic import BaseModel, Field


class Unit(BaseModel):
    """Unit model - database agnostic"""
    id: Optional[int] = None
    building_id: int
    unit_number: str = Field(..., min_length=1)
    floor: Optional[int] = None
    unit_type: Optional[str] = None  # 'Office' or 'Retail'
    square_feet: Optional[float] = None
    rent_amount: Optional[float] = None
    status: Optional[str] = None  # 'Vacant' or 'Let'
    tenant_name: Optional[str] = None
    tenant_phone: Optional[str] = None
    tenant_email: Optional[str] = None
    lease_start: Optional[str] = None  # Store as string for date compatibility
    lease_end: Optional[str] = None
    monthly_rent: Optional[float] = None
    notes: Optional[str] = None
    
    # For display purposes (joined data)
    building_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UnitCreate(BaseModel):
    """Unit creation request"""
    building_id: int
    unit_number: str = Field(..., min_length=1)
    floor: Optional[int] = None
    unit_type: Optional[str] = None
    square_feet: Optional[float] = None
    rent_amount: Optional[float] = None
    status: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_phone: Optional[str] = None
    tenant_email: Optional[str] = None
    lease_start: Optional[str] = None
    lease_end: Optional[str] = None
    monthly_rent: Optional[float] = None
    notes: Optional[str] = None


class UnitUpdate(UnitCreate):
    """Unit update request"""
    id: int
