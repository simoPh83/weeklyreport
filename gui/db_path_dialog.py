"""
Database Path Selector Dialog
Allows user to browse and select database file location
"""
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from pathlib import Path


class DatabasePathDialog(QDialog):
    """Dialog for selecting database path"""
    
    def __init__(self, current_path: str = None, parent=None):
        super().__init__(parent)
        
        self.selected_path = current_path
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Select Database Location")
        self.setMinimumWidth(600)
        self.setMinimumHeight(200)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Weekly Report")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Spacing
        layout.addSpacing(20)
        
        # Info label
        info_label = QLabel(
            "Please select the weekly report database file.\n"
            "This should be accessible by all users (e.g., on a network share)."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Spacing
        layout.addSpacing(20)
        
        # Path selection row
        path_layout = QHBoxLayout()
        
        path_label = QLabel("Database Path:")
        path_layout.addWidget(path_label)
        
        self.path_edit = QLineEdit()
        if self.selected_path:
            self.path_edit.setText(self.selected_path)
        else:
            # Start in home directory (empty path or suggest location)
            self.path_edit.setPlaceholderText("Browse to select database file...")
        
        self.path_edit.setMinimumWidth(300)
        path_layout.addWidget(self.path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_database)
        path_layout.addWidget(browse_button)
        
        layout.addLayout(path_layout)
        
        # Spacing
        layout.addSpacing(10)
        
        # Help text
        help_label = QLabel(
            "Tip: The database file should already exist.\n"
            "  Network share example: \\\\SERVER\\Share\\property_management.db\n"
            "  Mapped drive example: Z:\\SharedFolder\\property_management.db"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(help_label)
        
        # Stretch
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.setMinimumWidth(100)
        ok_button.setMinimumHeight(35)
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept_path)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(100)
        cancel_button.setMinimumHeight(35)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def browse_database(self):
        """Open file dialog to browse for database location"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database File",
            self.path_edit.text(),
            "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*.*)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
    
    def accept_path(self):
        """Validate and accept the selected path"""
        path = self.path_edit.text().strip()
        
        if not path:
            QMessageBox.warning(
                self,
                "No Path Selected",
                "Please browse and select a database file."
            )
            return
        
        # Check if it's a valid path format
        try:
            path_obj = Path(path)
            
            # Check if file exists
            if not path_obj.exists():
                reply = QMessageBox.question(
                    self,
                    "Database File Not Found",
                    f"The database file does not exist:\n\n{path}\n\n"
                    f"Do you want to use this path anyway?\n"
                    f"(The database will need to be created before the application can work)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Check extension
            if not path.endswith(('.db', '.sqlite', '.sqlite3')):
                reply = QMessageBox.question(
                    self,
                    "Confirm Path",
                    f"The path doesn't have a typical database extension.\n\n"
                    f"Path: {path}\n\n"
                    f"Do you want to use this path anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            self.selected_path = path
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Invalid Path",
                f"The selected path is not valid:\n{str(e)}"
            )
    
    def get_selected_path(self) -> str:
        """Get the selected database path"""
        return self.selected_path
