"""
Configuration settings for Property Management System
"""
from pathlib import Path
import os

# Database configuration
# Change this to your shared LAN drive path
DB_PATH = os.getenv('PM_DB_PATH', str(Path.home() / 'property_management.db'))

# You can also use a network path like:
# DB_PATH = r'\\SERVER\Share\property_management.db'
# or
# DB_PATH = r'Z:\SharedFolder\property_management.db'

# Lock configuration (defined in LockManager but can be overridden here)
LOCK_TIMEOUT_MINUTES = 10
HEARTBEAT_INTERVAL_SECONDS = 30

# UI Configuration
WINDOW_TITLE = "Property Management System"
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800

# Application Info
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Organization"
