"""
Database Path Manager
Handles saving and loading the database path from user's app data directory
"""
import pickle
from pathlib import Path
from typing import Optional
import sys


def get_app_data_dir() -> Path:
    """
    Get the appropriate application data directory for the current OS
    
    Returns:
        Path to application data directory
    """
    if sys.platform == 'win32':
        # Windows: %APPDATA%
        app_data = Path.home() / 'AppData' / 'Roaming' / 'PropertyManagement'
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Application Support
        app_data = Path.home() / 'Library' / 'Application Support' / 'PropertyManagement'
    else:
        # Linux/Unix: ~/.config
        app_data = Path.home() / '.config' / 'PropertyManagement'
    
    # Create directory if it doesn't exist
    app_data.mkdir(parents=True, exist_ok=True)
    
    return app_data


def get_settings_file() -> Path:
    """Get path to settings file"""
    return get_app_data_dir() / 'settings.pkl'


def save_database_path(db_path: str) -> bool:
    """
    Save database path to settings file
    
    Args:
        db_path: Path to database file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        settings_file = get_settings_file()
        settings = {'database_path': db_path}
        
        with open(settings_file, 'wb') as f:
            pickle.dump(settings, f)
        
        return True
    except Exception as e:
        print(f"Error saving database path: {e}")
        return False


def load_database_path() -> Optional[str]:
    """
    Load database path from settings file
    
    Returns:
        Database path if found, None otherwise
    """
    try:
        settings_file = get_settings_file()
        
        if not settings_file.exists():
            return None
        
        with open(settings_file, 'rb') as f:
            settings = pickle.load(f)
        
        return settings.get('database_path')
    
    except Exception as e:
        print(f"Error loading database path: {e}")
        return None


def clear_database_path() -> bool:
    """
    Clear saved database path
    
    Returns:
        True if successful, False otherwise
    """
    try:
        settings_file = get_settings_file()
        
        if settings_file.exists():
            settings_file.unlink()
        
        return True
    except Exception as e:
        print(f"Error clearing database path: {e}")
        return False
