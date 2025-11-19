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

from database import DatabaseManager
from core import LockManager
from gui import LoginDialog, MainWindow, DatabasePathDialog
from utils import load_database_path, save_database_path


def main():
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Weekly Report")
    app.setOrganizationName("The Langham Estate")
    
    # Apply dark theme
    # Options: "dark", "light", or "auto" (follows system preference)
    # You can also specify theme variations like:
    # qdarktheme.load_stylesheet("dark", "rounded") for rounded corners
    app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
    
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
        
        # Initialize database manager
        db_manager = DatabaseManager(db_path)
        
        # Show login dialog
        login_dialog = LoginDialog(db_manager)
        if login_dialog.exec() != login_dialog.DialogCode.Accepted:
            return 0
        
        # Get selected user
        current_user = login_dialog.get_selected_user()
        if not current_user:
            QMessageBox.critical(None, "Error", "No user selected")
            return 1
        
        # Initialize lock manager
        lock_manager = LockManager(db_path, db_manager)
        
        # Set lock manager in database manager for write verification
        db_manager.set_lock_manager(lock_manager)
        
        # Try to acquire write lock
        success, error_msg = lock_manager.acquire_write_lock(
            current_user['id'],
            current_user['username']
        )
        
        if not success:
            # Show warning but continue in read-only mode
            QMessageBox.information(
                None,
                "Read-Only Mode",
                f"Could not acquire write lock:\n{error_msg}\n\n"
                "You can view data but cannot make changes."
            )
        
        # Create and show main window
        main_window = MainWindow(db_manager, lock_manager, current_user, db_path)
        main_window.show()
        
        # Run application
        return app.exec()
    
    except Exception as e:
        QMessageBox.critical(None, "Fatal Error", f"Application failed to start:\n{str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
