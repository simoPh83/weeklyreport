"""
Unit Service
Handles all unit-related business logic
"""
from typing import List, Dict, Any, Optional
from repositories import BaseRepository
from models import Unit


class UnitService:
    """Service for unit management"""
    
    def __init__(self, repository: BaseRepository, auth_service):
        self.repository = repository
        self.auth_service = auth_service
    
    def get_all_units(self) -> List[Unit]:
        """Get all units"""
        units_data = self.repository.get_all_units()
        return [Unit(**unit) for unit in units_data]
    
    def get_units_by_building(self, building_id: int) -> List[Unit]:
        """Get all units for a specific building"""
        units_data = self.repository.get_units_by_building(building_id)
        return [Unit(**unit) for unit in units_data]
    
    def get_unit_by_id(self, unit_id: int) -> Optional[Unit]:
        """Get unit by ID"""
        unit_data = self.repository.get_unit_by_id(unit_id)
        return Unit(**unit_data) if unit_data else None
    
    def create_unit(self, unit_data: Dict[str, Any]) -> int:
        """
        Create new unit
        Returns unit ID
        Raises exception if user doesn't have write lock
        """
        user = self.auth_service.get_current_user()
        if not user:
            raise PermissionError("No authenticated user")
        
        # Repository will verify write lock
        return self.repository.create_unit(unit_data, user.id)
    
    def update_unit(self, unit_id: int, unit_data: Dict[str, Any]) -> bool:
        """
        Update existing unit
        Returns True if successful
        Raises exception if user doesn't have write lock
        """
        user = self.auth_service.get_current_user()
        if not user:
            raise PermissionError("No authenticated user")
        
        # Repository will verify write lock
        self.repository.update_unit(unit_id, unit_data, user.id)
        return True
    
    def delete_unit(self, unit_id: int) -> bool:
        """
        Delete unit
        Returns True if successful
        Raises exception if user doesn't have write lock
        """
        user = self.auth_service.get_current_user()
        if not user:
            raise PermissionError("No authenticated user")
        
        # Repository will verify write lock
        self.repository.delete_unit(unit_id, user.id)
        return True
    
    def get_vacant_units(self) -> List[Unit]:
        """Get all vacant units"""
        # TODO: Implement vacancy tracking in new schema
        return []
    
    def get_occupied_units(self) -> List[Unit]:
        """Get all let units"""
        # TODO: Implement let/vacant tracking in new schema
        return []
    
    def get_unit_statistics(self) -> Dict[str, Any]:
        """Get statistics about all units"""
        units = self.get_all_units()
        
        # TODO: Update statistics for new schema
        return {
            'total_units': len(units),
            'vacant_units': 0,
            'let_units': 0,
            'total_sqft': sum(u.sq_ft for u in units if u.sq_ft),
            'total_rent': 0.0
        }
    
    def _group_by_type(self, units: List[Unit]) -> Dict[str, int]:
        """Group units by type"""
        type_counts = {}
        for unit in units:
            unit_type = unit.unit_type or 'Unknown'
            type_counts[unit_type] = type_counts.get(unit_type, 0) + 1
        return type_counts
    
    def search_units(self, search_term: str) -> List[Unit]:
        """Search units by unit number, tenant name, or building name"""
        all_units = self.get_all_units()
        search_lower = search_term.lower()
        
        return [
            unit for unit in all_units
            if (search_lower in unit.unit_number.lower() or
                (unit.tenant_name and search_lower in unit.tenant_name.lower()) or
                (unit.building_name and search_lower in unit.building_name.lower()))
        ]
