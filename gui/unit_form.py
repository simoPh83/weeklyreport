"""  
Unit Form Dialog
Loads unit_form.ui for adding/editing units
"""
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import QDate
from pathlib import Path

from database.db_manager import DatabaseWriteError


class UnitFormDialog(QDialog):
    """Dialog for adding or editing unit information"""
    
    def __init__(self, db_manager, user_id, unit_id=None, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.user_id = user_id
        self.unit_id = unit_id
        
        # Load UI file
        ui_path = Path(__file__).parent.parent / 'ui' / 'unit_form.ui'
        uic.loadUi(ui_path, self)
        
        # Set window title
        if unit_id:
            self.setWindowTitle("Edit Unit")
        else:
            self.setWindowTitle("Add New Unit")
        
        # Load buildings into combo box
        self.load_buildings()
        
        # Load unit data if editing
        if unit_id:
            self.load_unit_data()
        
        # Connect signals
        self.buttonBox.accepted.connect(self.handle_save)
        self.buttonBox.rejected.connect(self.reject)
    
    def load_buildings(self):
        """Load buildings into combo box"""
        try:
            buildings = self.db_manager.get_all_buildings()
            
            self.buildingComboBox.clear()
            for building in buildings:
                self.buildingComboBox.addItem(building['name'], building['id'])
            
            if self.buildingComboBox.count() == 0:
                QMessageBox.warning(
                    self, 
                    "No Buildings", 
                    "Please create a building first before adding units."
                )
                self.buttonBox.button(self.buttonBox.StandardButton.Save).setEnabled(False)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load buildings: {str(e)}")
    
    def load_unit_data(self):
        """Load existing unit data for editing"""
        if not self.unit_id:
            return
        
        try:
            unit = self.db_manager.get_unit_by_id(self.unit_id)
            if unit:
                # Set building
                index = self.buildingComboBox.findData(unit.get('building_id'))
                if index >= 0:
                    self.buildingComboBox.setCurrentIndex(index)
                
                # Set basic info
                self.unitNumberEdit.setText(unit.get('unit_number', ''))
                if unit.get('floor') is not None:
                    self.floorSpinBox.setValue(unit['floor'])
                if unit.get('bedrooms') is not None:
                    self.bedroomsSpinBox.setValue(unit['bedrooms'])
                if unit.get('bathrooms') is not None:
                    self.bathroomsSpinBox.setValue(unit['bathrooms'])
                if unit.get('square_feet') is not None:
                    self.squareFeetSpinBox.setValue(unit['square_feet'])
                
                # Set financial info
                if unit.get('rent_amount') is not None:
                    self.rentSpinBox.setValue(unit['rent_amount'])
                
                # Set tenant info
                status = unit.get('status', 'Vacant')
                index = self.statusComboBox.findText(status)
                if index >= 0:
                    self.statusComboBox.setCurrentIndex(index)
                
                self.tenantNameEdit.setText(unit.get('tenant_name', '') or '')
                
                # Set dates
                if unit.get('lease_start'):
                    lease_start = QDate.fromString(unit['lease_start'], 'yyyy-MM-dd')
                    if lease_start.isValid():
                        self.leaseStartEdit.setDate(lease_start)
                
                if unit.get('lease_end'):
                    lease_end = QDate.fromString(unit['lease_end'], 'yyyy-MM-dd')
                    if lease_end.isValid():
                        self.leaseEndEdit.setDate(lease_end)
                
                # Set notes
                self.notesEdit.setPlainText(unit.get('notes', '') or '')
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load unit data: {str(e)}")
            self.reject()
    
    def handle_save(self):
        """Validate and save unit data"""
        # Validate required fields
        if self.buildingComboBox.currentIndex() < 0:
            QMessageBox.warning(self, "Validation Error", "Please select a building.")
            return
        
        if not self.unitNumberEdit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Unit number is required.")
            self.unitNumberEdit.setFocus()
            return
        
        # Collect data
        data = {
            'building_id': self.buildingComboBox.currentData(),
            'unit_number': self.unitNumberEdit.text().strip(),
            'floor': self.floorSpinBox.value() if self.floorSpinBox.value() != 0 else None,
            'bedrooms': self.bedroomsSpinBox.value() if self.bedroomsSpinBox.value() > 0 else None,
            'bathrooms': self.bathroomsSpinBox.value() if self.bathroomsSpinBox.value() > 0 else None,
            'square_feet': self.squareFeetSpinBox.value() if self.squareFeetSpinBox.value() > 0 else None,
            'rent_amount': self.rentSpinBox.value() if self.rentSpinBox.value() > 0 else None,
            'status': self.statusComboBox.currentText(),
            'tenant_name': self.tenantNameEdit.text().strip() or None,
            'lease_start': self.leaseStartEdit.date().toString('yyyy-MM-dd') if self.leaseStartEdit.date().isValid() else None,
            'lease_end': self.leaseEndEdit.date().toString('yyyy-MM-dd') if self.leaseEndEdit.date().isValid() else None,
            'notes': self.notesEdit.toPlainText().strip() or None
        }
        
        try:
            if self.unit_id:
                # Update existing unit
                self.db_manager.update_unit(self.unit_id, data, self.user_id)
            else:
                # Create new unit
                self.db_manager.create_unit(data, self.user_id)
            
            self.accept()
        
        except DatabaseWriteError as e:
            # Handle lock verification failure
            QMessageBox.critical(
                self,
                "Write Lock Lost",
                f"{str(e)}\n\nChanges cannot be saved."
            )
            self.reject()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save unit: {str(e)}")
