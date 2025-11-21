"""
Configuration settings for Property Management System
"""
from pathlib import Path
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from repositories import BaseRepository


# ==================== Mode Configuration ====================

# Set to False to use API mode (FastAPI backend)
# Set to True to use local SQLite mode
USE_LOCAL_MODE = os.getenv("USE_LOCAL_MODE", "true").lower() == "true"

# Local mode settings
# DATABASE_PATH is now dynamic (set via GUI), but can be overridden
DEFAULT_DATABASE_PATH = None  # Set via DatabasePathDialog

# API mode settings (for future use)
API_BASE_URL = os.getenv("API_BASE_URL", "https://your-app.railway.app")
API_KEY = os.getenv("API_KEY", None)


# ==================== Repository Factory ====================

def get_repository(db_path: str = None) -> "BaseRepository":
    """
    Factory function to get the appropriate repository implementation
    
    Args:
        db_path: Path to SQLite database (required for local mode)
        
    Returns:
        BaseRepository implementation (LocalRepository or APIRepository)
    """
    if USE_LOCAL_MODE:
        from repositories import LocalRepository
        
        if not db_path:
            raise ValueError("db_path is required for local mode")
        
        return LocalRepository(db_path)
    else:
        from repositories import APIRepository
        
        return APIRepository(API_BASE_URL, API_KEY)


# ==================== Legacy Configuration ====================

# Lock configuration (defined in LockManager but can be overridden here)
LOCK_TIMEOUT_MINUTES = 10
HEARTBEAT_INTERVAL_SECONDS = 30

# UI Configuration
WINDOW_TITLE = "Weekly Report"
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800

# Application Info
APP_VERSION = "1.0.0"
APP_AUTHOR = "The Langham Estate"
