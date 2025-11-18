# Property Management System

A PyQt6-based desktop application for managing commercial properties with multi-user support, database locking, and modern dark/light themes.

## Features
- **Multi-user support** with login system (no authentication required)
- **Visual database path configuration** with automatic saving
- **Shared SQLite database** on LAN drive with hybrid locking
- **Modern UI themes** - dark, light, or auto (follows system)
- **Read-only mode** when database is locked by another user
- **10-minute auto-timeout** with automatic session cleanup
- **Admin force-unlock** capability
- **Audit logging** for all data changes
- **Buildings and Units management** with full CRUD operations

## Quick Start

### Running from Source

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **First run:** Select database location when prompted
   - For testing: Use suggested default path
   - For production: Browse to network share (e.g., `\\SERVER\Share\property.db`)

4. **Login:** Select a user (admin, user1, or user2)

The database location is saved automatically for future sessions.

### Building Executable

See **[guides/BUILD_README.md](guides/BUILD_README.md)** for instructions on creating standalone executables.

## Project Structure

```
weeklyreport/
├── main.py                 # Application entry point
├── config.py              # Configuration (deprecated - uses dynamic path now)
├── requirements.txt       # Python dependencies
│
├── core/                  # Core business logic
│   └── lock_manager.py    # Hybrid locking system
│
├── database/              # Database layer
│   └── db_manager.py      # All database operations
│
├── gui/                   # User interface
│   ├── login_dialog.py
│   ├── main_window.py
│   ├── building_form.py
│   ├── unit_form.py
│   └── db_path_dialog.py
│
├── ui/                    # Qt Designer files (.ui)
│   ├── login_dialog.ui
│   ├── main_window.ui
│   ├── building_form.ui
│   └── unit_form.ui
│
├── utils/                 # Utility modules
│   ├── db_path_manager.py # Path persistence
│   └── helpers.py         # Utility functions
│
├── tests/                 # Test files
│   ├── test_system.py
│   ├── test_force_unlock.py
│   ├── test_centralized_lock.py
│   └── test_gui_lock_lost.py
│
└── guides/                # Documentation
    ├── START_HERE.md
    ├── ARCHITECTURE.md
    ├── BUILD_INSTRUCTIONS.md
    └── DATABASE_PATH_GUIDE.md
```

## Documentation

- **[guides/START_HERE.md](guides/START_HERE.md)** - Development setup and workflow
- **[guides/ARCHITECTURE.md](guides/ARCHITECTURE.md)** - System design and components
- **[guides/DATABASE_PATH_GUIDE.md](guides/DATABASE_PATH_GUIDE.md)** - Database configuration
- **[guides/BUILD_INSTRUCTIONS.md](guides/BUILD_INSTRUCTIONS.md)** - Creating executables

## Changing Database Location

While the application is running:
- **File → Change Database Path...** menu option
- Select new location and confirm restart

Or manually clear saved path:
```bash
python -c "from utils import clear_database_path; clear_database_path()"
```

## Requirements

- Python 3.8+
- PyQt6
- qdarktheme (for modern UI)
- SQLite3 (included with Python)

## License

[Your License Here]


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
