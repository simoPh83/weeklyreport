"""Building model"""
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class Building(BaseModel):
    """Building model - UK commercial property"""
    id: Optional[int] = None
    property_code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    property_name: Optional[str] = None
    property_address: str = Field(..., min_length=1)
    postcode: str = Field(..., min_length=1)
    client_code: str = Field(..., min_length=1, max_length=10)
    acquisition_date: Optional[date] = None
    disposal_date: Optional[date] = None
    notes: Optional[str] = None
    occupancy: Optional[float] = None  # Occupancy percentage (0-100), calculated field
    latest_valuation_year: Optional[int] = None  # Most recent valuation year
    latest_valuation_amount: Optional[float] = None  # Most recent valuation amount (£)
    
    class Config:
        from_attributes = True


class BuildingCreate(BaseModel):
    """Building creation request"""
    property_code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    property_name: Optional[str] = None
    property_address: str = Field(..., min_length=1)
    postcode: str = Field(..., min_length=1)
    client_code: str = Field(..., min_length=1, max_length=10)
    acquisition_date: Optional[date] = None
    disposal_date: Optional[date] = None
    notes: Optional[str] = None


class BuildingUpdate(BuildingCreate):
    """Building update request"""
    id: int
