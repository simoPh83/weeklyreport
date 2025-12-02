"""  
Unit Form Dialog
Loads unit_form.ui for adding/editing units
"""
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import QDate
from pathlib import Path


class UnitFormDialog(QDialog):
    """Dialog for adding or editing unit information"""
    
    def __init__(self, unit_service, building_service, user_id, unit_id=None, parent=None):
        super().__init__(parent)
        
        self.unit_service = unit_service
        self.building_service = building_service
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
        
        # Enable thousand separators for numeric fields
        self.squareFeetSpinBox.setGroupSeparatorShown(True)
        self.rentSpinBox.setGroupSeparatorShown(True)
    
    def load_buildings(self):
        """Load buildings into combo box"""
        try:
            buildings = self.building_service.get_all_buildings()
            
            self.buildingComboBox.clear()
            for building in buildings:
                self.buildingComboBox.addItem(building.name, building.id)
            
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
            unit = self.unit_service.get_unit_by_id(self.unit_id)
            if unit:
                # Set building
                index = self.buildingComboBox.findData(unit.building_id)
                if index >= 0:
                    self.buildingComboBox.setCurrentIndex(index)
                
                # Set basic info
                self.unitNumberEdit.setText(unit.unit_number)
                if unit.floor is not None:
                    self.floorSpinBox.setValue(unit.floor)
                    
                # Set unit type
                unit_type = unit.unit_type or 'Office'
                index = self.unitTypeComboBox.findText(unit_type)
                if index >= 0:
                    self.unitTypeComboBox.setCurrentIndex(index)
                    
                if unit.square_feet is not None:
                    self.squareFeetSpinBox.setValue(unit.square_feet)
                    # Format display with thousand separator
                    self.squareFeetSpinBox.setGroupSeparatorShown(True)
                
                # Set financial info
                # TODO: Update for new schema - old columns removed
                # if unit.rent_amount is not None:
                #     self.rentSpinBox.setValue(unit.rent_amount)
                #     self.rentSpinBox.setGroupSeparatorShown(True)
                
                # Set tenant info
                # TODO: Update for new schema - status column removed
                # status = unit.status or 'Vacant'
                # index = self.statusComboBox.findText(status)
                # if index >= 0:
                #     self.statusComboBox.setCurrentIndex(index)
                
                # self.tenantNameEdit.setText(unit.tenant_name or '')
                
                # Set dates
                # TODO: Update for new schema - lease dates removed
                # if unit.lease_start:
                #     lease_start = QDate.fromString(str(unit.lease_start), 'yyyy-MM-dd')
                #     if lease_start.isValid():
                #         self.leaseStartEdit.setDate(lease_start)
                
                # if unit.lease_end:
                #     lease_end = QDate.fromString(str(unit.lease_end), 'yyyy-MM-dd')
                #     if lease_end.isValid():
                #         self.leaseEndEdit.setDate(lease_end)
                
                # Set notes
                self.notesEdit.setPlainText(unit.notes or '')
        
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
            'unit_type': self.unitTypeComboBox.currentText(),
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
                self.unit_service.update_unit(self.unit_id, data)
            else:
                # Create new unit
                self.unit_service.create_unit(data)
            
            self.accept()
        
        except PermissionError as e:
            # Handle lock verification failure
            QMessageBox.critical(
                self,
                "Write Lock Lost",
                f"{str(e)}\n\nChanges cannot be saved."
            )
            self.reject()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save unit: {str(e)}")
