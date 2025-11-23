"""
Property Management System
Main application entry point
"""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
import qdarktheme

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_repository, USE_LOCAL_MODE
from services import AuthService, BuildingService, UnitService
from gui import LoginDialog, MainWindow, DatabasePathDialog
from utils import load_database_path, save_database_path, load_theme_preference


def main():
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Weekly Report")
    app.setOrganizationName("The Langham Estate")
    
    # Apply theme based on saved preference
    theme = load_theme_preference()  # Returns 'dark' by default
    app.setStyleSheet(qdarktheme.load_stylesheet(theme))
    
    try:
        # Load or select database path
        db_path = load_database_path()
        
        # If no path saved, show path selection dialog
        if not db_path:
            path_dialog = DatabasePathDialog()
            if path_dialog.exec() != path_dialog.DialogCode.Accepted:
                return 0
            
            db_path = path_dialog.get_selected_path()
            if not db_path:
                QMessageBox.critical(None, "Error", "No database path selected")
                return 1
            
            # Save the selected path
            save_database_path(db_path)
        
        # Initialize repository (abstraction over database/lock managers)
        repository = get_repository(db_path)
        
        # Initialize services
        auth_service = AuthService(repository)
        building_service = BuildingService(repository, auth_service)
        unit_service = UnitService(repository, auth_service)
        
        # Show login dialog
        login_dialog = LoginDialog(auth_service)
        if login_dialog.exec() != login_dialog.DialogCode.Accepted:
            return 0
        
        # Get selected user
        current_user = login_dialog.get_selected_user()
        if not current_user:
            QMessageBox.critical(None, "Error", "No user selected")
            return 1
        
        # Set current user in auth service
        user_dict = current_user
        from models import User
        user_model = User(
            id=user_dict['id'],
            username=user_dict['username'],
            display_name=user_dict['display_name'],
            is_admin=user_dict['is_admin']
        )
        auth_service.set_current_user(user_model)
        
        # Try to acquire write lock via auth service
        success, session_id = auth_service.acquire_write_lock(
            user_dict['id'],
            user_dict['username']
        )
        
        if not success:
            # Show warning but continue in read-only mode
            QMessageBox.information(
                None,
                "Read-Only Mode",
                f"Could not acquire write lock:\n{session_id}\n\n"
                "You can view data but cannot make changes."
            )
        
        # Create and show main window
        main_window = MainWindow(auth_service, building_service, unit_service, current_user, db_path)
        main_window.show()
        
        # Run application
        return app.exec()
    
    except Exception as e:
        QMessageBox.critical(None, "Fatal Error", f"Application failed to start:\n{str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
