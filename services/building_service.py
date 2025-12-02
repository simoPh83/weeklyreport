"""
Building Service
Handles all building-related business logic
"""
from typing import List, Dict, Any, Optional
from repositories import BaseRepository
from models import Building


class BuildingService:
    """Service for building management"""
    
    def __init__(self, repository: BaseRepository, auth_service):
        self.repository = repository
        self.auth_service = auth_service
    
    def get_all_buildings(self) -> List[Building]:
        """Get all buildings with current capital valuations"""
        buildings_data = self.repository.get_all_current_buildings()
        return [Building(**building) for building in buildings_data]
    
    def get_building_by_id(self, building_id: int) -> Optional[Building]:
        """Get building by ID"""
        building_data = self.repository.get_building_by_id(building_id)
        return Building(**building_data) if building_data else None
    
    def create_building(self, building_data: Dict[str, Any]) -> int:
        """
        Create new building
        Returns building ID
        Raises exception if user doesn't have write lock
        """
        user = self.auth_service.get_current_user()
        if not user:
            raise PermissionError("No authenticated user")
        
        # Repository will verify write lock
        return self.repository.create_building(building_data, user.id)
    
    def update_building(self, building_id: int, building_data: Dict[str, Any]) -> bool:
        """
        Update existing building
        Returns True if successful
        Raises exception if user doesn't have write lock
        """
        user = self.auth_service.get_current_user()
        if not user:
            raise PermissionError("No authenticated user")
        
        # Repository will verify write lock
        self.repository.update_building(building_id, building_data, user.id)
        return True
    
    def delete_building(self, building_id: int) -> bool:
        """
        Delete building
        Returns True if successful
        Raises exception if user doesn't have write lock
        """
        user = self.auth_service.get_current_user()
        if not user:
            raise PermissionError("No authenticated user")
        
        # Repository will verify write lock
        self.repository.delete_building(building_id, user.id)
        return True
    
    def search_buildings(self, search_term: str) -> List[Building]:
        """Search buildings by name, address, or city"""
        all_buildings = self.get_all_buildings()
        search_lower = search_term.lower()
        
        return [
            building for building in all_buildings
            if (search_lower in building.name.lower() or
                (building.address and search_lower in building.address.lower()) or
                (building.city and search_lower in building.city.lower()))
        ]
    
    def get_building_statistics(self) -> Dict[str, Any]:
        """Get statistics about all buildings"""
        buildings = self.get_all_buildings()
        
        return {
            'total_buildings': len(buildings),
            'total_units': sum(b.total_units for b in buildings),
            'buildings_by_city': self._group_by_city(buildings)
        }
    
    def _group_by_city(self, buildings: List[Building]) -> Dict[str, int]:
        """Group buildings by city"""
        city_counts = {}
        for building in buildings:
            city = building.city or 'Unknown'
            city_counts[city] = city_counts.get(city, 0) + 1
        return city_counts
