"""
Login Dialog
Handles user login with username and password authentication
"""
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt
from pathlib import Path


class LoginDialog(QDialog):
    """Login dialog for username and password authentication"""
    
    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        
        self.auth_service = auth_service
        self.selected_user = None
        
        # Load UI file
        ui_path = Path(__file__).parent.parent / 'ui' / 'login_dialog.ui'
        uic.loadUi(ui_path, self)
        
        # Connect signals
        self.loginButton.clicked.connect(self.handle_login)
        self.cancelButton.clicked.connect(self.reject)
        self.passwordLineEdit.returnPressed.connect(self.handle_login)
        self.usernameLineEdit.returnPressed.connect(self.handle_login)
        
        # Focus username field
        self.usernameLineEdit.setFocus()
    
    def handle_login(self):
        """Handle login button click with password authentication"""
        username = self.usernameLineEdit.text().strip()
        password = self.passwordLineEdit.text()
        
        if not username:
            QMessageBox.warning(self, "Missing Username", "Please enter your username.")
            self.usernameLineEdit.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Missing Password", "Please enter your password.")
            self.passwordLineEdit.setFocus()
            return
        
        # Authenticate user
        authenticated_user = self.auth_service.authenticate(username, password)
        
        if authenticated_user:
            # Convert User model to dict for compatibility
            self.selected_user = {
                'id': authenticated_user.id,
                'username': authenticated_user.username,
                'display_name': authenticated_user.display_name,
                'is_admin': authenticated_user.is_admin
            }
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Authentication Failed",
                "Invalid username or password. Please try again."
            )
            self.passwordLineEdit.clear()
            self.usernameLineEdit.selectAll()
            self.usernameLineEdit.setFocus()
    
    def get_selected_user(self):
        """Get the selected user"""
        return self.selected_user
