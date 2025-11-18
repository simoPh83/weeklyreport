# Property Management System

A PyQt6-based application for managing commercial properties with multi-user support and database locking.

## Features
- Multi-user login (no authentication)
- **Visual database path configuration** with automatic saving
- Shared SQLite database on LAN drive
- Hybrid locking mechanism (file + database)
- Read-only mode when database is locked by another user
- 10-minute auto-unlock on inactivity
- Admin force-unlock capability
- Audit logging for all changes
- Buildings and Units management

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. **First Run**: Select database location when prompted
   - For testing: Use suggested default path
   - For production: Browse to network share

4. The database location is saved automatically for future sessions

## Changing Database Location
4. The database location is saved automatically for future sessions

## Changing Database Location

While the application is running:
- **File → Change Database Path...** menu option
- Select new location and the app will restart

Or manually:
```bash
# Clear saved path (next run will show selector)
python -c "from utils import clear_database_path; clear_database_path()"
```

See [DATABASE_PATH_GUIDE.md](DATABASE_PATH_GUIDE.md) for details.

## Editing UI Files

The application uses Qt Designer .ui files located in the `ui/` folder. To edit them:

1. Install Qt Designer (comes with PyQt6-tools)
2. Open .ui files in Qt Designer
3. Save your changes
4. The application will automatically load the updated UI

## Architecture

- `main.py` - Application entry point
- `config.py` - Configuration settings
- `database/` - Database management and schema
- `core/` - Core business logic (lock manager)
- `ui/` - Qt Designer .ui files
- `gui/` - Python UI classes that load .ui files
- `models/` - Data models
- `utils/` - Utility functions
