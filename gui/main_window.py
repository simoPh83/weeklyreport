"""  
Main Window
Loads main_window.ui and manages the main application interface
"""
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView, QProgressBar, QWidget, QHBoxLayout, QApplication, QCheckBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
from pathlib import Path
import qdarktheme

from .building_form import BuildingFormDialog
from .unit_form import UnitFormDialog
from .db_path_dialog import DatabasePathDialog
from utils import save_database_path, save_theme_preference, load_theme_preference
from config import USE_FILE_LOCK


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
        self.current_theme = load_theme_preference()  # Load saved theme preference
        
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
        # Initialize permissions flags
        self.has_permissions_write = False
        
        # Update user label
        self.userLabel.setText(f"User: {self.current_user['display_name']}")
        
        # Update window title with database path
        db_name = Path(self.db_path).name
        self.setWindowTitle(f"Weekly Report - {db_name}")
        
        # Setup tables
        self.setup_buildings_table()
        self.setup_units_table()
        self.setup_audit_table()
        self.setup_permissions_tables()
        
        # Check permissions and configure permissions tab visibility
        self.configure_permissions_tab()
        
        # Setup theme toggle button
        self.setup_theme_toggle()
        
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
        
        # Permissions tab - Set buttons will be connected in configure_permissions_tab
        
        # Menu actions
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionRefresh.triggered.connect(self.refresh_all_data)
        self.actionForceUnlock.triggered.connect(self.force_unlock)
        self.actionToggleTheme.triggered.connect(self.toggle_theme)
        
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
        self.buildingsTable.setColumnCount(9)
        self.buildingsTable.setHorizontalHeaderLabels([
            'ID', 'Property Code', 'Property Name', 'Address', 'Postcode', 'Client', 'Acquired', 'Capital Valuation (£)', 'Occupancy %'
        ])
        self.buildingsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.buildingsTable.setColumnHidden(0, True)  # Hide ID column
        
        # Make table read-only
        self.buildingsTable.setEditTriggers(self.buildingsTable.EditTrigger.NoEditTriggers)
        
        # Enable sorting
        self.buildingsTable.setSortingEnabled(True)
        
        # Fix scrollbar - apply stylesheet to ensure scrollbar starts below header
        self.buildingsTable.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget QTableCornerButton::section {
                background: palette(base);
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                width: 14px;
                margin: 0px 0px 0px 0px;
            }
        """)
    
    def setup_units_table(self):
        """Setup units table"""
        self.unitsTable.setColumnCount(5)
        self.unitsTable.setHorizontalHeaderLabels([
            'ID', 'Building', 'Unit Name', 'Sq Ft', 'Type'
        ])
        self.unitsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.unitsTable.setColumnHidden(0, True)  # Hide ID column
        
        # Make table read-only
        self.unitsTable.setEditTriggers(self.unitsTable.EditTrigger.NoEditTriggers)
        
        # Enable sorting
        self.unitsTable.setSortingEnabled(True)
        
        # Fix scrollbar - apply stylesheet to ensure scrollbar starts below header
        self.unitsTable.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget QTableCornerButton::section {
                background: palette(base);
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                width: 14px;
                margin: 0px 0px 0px 0px;
            }
        """)
    
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
        
        # Fix scrollbar - apply stylesheet to ensure scrollbar starts below header
        self.auditTable.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget QTableCornerButton::section {
                background: palette(base);
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                width: 14px;
                margin: 0px 0px 0px 0px;
            }
        """)
    
    def setup_permissions_tables(self):
        """Setup role permissions and user roles tables"""
        # Setup role permissions table
        self.rolePermissionsTable.clear()
        self.rolePermissionsTable.setEditTriggers(self.rolePermissionsTable.EditTrigger.NoEditTriggers)
        
        # Setup user roles table  
        self.userRolesTable.clear()
        self.userRolesTable.setEditTriggers(self.userRolesTable.EditTrigger.NoEditTriggers)
        
        # Apply consistent styling
        for table in [self.rolePermissionsTable, self.userRolesTable]:
            table.setStyleSheet("""
                QTableWidget {
                    gridline-color: #d0d0d0;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QTableWidget QTableCornerButton::section {
                    background: palette(base);
                    border: none;
                }
                QScrollBar:vertical {
                    border: none;
                    width: 14px;
                    margin: 0px 0px 0px 0px;
                }
            """)
    
    def configure_permissions_tab(self):
        """Configure permissions tab visibility and edit permissions based on user permissions"""
        # Check if user has view permission
        has_view = self.auth_service.is_admin() or \
                   self.auth_service.has_permission('view_users_permissions')
        
        # Find the permissions tab index
        permissions_tab_index = -1
        for i in range(self.tabWidget.count()):
            if self.tabWidget.widget(i).objectName() == 'permissionsTab':
                permissions_tab_index = i
                break
        
        # Hide/show tab based on view permission
        if permissions_tab_index >= 0:
            self.tabWidget.setTabVisible(permissions_tab_index, has_view)
        
        # If user has view permission, configure edit permissions
        if has_view:
            has_write = self.auth_service.is_admin() or \
                       self.auth_service.has_permission('write_users_permissions')
            
            # Check if user also has write lock (only if file locking is enabled)
            if USE_FILE_LOCK:
                has_write_lock = self.auth_service.verify_write_lock()
                effective_write = has_write and has_write_lock
            else:
                effective_write = has_write  # No lock check needed
            
            # Store pending changes for batch update
            self.pending_role_permission_changes = {}  # (role_id, perm_id): True/False
            self.pending_user_role_changes = {}  # (user_id, role_id): True/False
            
            # Refresh tables initially
            self.refresh_role_permissions()
            self.refresh_user_roles()
            
            # Connect Set button signals
            self.setRolePermissionsButton.clicked.connect(self.apply_role_permission_changes)
            self.setUserRolesButton.clicked.connect(self.apply_user_role_changes)
            
            # Enable/disable Set buttons based on both permission and write lock
            self.setRolePermissionsButton.setEnabled(effective_write)
            self.setUserRolesButton.setEnabled(effective_write)
            
            # Store permissions for later use (button enabling/disabling)
            self.has_permissions_write = has_write
    
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
        # If file locking is disabled, always grant write access
        if not USE_FILE_LOCK:
            self.is_read_only = False
            self.lockStatusLabel.setText("Database Status: Read-Write (File lock disabled)")
            self.lockStatusLabel.setStyleSheet("color: green; font-weight: bold;")
            self.enable_edit_buttons(True)
            return
        
        # File locking is enabled - check lock status
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
        
        # Permissions tab - only enable if user has both write lock AND write permission
        if hasattr(self, 'setRolePermissionsButton') and hasattr(self, 'setUserRolesButton'):
            has_perm_write = getattr(self, 'has_permissions_write', False)
            permissions_enabled = enabled and has_perm_write
            self.setRolePermissionsButton.setEnabled(permissions_enabled)
            self.setUserRolesButton.setEnabled(permissions_enabled)
            
            # Also disable/enable checkboxes in permissions tables
            self._update_permissions_checkboxes_state(permissions_enabled)
    
    def _update_permissions_checkboxes_state(self, enabled: bool):
        """Update enabled state of all checkboxes in permissions tables"""
        # Update role permissions table checkboxes
        if hasattr(self, 'rolePermissionsTable'):
            for row in range(self.rolePermissionsTable.rowCount()):
                for col in range(1, self.rolePermissionsTable.columnCount()):
                    widget = self.rolePermissionsTable.cellWidget(row, col)
                    if widget:
                        checkbox = widget.findChild(QCheckBox)
                        if checkbox:
                            checkbox.setEnabled(enabled)
        
        # Update user roles table checkboxes
        if hasattr(self, 'userRolesTable'):
            for row in range(self.userRolesTable.rowCount()):
                for col in range(2, self.userRolesTable.columnCount()):
                    widget = self.userRolesTable.cellWidget(row, col)
                    if widget:
                        checkbox = widget.findChild(QCheckBox)
                        if checkbox:
                            checkbox.setEnabled(enabled)
    
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
        
        # Only refresh permissions if tab is visible
        if hasattr(self, 'has_permissions_write'):
            self.refresh_role_permissions()
            self.refresh_user_roles()
    
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
                self.buildingsTable.setItem(row, 1, QTableWidgetItem(building.property_code))
                self.buildingsTable.setItem(row, 2, QTableWidgetItem(building.property_name or ''))
                self.buildingsTable.setItem(row, 3, QTableWidgetItem(building.property_address or ''))
                self.buildingsTable.setItem(row, 4, QTableWidgetItem(building.postcode or ''))
                self.buildingsTable.setItem(row, 5, QTableWidgetItem(building.client_code or ''))
                
                # Format acquisition date as DD/MM/YYYY
                acquired_text = ''
                if building.acquisition_date:
                    acquired_text = building.acquisition_date.strftime('%d/%m/%Y')
                self.buildingsTable.setItem(row, 6, QTableWidgetItem(acquired_text))
                
                # Add capital valuation (formatted with commas and year)
                if building.latest_valuation_amount is not None:
                    valuation_text = f"£{building.latest_valuation_amount:,.0f}"
                    if building.latest_valuation_year:
                        valuation_text += f" ({building.latest_valuation_year})"
                    valuation_item = QTableWidgetItem(valuation_text)
                    # Store numeric value for sorting
                    valuation_item.setData(Qt.ItemDataRole.UserRole, building.latest_valuation_amount)
                else:
                    valuation_item = QTableWidgetItem("N/A")
                    valuation_item.setData(Qt.ItemDataRole.UserRole, 0)
                self.buildingsTable.setItem(row, 7, valuation_item)
                
                # Add occupancy percentage with progress bar
                occupancy_value = building.occupancy if building.occupancy is not None else 0.0
                
                # Create a sortable item with numeric value for sorting
                occupancy_item = QTableWidgetItem()
                occupancy_item.setData(Qt.ItemDataRole.DisplayRole, occupancy_value)
                self.buildingsTable.setItem(row, 8, occupancy_item)
                
                # Add visual progress bar widget on top
                progress_widget = self.create_progress_bar(occupancy_value)
                self.buildingsTable.setCellWidget(row, 8, progress_widget)
            
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
        
        # Theme-aware background colors
        if self.current_theme == 'dark':
            bg_color = "#2b2b2b"
            border_color = "#555"
        else:
            bg_color = "#e0e0e0"
            border_color = "#999"
        
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 3px;
                text-align: center;
                background-color: {bg_color};
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
                self.unitsTable.setItem(row, 2, QTableWidgetItem(unit.unit_name or ''))
                
                # Square feet
                sqft_item = QTableWidgetItem()
                if unit.sq_ft:
                    sqft_item.setData(Qt.ItemDataRole.DisplayRole, unit.sq_ft)
                self.unitsTable.setItem(row, 3, sqft_item)
                
                self.unitsTable.setItem(row, 4, QTableWidgetItem(unit.unit_type_name or ''))
            
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
        if not self.auth_service.is_admin():
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
            f"Admin: {'Yes' if self.auth_service.is_admin() else 'No'}"
        )
    
    def setup_theme_toggle(self):
        """Setup theme toggle button with sun/moon icons"""
        # Create icons using Unicode characters (works without icon files)
        # Sun emoji for light theme, Moon emoji for dark theme
        self.update_theme_icon()
    
    def update_theme_icon(self):
        """Update the theme toggle button icon based on current theme"""
        if self.current_theme == 'dark':
            # Show sun icon when in dark mode (click to go to light)
            self.actionToggleTheme.setText("☀️ Light Mode")
            self.actionToggleTheme.setToolTip("Switch to Light theme")
        else:
            # Show moon icon when in light mode (click to go to dark)
            self.actionToggleTheme.setText("🌙 Dark Mode")
            self.actionToggleTheme.setToolTip("Switch to Dark theme")
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        # Switch theme
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        
        # Apply new theme
        app = QApplication.instance()
        app.setStyleSheet(qdarktheme.load_stylesheet(self.current_theme))
        
        # Save preference
        save_theme_preference(self.current_theme)
        
        # Update icon
        self.update_theme_icon()
        
        # Refresh buildings table to update progress bar colors
        self.refresh_buildings()
    
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
    
    # ==================== Permissions Management ====================
    
    def refresh_role_permissions(self):
        """Refresh role permissions table with checkboxes"""
        try:
            # Get all roles, permissions, and current mappings
            roles = self.auth_service.repository.get_all_roles()
            permissions = self.auth_service.repository.get_all_permissions()
            role_perms = self.auth_service.repository.get_role_permissions()
            
            # Create a set of (role_id, permission_id) for quick lookup
            granted = {(rp['role_id'], rp['permission_id']) for rp in role_perms}
            
            # Setup table
            self.rolePermissionsTable.setRowCount(len(roles))
            self.rolePermissionsTable.setColumnCount(len(permissions) + 1)
            
            # Set headers
            headers = ['Role'] + [p['name'] for p in permissions]
            self.rolePermissionsTable.setHorizontalHeaderLabels(headers)
            
            # Populate table
            for row, role in enumerate(roles):
                # Role name (read-only)
                role_item = QTableWidgetItem(role['name'])
                role_item.setFlags(role_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.rolePermissionsTable.setItem(row, 0, role_item)
                
                # Permission checkboxes
                for col, permission in enumerate(permissions, start=1):
                    checkbox_widget = QWidget()
                    checkbox = QCheckBox()
                    checkbox.setChecked((role['id'], permission['id']) in granted)
                    # Enable only if user has permission AND write lock (if file locking enabled)
                    if USE_FILE_LOCK:
                        has_lock = self.auth_service.verify_write_lock()
                        effective_write = getattr(self, 'has_permissions_write', False) and has_lock
                    else:
                        effective_write = getattr(self, 'has_permissions_write', False)
                    checkbox.setEnabled(effective_write)
                    
                    # Connect checkbox to track pending changes
                    checkbox.stateChanged.connect(
                        lambda state, r=role['id'], p=permission['id']: 
                        self.on_role_permission_checkbox_changed(r, p, state)
                    )
                    
                    # Center the checkbox
                    layout = QHBoxLayout(checkbox_widget)
                    layout.addWidget(checkbox)
                    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.setContentsMargins(0, 0, 0, 0)
                    
                    self.rolePermissionsTable.setCellWidget(row, col, checkbox_widget)
            
            # Resize columns
            self.rolePermissionsTable.resizeColumnsToContents()
            self.rolePermissionsTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh role permissions: {str(e)}")
    
    def on_role_permission_checkbox_changed(self, role_id: int, permission_id: int, state: int):
        """Track role permission checkbox changes for batch update"""
        is_checked = (state == Qt.CheckState.Checked.value)
        self.pending_role_permission_changes[(role_id, permission_id)] = is_checked
    
    def apply_role_permission_changes(self):
        """Apply all pending role permission changes after confirmation"""
        if not self.pending_role_permission_changes:
            QMessageBox.information(self, "No Changes", "No changes to apply.")
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Changes",
            f"You are about to apply {len(self.pending_role_permission_changes)} role permission change(s).\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Apply changes
        try:
            success_count = 0
            fail_count = 0
            
            for (role_id, permission_id), is_granted in self.pending_role_permission_changes.items():
                try:
                    if is_granted:
                        success = self.auth_service.repository.grant_role_permission(
                            role_id, permission_id, self.current_user['id']
                        )
                    else:
                        success = self.auth_service.repository.revoke_role_permission(
                            role_id, permission_id, self.current_user['id']
                        )
                    
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    print(f"Error updating role permission: {e}")
                    fail_count += 1
            
            # Clear pending changes
            self.pending_role_permission_changes.clear()
            
            # Refresh table to show actual state
            self.refresh_role_permissions()
            
            # Show result
            if fail_count == 0:
                QMessageBox.information(self, "Success", 
                    f"Successfully applied {success_count} change(s).")
            else:
                QMessageBox.warning(self, "Partial Success",
                    f"Applied {success_count} change(s), {fail_count} failed.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {str(e)}")
            self.refresh_role_permissions()
    
    def refresh_user_roles(self):
        """Refresh user roles table with checkboxes"""
        try:
            # Get all users, roles, and current assignments
            users = self.auth_service.repository.get_all_users()
            roles = self.auth_service.repository.get_all_roles()
            user_roles = self.auth_service.repository.get_user_roles()
            
            # Create a set of (user_id, role_id) for quick lookup
            assigned = {(ur['user_id'], ur['role_id']) for ur in user_roles}
            
            # Setup table
            self.userRolesTable.setRowCount(len(users))
            self.userRolesTable.setColumnCount(len(roles) + 2)
            
            # Set headers
            headers = ['Username', 'Display Name'] + [r['name'] for r in roles]
            self.userRolesTable.setHorizontalHeaderLabels(headers)
            
            # Populate table
            for row, user in enumerate(users):
                # Username (read-only)
                username_item = QTableWidgetItem(user['username'])
                username_item.setFlags(username_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.userRolesTable.setItem(row, 0, username_item)
                
                # Display name (read-only)
                display_item = QTableWidgetItem(user['display_name'])
                display_item.setFlags(display_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.userRolesTable.setItem(row, 1, display_item)
                
                # Role checkboxes
                for col, role in enumerate(roles, start=2):
                    checkbox_widget = QWidget()
                    checkbox = QCheckBox()
                    checkbox.setChecked((user['id'], role['id']) in assigned)
                    # Enable only if user has permission AND write lock (if file locking enabled)
                    if USE_FILE_LOCK:
                        has_lock = self.auth_service.verify_write_lock()
                        effective_write = getattr(self, 'has_permissions_write', False) and has_lock
                    else:
                        effective_write = getattr(self, 'has_permissions_write', False)
                    checkbox.setEnabled(effective_write)
                    
                    # Connect checkbox to track pending changes
                    checkbox.stateChanged.connect(
                        lambda state, u=user['id'], r=role['id']: 
                        self.on_user_role_checkbox_changed(u, r, state)
                    )
                    
                    # Center the checkbox
                    layout = QHBoxLayout(checkbox_widget)
                    layout.addWidget(checkbox)
                    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.setContentsMargins(0, 0, 0, 0)
                    
                    self.userRolesTable.setCellWidget(row, col, checkbox_widget)
            
            # Resize columns
            self.userRolesTable.resizeColumnsToContents()
            self.userRolesTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            self.userRolesTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh user roles: {str(e)}")
    
    def on_user_role_checkbox_changed(self, user_id: int, role_id: int, state: int):
        """Track user role checkbox changes for batch update"""
        is_checked = (state == Qt.CheckState.Checked.value)
        self.pending_user_role_changes[(user_id, role_id)] = is_checked
    
    def apply_user_role_changes(self):
        """Apply all pending user role changes after confirmation"""
        if not self.pending_user_role_changes:
            QMessageBox.information(self, "No Changes", "No changes to apply.")
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Changes",
            f"You are about to apply {len(self.pending_user_role_changes)} user role change(s).\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Apply changes
        try:
            success_count = 0
            fail_count = 0
            
            for (user_id, role_id), is_assigned in self.pending_user_role_changes.items():
                try:
                    if is_assigned:
                        success = self.auth_service.repository.assign_user_role(
                            user_id, role_id, self.current_user['id']
                        )
                    else:
                        success = self.auth_service.repository.unassign_user_role(
                            user_id, role_id, self.current_user['id']
                        )
                    
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    print(f"Error updating user role: {e}")
                    fail_count += 1
            
            # Clear pending changes
            self.pending_user_role_changes.clear()
            
            # Refresh table to show actual state
            self.refresh_user_roles()
            
            # Show result
            if fail_count == 0:
                QMessageBox.information(self, "Success", 
                    f"Successfully applied {success_count} change(s).")
            else:
                QMessageBox.warning(self, "Partial Success",
                    f"Applied {success_count} change(s), {fail_count} failed.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {str(e)}")
            self.refresh_user_roles()

