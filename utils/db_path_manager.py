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


def _load_settings() -> dict:
    """Load all settings from file"""
    try:
        settings_file = get_settings_file()
        if not settings_file.exists():
            return {}
        
        with open(settings_file, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return {}


def _save_settings(settings: dict) -> bool:
    """Save all settings to file"""
    try:
        settings_file = get_settings_file()
        with open(settings_file, 'wb') as f:
            pickle.dump(settings, f)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def save_database_path(db_path: str) -> bool:
    """
    Save database path to settings file
    
    Args:
        db_path: Path to database file
        
    Returns:
        True if successful, False otherwise
    """
    settings = _load_settings()
    settings['database_path'] = db_path
    return _save_settings(settings)


def load_database_path() -> Optional[str]:
    """
    Load database path from settings file
    
    Returns:
        Database path if found, None otherwise
    """
    settings = _load_settings()
    return settings.get('database_path')


def save_theme_preference(theme: str) -> bool:
    """
    Save theme preference to settings file
    
    Args:
        theme: Theme name ('dark' or 'light')
        
    Returns:
        True if successful, False otherwise
    """
    settings = _load_settings()
    settings['theme'] = theme
    return _save_settings(settings)


def load_theme_preference() -> str:
    """
    Load theme preference from settings file
    
    Returns:
        Theme name ('dark' or 'light'), defaults to 'dark'
    """
    settings = _load_settings()
    return settings.get('theme', 'dark')


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
