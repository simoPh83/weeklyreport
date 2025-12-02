"""
Building Form Dialog
Loads building_form.ui for adding/editing buildings
"""
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import QDate
from pathlib import Path
from datetime import date


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
            self.setWindowTitle("Edit Property")
            self.load_building_data()
        else:
            self.setWindowTitle("Add New Property")
        
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
                self.propertyCodeEdit.setText(building.property_code)
                self.propertyNameEdit.setText(building.property_name or '')
                self.propertyAddressEdit.setText(building.property_address or '')
                self.postcodeEdit.setText(building.postcode or '')
                self.clientCodeEdit.setText(building.client_code or '')
                
                # Handle acquisition date
                if building.acquisition_date:
                    qdate = QDate(
                        building.acquisition_date.year,
                        building.acquisition_date.month,
                        building.acquisition_date.day
                    )
                    self.acquisitionDateEdit.setDate(qdate)
                else:
                    self.acquisitionDateEdit.setDate(QDate())  # NULL date
                
                # Handle disposal date
                if building.disposal_date:
                    qdate = QDate(
                        building.disposal_date.year,
                        building.disposal_date.month,
                        building.disposal_date.day
                    )
                    self.disposalDateEdit.setDate(qdate)
                else:
                    self.disposalDateEdit.setDate(QDate())  # NULL date
                
                self.notesEdit.setPlainText(building.notes or '')
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load property data: {str(e)}")
            self.reject()
    
    def handle_save(self):
        """Validate and save building data"""
        # Validate required fields
        property_code = self.propertyCodeEdit.text().strip()
        property_address = self.propertyAddressEdit.text().strip()
        postcode = self.postcodeEdit.text().strip()
        client_code = self.clientCodeEdit.text().strip()
        
        if not property_code:
            QMessageBox.warning(self, "Validation Error", "Property code is required.")
            self.propertyCodeEdit.setFocus()
            return
        
        if len(property_code) != 6 or not property_code.isdigit():
            QMessageBox.warning(self, "Validation Error", "Property code must be 6 digits.")
            self.propertyCodeEdit.setFocus()
            return
        
        if not property_address:
            QMessageBox.warning(self, "Validation Error", "Property address is required.")
            self.propertyAddressEdit.setFocus()
            return
        
        if not postcode:
            QMessageBox.warning(self, "Validation Error", "Postcode is required.")
            self.postcodeEdit.setFocus()
            return
        
        if not client_code:
            QMessageBox.warning(self, "Validation Error", "Client code is required.")
            self.clientCodeEdit.setFocus()
            return
        
        # Collect data
        data = {
            'property_code': property_code,
            'property_name': self.propertyNameEdit.text().strip() or None,
            'property_address': property_address,
            'postcode': postcode,
            'client_code': client_code,
            'notes': self.notesEdit.toPlainText().strip() or None
        }
        
        # Handle acquisition date
        acq_qdate = self.acquisitionDateEdit.date()
        if acq_qdate.isNull():
            data['acquisition_date'] = None
        else:
            data['acquisition_date'] = date(acq_qdate.year(), acq_qdate.month(), acq_qdate.day())
        
        # Handle disposal date
        disp_qdate = self.disposalDateEdit.date()
        if disp_qdate.isNull():
            data['disposal_date'] = None
        else:
            data['disposal_date'] = date(disp_qdate.year(), disp_qdate.month(), disp_qdate.day())
        
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
            QMessageBox.critical(self, "Error", f"Failed to save property: {str(e)}")
