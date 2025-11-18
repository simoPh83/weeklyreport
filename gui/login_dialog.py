"""
Login Dialog
Loads login_dialog.ui and handles user login
"""
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt
from pathlib import Path


class LoginDialog(QDialog):
    """Login dialog for user selection"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.selected_user = None
        
        # Load UI file
        ui_path = Path(__file__).parent.parent / 'ui' / 'login_dialog.ui'
        uic.loadUi(ui_path, self)
        
        # Connect signals
        self.loginButton.clicked.connect(self.handle_login)
        self.cancelButton.clicked.connect(self.reject)
        
        # Load users
        self.load_users()
    
    def load_users(self):
        """Load users from database into combo box"""
        try:
            users = self.db_manager.get_all_users()
            
            self.userComboBox.clear()
            for user in users:
                self.userComboBox.addItem(user['display_name'], user)
            
            if self.userComboBox.count() == 0:
                self.statusLabel.setText("No users found in database")
                self.loginButton.setEnabled(False)
            
        except Exception as e:
            self.statusLabel.setText(f"Error loading users: {str(e)}")
            self.loginButton.setEnabled(False)
    
    def handle_login(self):
        """Handle login button click"""
        if self.userComboBox.currentIndex() < 0:
            QMessageBox.warning(self, "No User Selected", "Please select a user to continue.")
            return
        
        self.selected_user = self.userComboBox.currentData()
        self.accept()
    
    def get_selected_user(self):
        """Get the selected user"""
        return self.selected_user
