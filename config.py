"""
Configuration settings for Property Management System
"""
from pathlib import Path
import os


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
