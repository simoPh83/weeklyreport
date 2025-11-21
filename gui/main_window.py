"""  
Main Window
Loads main_window.ui and manages the main application interface
"""
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView, QProgressBar, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from pathlib import Path

from .building_form import BuildingFormDialog
from .unit_form import UnitFormDialog
from .db_path_dialog import DatabasePathDialog
from utils import save_database_path


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signal to safely handle lock lost from background thread
    lock_lost_signal = pyqtSignal(int)
    
    def __init__(self, auth_service, building_service, unit_service, current_user, db_path, parent=None):
        super().__init__(parent)
        
        self.auth_service = auth_service
        self.building_service = building_service
        self.unit_service = unit_service
        self.current_user = current_user
        self.db_path = db_path
        self.is_read_only = False
        
        # Load UI file
        ui_path = Path(__file__).parent.parent / 'ui' / 'main_window.ui'
        uic.loadUi(ui_path, self)
        
        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Load data
        self.refresh_all_data()
        
        # Setup status check timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_lock_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        
        # Connect lock lost signal (must be connected before setting callback)
        self.lock_lost_signal.connect(self.handle_lock_lost_ui)
        
        # Register lock lost callback (if using LocalRepository)
        try:
            from repositories import LocalRepository
            repository = self.auth_service.repository
            if isinstance(repository, LocalRepository):
                repository.lock_manager.set_lock_lost_callback(self.on_lock_lost_thread)
        except Exception:
            pass  # API mode or other repository
    
    def setup_ui(self):
        """Setup UI elements"""
        # Update user label
        self.userLabel.setText(f"User: {self.current_user['display_name']}")
        
        # Update window title with database path
        db_name = Path(self.db_path).name
        self.setWindowTitle(f"Weekly Report - {db_name}")
        
        # Setup tables
        self.setup_buildings_table()
        self.setup_units_table()
        self.setup_audit_table()
        
        # Check initial lock status
        self.check_lock_status()
    
    def connect_signals(self):
        """Connect UI signals to slots"""
        # Buildings tab
        self.addBuildingButton.clicked.connect(self.add_building)
        self.editBuildingButton.clicked.connect(self.edit_building)
        self.deleteBuildingButton.clicked.connect(self.delete_building)
        self.refreshBuildingsButton.clicked.connect(self.refresh_buildings)
        
        # Units tab
        self.addUnitButton.clicked.connect(self.add_unit)
        self.editUnitButton.clicked.connect(self.edit_unit)
        self.deleteUnitButton.clicked.connect(self.delete_unit)
        self.refreshUnitsButton.clicked.connect(self.refresh_units)
        
        # Audit tab
        self.refreshAuditButton.clicked.connect(self.refresh_audit)
        
        # Menu actions
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionRefresh.triggered.connect(self.refresh_all_data)
        self.actionForceUnlock.triggered.connect(self.force_unlock)
        
        # Add change database path action if it doesn't exist
        if not hasattr(self, 'actionChangeDatabasePath'):
            from PyQt6.QtGui import QAction
            self.actionChangeDatabasePath = QAction("Change Database Path...", self)
            self.actionChangeDatabasePath.triggered.connect(self.change_database_path)
            # Insert before the separator before Force Unlock
            actions = self.menuFile.actions()
            for i, action in enumerate(actions):
                if action.text() == "Force Unlock Database (Admin)":
                    self.menuFile.insertAction(action, self.actionChangeDatabasePath)
                    break
        
        # Custom sorting for occupancy column (column 7) - descending first
        self.buildingsTable.horizontalHeader().sectionClicked.connect(self.on_building_header_clicked)
        self.last_occupancy_sort_order = None
    
    def setup_buildings_table(self):
        """Setup buildings table"""
        self.buildingsTable.setColumnCount(8)
        self.buildingsTable.setHorizontalHeaderLabels([
            'ID', 'Name', 'Address', 'City', 'State', 'Zip Code', 'Total Units', 'Occupancy %'
        ])
        self.buildingsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.buildingsTable.setColumnHidden(0, True)  # Hide ID column
        
        # Make table read-only
        self.buildingsTable.setEditTriggers(self.buildingsTable.EditTrigger.NoEditTriggers)
        
        # Enable sorting
        self.buildingsTable.setSortingEnabled(True)
    
    def setup_units_table(self):
        """Setup units table"""
        self.unitsTable.setColumnCount(9)
        self.unitsTable.setHorizontalHeaderLabels([
            'ID', 'Building', 'Unit Number', 'Floor', 'Type', 
            'Sq Ft', 'Rent', 'Status', 'Tenant'
        ])
        self.unitsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.unitsTable.setColumnHidden(0, True)  # Hide ID column
        
        # Make table read-only
        self.unitsTable.setEditTriggers(self.unitsTable.EditTrigger.NoEditTriggers)
        
        # Enable sorting
        self.unitsTable.setSortingEnabled(True)
    
    def setup_audit_table(self):
        """Setup audit log table"""
        self.auditTable.setColumnCount(5)
        self.auditTable.setHorizontalHeaderLabels([
            'Timestamp', 'User', 'Action', 'Table', 'Record ID'
        ])
        self.auditTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Make table read-only
        self.auditTable.setEditTriggers(self.auditTable.EditTrigger.NoEditTriggers)
        
        # Enable sorting
        self.auditTable.setSortingEnabled(True)
    
    def on_building_header_clicked(self, logical_index: int):
        """Handle building table header clicks for custom occupancy sorting"""
        if logical_index == 7:  # Occupancy column
            # Disable default sorting temporarily
            self.buildingsTable.setSortingEnabled(False)
            
            # Determine sort order: start with descending, then toggle
            if self.last_occupancy_sort_order == Qt.SortOrder.DescendingOrder:
                order = Qt.SortOrder.AscendingOrder
            else:
                order = Qt.SortOrder.DescendingOrder
            
            self.last_occupancy_sort_order = order
            self.buildingsTable.sortItems(7, order)
            
            # Re-enable sorting
            self.buildingsTable.setSortingEnabled(True)
    
    def check_lock_status(self):
        """Check database lock status and update UI"""
        has_write_lock = self.auth_service.verify_write_lock()
        
        if has_write_lock:
            # Has write lock
            self.is_read_only = False
            self.lockStatusLabel.setText("Database Status: Read-Write")
            self.lockStatusLabel.setStyleSheet("color: green; font-weight: bold;")
            self.enable_edit_buttons(True)
        else:
            # Read-only mode
            lock_info = self.auth_service.get_write_lock_info()
            if lock_info:
                holder_name = lock_info.username
                self.lockStatusLabel.setText(f"Database Status: Read-Only (Locked by {holder_name})")
            else:
                self.lockStatusLabel.setText("Database Status: Read-Only")
            self.lockStatusLabel.setStyleSheet("color: orange; font-weight: bold;")
            self.enable_edit_buttons(False)
            self.is_read_only = True
    
    def enable_edit_buttons(self, enabled: bool):
        """Enable or disable edit buttons based on lock status"""
        # Buildings
        self.addBuildingButton.setEnabled(enabled)
        self.editBuildingButton.setEnabled(enabled)
        self.deleteBuildingButton.setEnabled(enabled)
        
        # Units
        self.addUnitButton.setEnabled(enabled)
        self.editUnitButton.setEnabled(enabled)
        self.deleteUnitButton.setEnabled(enabled)
    
    def on_lock_lost_thread(self, session_id):
        """
        Called from background thread when lock is lost.
        Emits signal to handle UI updates in main thread.
        """
        # Emit signal to handle in main thread - Qt signals are thread-safe
        self.lock_lost_signal.emit(session_id)
    
    def handle_lock_lost_ui(self, session_id):
        """
        Called in main GUI thread when lock is lost.
        Safe to update UI elements here.
        """
        # Update to read-only mode immediately
        self.is_read_only = True
        self.lockStatusLabel.setText("Database Status: Read-Only (Lock was removed by administrator)")
        self.lockStatusLabel.setStyleSheet("color: red; font-weight: bold;")
        self.enable_edit_buttons(False)
        
        # Show warning to user
        QMessageBox.warning(
            self,
            "Lock Lost",
            "Your write access has been revoked by an administrator.\n\n"
            "The database is now in read-only mode.\n"
            "Any unsaved changes in open dialogs will not be saved.",
            QMessageBox.StandardButton.Ok
        )
    
    def refresh_all_data(self):
        """Refresh all data tables"""
        self.refresh_buildings()
        self.refresh_units()
        self.refresh_audit()
    
    def refresh_buildings(self):
        """Refresh buildings table"""
        try:
            # Disable sorting while populating data
            self.buildingsTable.setSortingEnabled(False)
            
            buildings = self.building_service.get_all_buildings()
            
            self.buildingsTable.setRowCount(0)
            for building in buildings:
                row = self.buildingsTable.rowCount()
                self.buildingsTable.insertRow(row)
                
                self.buildingsTable.setItem(row, 0, QTableWidgetItem(str(building.id)))
                self.buildingsTable.setItem(row, 1, QTableWidgetItem(building.name))
                self.buildingsTable.setItem(row, 2, QTableWidgetItem(building.address or ''))
                self.buildingsTable.setItem(row, 3, QTableWidgetItem(building.city or ''))
                self.buildingsTable.setItem(row, 4, QTableWidgetItem(building.state or ''))
                self.buildingsTable.setItem(row, 5, QTableWidgetItem(building.zip_code or ''))
                self.buildingsTable.setItem(row, 6, QTableWidgetItem(str(building.notes or '')))
                
                # Add occupancy percentage with progress bar
                occupancy_value = building.occupancy if building.occupancy is not None else 0.0
                
                # Create a sortable item with numeric value for sorting
                occupancy_item = QTableWidgetItem()
                occupancy_item.setData(Qt.ItemDataRole.DisplayRole, occupancy_value)
                self.buildingsTable.setItem(row, 7, occupancy_item)
                
                # Add visual progress bar widget on top
                progress_widget = self.create_progress_bar(occupancy_value)
                self.buildingsTable.setCellWidget(row, 7, progress_widget)
            
            # Re-enable sorting
            self.buildingsTable.setSortingEnabled(True)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh buildings: {str(e)}")
    
    def create_progress_bar(self, percentage: float) -> QWidget:
        """Create a progress bar widget for occupancy display"""
        # Container widget
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        
        # Progress bar
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(int(percentage))
        progress.setFormat(f"{percentage:.1f}%")
        progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Color based on occupancy level
        if percentage >= 90:
            color = "#4caf50"  # Green - excellent
        elif percentage >= 75:
            color = "#8bc34a"  # Light green - good
        elif percentage >= 50:
            color = "#ffc107"  # Amber - moderate
        elif percentage >= 25:
            color = "#ff9800"  # Orange - low
        else:
            color = "#f44336"  # Red - very low
        
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                background-color: #2b2b2b;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
        
        layout.addWidget(progress)
        return container
    
    def refresh_units(self):
        """Refresh units table"""
        try:
            # Disable sorting while populating data
            self.unitsTable.setSortingEnabled(False)
            
            units = self.unit_service.get_all_units()
            
            self.unitsTable.setRowCount(0)
            for unit in units:
                row = self.unitsTable.rowCount()
                self.unitsTable.insertRow(row)
                
                self.unitsTable.setItem(row, 0, QTableWidgetItem(str(unit.id)))
                self.unitsTable.setItem(row, 1, QTableWidgetItem(unit.building_name or ''))
                self.unitsTable.setItem(row, 2, QTableWidgetItem(unit.unit_number))
                self.unitsTable.setItem(row, 3, QTableWidgetItem(str(unit.floor) if unit.floor else ''))
                self.unitsTable.setItem(row, 4, QTableWidgetItem(unit.unit_type or 'Office'))
                
                # Square feet - store numeric value for sorting, display formatted text
                sqft_item = QTableWidgetItem()
                if unit.square_feet:
                    sqft_item.setData(Qt.ItemDataRole.DisplayRole, unit.square_feet)  # Numeric value for sorting
                    sqft_item.setText(f"{unit.square_feet:,.0f}")  # Formatted display with thousand separators
                self.unitsTable.setItem(row, 5, sqft_item)
                
                # Rent amount - store numeric value for sorting, display formatted text
                rent_item = QTableWidgetItem()
                if unit.rent_amount:
                    rent_item.setData(Qt.ItemDataRole.DisplayRole, unit.rent_amount)  # Numeric value for sorting
                    rent_item.setText(f"£{unit.rent_amount:,.2f}")  # Formatted display with thousand separators
                self.unitsTable.setItem(row, 6, rent_item)
                
                self.unitsTable.setItem(row, 7, QTableWidgetItem(unit.status or 'Vacant'))
                self.unitsTable.setItem(row, 8, QTableWidgetItem(unit.tenant_name or ''))
            
            # Re-enable sorting
            self.unitsTable.setSortingEnabled(True)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh units: {str(e)}")
    
    def refresh_audit(self):
        """Refresh audit log table"""
        try:
            # Disable sorting while populating data
            self.auditTable.setSortingEnabled(False)
            
            # Audit log still accessed through repository
            audit_log = self.auth_service.repository.get_audit_log(100)
            
            self.auditTable.setRowCount(0)
            for entry in audit_log:
                row = self.auditTable.rowCount()
                self.auditTable.insertRow(row)
                
                self.auditTable.setItem(row, 0, QTableWidgetItem(entry.get('timestamp', '')))
                self.auditTable.setItem(row, 1, QTableWidgetItem(entry.get('username', '')))
                self.auditTable.setItem(row, 2, QTableWidgetItem(entry.get('action', '')))
                self.auditTable.setItem(row, 3, QTableWidgetItem(entry.get('table_name', '')))
                self.auditTable.setItem(row, 4, QTableWidgetItem(str(entry.get('record_id', '') or '')))
            
            # Re-enable sorting
            self.auditTable.setSortingEnabled(True)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh audit log: {str(e)}")
    
    def add_building(self):
        """Show dialog to add a new building"""
        if self.is_read_only:
            QMessageBox.warning(self, "Read-Only Mode", "Cannot add buildings in read-only mode.")
            return
        
        dialog = BuildingFormDialog(self.building_service, self.current_user['id'], parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.refresh_buildings()
    
    def edit_building(self):
        """Show dialog to edit selected building"""
        if self.is_read_only:
            QMessageBox.warning(self, "Read-Only Mode", "Cannot edit buildings in read-only mode.")
            return
        
        selected_rows = self.buildingsTable.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a building to edit.")
            return
        
        row = selected_rows[0].row()
        building_id = int(self.buildingsTable.item(row, 0).text())
        
        dialog = BuildingFormDialog(self.building_service, self.current_user['id'], building_id, parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.refresh_buildings()
    
    def delete_building(self):
        """Delete selected building"""
        if self.is_read_only:
            QMessageBox.warning(self, "Read-Only Mode", "Cannot delete buildings in read-only mode.")
            return
        
        selected_rows = self.buildingsTable.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a building to delete.")
            return
        
        row = selected_rows[0].row()
        building_id = int(self.buildingsTable.item(row, 0).text())
        building_name = self.buildingsTable.item(row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete building '{building_name}'?\n\n"
            "This will also delete all units in this building.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.building_service.delete_building(building_id)
                self.refresh_buildings()
                self.refresh_units()
            except PermissionError as e:
                QMessageBox.critical(
                    self,
                    "Write Lock Lost",
                    f"{str(e)}\n\nCannot delete building."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete building: {str(e)}")
    
    def add_unit(self):
        """Show dialog to add a new unit"""
        if self.is_read_only:
            QMessageBox.warning(self, "Read-Only Mode", "Cannot add units in read-only mode.")
            return
        
        dialog = UnitFormDialog(self.unit_service, self.building_service, self.current_user['id'], parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.refresh_units()
    
    def edit_unit(self):
        """Show dialog to edit selected unit"""
        if self.is_read_only:
            QMessageBox.warning(self, "Read-Only Mode", "Cannot edit units in read-only mode.")
            return
        
        selected_rows = self.unitsTable.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a unit to edit.")
            return
        
        row = selected_rows[0].row()
        unit_id = int(self.unitsTable.item(row, 0).text())
        
        dialog = UnitFormDialog(self.unit_service, self.building_service, self.current_user['id'], unit_id, parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.refresh_units()
    
    def delete_unit(self):
        """Delete selected unit"""
        if self.is_read_only:
            QMessageBox.warning(self, "Read-Only Mode", "Cannot delete units in read-only mode.")
            return
        
        selected_rows = self.unitsTable.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a unit to delete.")
            return
        
        row = selected_rows[0].row()
        unit_id = int(self.unitsTable.item(row, 0).text())
        unit_number = self.unitsTable.item(row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete unit '{unit_number}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.unit_service.delete_unit(unit_id)
                self.refresh_units()
            except PermissionError as e:
                QMessageBox.critical(
                    self,
                    "Write Lock Lost",
                    f"{str(e)}\n\nCannot delete unit."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete unit: {str(e)}")
    
    def force_unlock(self):
        """Force unlock database (admin only)"""
        if not self.current_user.get('is_admin'):
            QMessageBox.warning(
                self,
                "Permission Denied",
                "Only administrators can force unlock the database."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Force Unlock",
            "Are you sure you want to force unlock the database?\n\n"
            "This will disconnect any user currently holding the write lock.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.auth_service.force_release_lock(self.current_user['id'], self.current_user['id'])
            if success:
                # Try to acquire write lock after forcing unlock
                lock_success, session_id = self.auth_service.acquire_write_lock(
                    self.current_user['id'],
                    self.current_user['username']
                )
                
                if lock_success:
                    QMessageBox.information(
                        self, 
                        "Success", 
                        "Database lock has been released and you now have write access."
                    )
                else:
                    QMessageBox.information(
                        self, 
                        "Success", 
                        f"Database lock has been released.\n\n"
                        f"Could not acquire write lock: {session_id}"
                    )
                
                # Update UI to reflect new lock status
                self.check_lock_status()
            else:
                QMessageBox.critical(self, "Error", "Failed to release lock.")
    
    def show_about(self):
        """Show about dialog"""
        db_name = Path(self.db_path).name
        QMessageBox.about(
            self,
            "About Weekly Report",
            "Weekly Report\n\n"
            "A multi-user property management application with:\n"
            "- Shared SQLite database\n"
            "- Hybrid locking mechanism\n"
            "- Buildings and units management\n"
            "- Audit logging\n\n"
            f"Database: {db_name}\n"
            f"Full Path: {self.db_path}\n\n"
            f"Current User: {self.current_user['display_name']}\n"
            f"Admin: {'Yes' if self.current_user.get('is_admin') else 'No'}"
        )
    
    def change_database_path(self):
        """Change database path"""
        reply = QMessageBox.question(
            self,
            "Change Database Path",
            "Changing the database path will close the application.\n"
            "You will need to log in again with the new database.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Show path selection dialog
            path_dialog = DatabasePathDialog(self.db_path, self)
            if path_dialog.exec() == path_dialog.DialogCode.Accepted:
                new_path = path_dialog.get_selected_path()
                if new_path and new_path != self.db_path:
                    # Save new path
                    save_database_path(new_path)
                    
                    QMessageBox.information(
                        self,
                        "Database Path Changed",
                        f"Database path has been updated to:\n{new_path}\n\n"
                        "The application will now close.\n"
                        "Please restart the application to use the new database."
                    )
                    
                    # Close the application
                    self.close()
                    sys.exit(0)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop status timer
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Release lock if held
        if self.auth_service.verify_write_lock():
            self.auth_service.release_write_lock(self.current_user['id'])
        
        event.accept()
