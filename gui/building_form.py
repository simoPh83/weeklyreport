"""
Building Form Dialog
Loads building_form.ui for adding/editing buildings
"""
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from pathlib import Path


class BuildingFormDialog(QDialog):
    """Dialog for adding or editing building information"""
    
    def __init__(self, building_service, user_id, building_id=None, parent=None):
        super().__init__(parent)
        
        self.building_service = building_service
        self.user_id = user_id
        self.building_id = building_id
        
        # Load UI file
        ui_path = Path(__file__).parent.parent / 'ui' / 'building_form.ui'
        uic.loadUi(ui_path, self)
        
        # Set window title
        if building_id:
            self.setWindowTitle("Edit Building")
            self.load_building_data()
        else:
            self.setWindowTitle("Add New Building")
        
        # Connect signals
        self.buttonBox.accepted.connect(self.handle_save)
        self.buttonBox.rejected.connect(self.reject)
    
    def load_building_data(self):
        """Load existing building data for editing"""
        if not self.building_id:
            return
        
        try:
            building = self.building_service.get_building_by_id(self.building_id)
            if building:
                self.nameEdit.setText(building.name)
                self.addressEdit.setText(building.address or '')
                self.cityEdit.setText(building.city or '')
                self.stateEdit.setText(building.state or '')
                self.zipCodeEdit.setText(building.zip_code or '')
                self.totalUnitsSpinBox.setValue(0)  # total_units not in model
                self.notesEdit.setPlainText(building.notes or '')
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load building data: {str(e)}")
            self.reject()
    
    def handle_save(self):
        """Validate and save building data"""
        # Validate required fields
        if not self.nameEdit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Building name is required.")
            self.nameEdit.setFocus()
            return
        
        # Collect data
        data = {
            'name': self.nameEdit.text().strip(),
            'address': self.addressEdit.text().strip() or None,
            'city': self.cityEdit.text().strip() or None,
            'state': self.stateEdit.text().strip().upper() or None,
            'zip_code': self.zipCodeEdit.text().strip() or None,
            'total_units': self.totalUnitsSpinBox.value(),
            'notes': self.notesEdit.toPlainText().strip() or None
        }
        
        try:
            if self.building_id:
                # Update existing building
                self.building_service.update_building(self.building_id, data)
            else:
                # Create new building
                self.building_service.create_building(data)
            
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
            QMessageBox.critical(self, "Error", f"Failed to save building: {str(e)}")
