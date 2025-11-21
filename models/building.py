"""Building model"""
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class Building(BaseModel):
    """Building model - database agnostic"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1)
    address: Optional[str] = Field(None, min_length=1)  # Made optional
    city: Optional[str] = Field(None, min_length=1)  # Made optional
    state: Optional[str] = Field(None, min_length=1, max_length=50)
    zip_code: Optional[str] = Field(None, min_length=2, max_length=20)
    notes: Optional[str] = None
    occupancy: Optional[float] = None  # Occupancy percentage (0-100)
    
    class Config:
        from_attributes = True


class BuildingCreate(BaseModel):
    """Building creation request"""
    name: str = Field(..., min_length=1)
    address: Optional[str] = Field(None, min_length=1)
    city: Optional[str] = Field(None, min_length=1)
    state: Optional[str] = Field(None, min_length=1, max_length=50)
    zip_code: Optional[str] = Field(None, min_length=2, max_length=20)
    notes: Optional[str] = None


class BuildingUpdate(BuildingCreate):
    """Building update request"""
    id: int
