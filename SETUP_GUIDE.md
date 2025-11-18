# Property Management System - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database Path
Edit `config.py` and set the `DB_PATH` variable to your shared LAN drive location:

```python
# For Windows network share:
DB_PATH = r'\\SERVER\Share\property_management.db'

# For mapped drive:
DB_PATH = r'Z:\SharedFolder\property_management.db'

# For local testing:
DB_PATH = r'C:\PropertyManagement\property_management.db'
```

### 3. Run the Application
```bash
python main.py
```

## Default Users

The application comes with 3 default users:
- **admin** (Administrator) - Display Name: "Administrator"
- **user1** - Display Name: "User One"
- **user2** - Display Name: "User Two"

Only the admin user can force-unlock the database.

## Editing UI Files

All UI files are located in the `ui/` folder:
- `login_dialog.ui` - Login screen
- `main_window.ui` - Main application window
- `building_form.ui` - Building add/edit form
- `unit_form.ui` - Unit add/edit form

To edit these files:

### Option 1: Qt Designer (Recommended)
1. Install Qt Designer: `pip install pyqt6-tools`
2. Run Qt Designer: `pyqt6-tools designer`
3. Open the .ui file
4. Make your changes
5. Save and restart the application

### Option 2: Edit XML Directly
The .ui files are XML files and can be edited in any text editor.

## Architecture Overview

### Locking Mechanism

The application uses a **hybrid locking system**:

1. **File-based Lock**: Creates a `.lock` file next to the database
   - Contains username, machine name, timestamp
   - Serves as primary lock indicator

2. **Database-based Lock**: Stores active sessions in the `sessions` table
   - Tracks user_id, username, machine_name
   - Updates `last_heartbeat` every 30 seconds
   - Enables timeout detection

### Lock Timeout

- **Timeout Period**: 10 minutes of inactivity
- **Heartbeat Interval**: 30 seconds
- If no heartbeat is received for 10 minutes, the lock is automatically released

### Admin Force Unlock

- Only users with `is_admin = 1` can force unlock
- Removes both file and database locks
- Use in case of crashes or network issues

### Read-Only Mode

When another user has the write lock:
- Current user sees all data but cannot edit
- Status bar shows: "Database Status: Read-Only (Locked by [username])"
- All Add/Edit/Delete buttons are disabled
- Data refreshes normally

### Database Schema

**Tables:**
- `users` - User accounts
- `buildings` - Building records
- `units` - Unit records (linked to buildings)
- `sessions` - Active user sessions and locks
- `audit_log` - Audit trail of all changes

## Network Deployment

### Step 1: Set Up Shared Drive
1. Create a shared folder on your LAN server
2. Ensure all users have read/write permissions
3. Map the network drive on each client machine (optional)

### Step 2: Deploy Application
1. Copy the entire project folder to each client machine
2. Install Python and dependencies on each machine
3. Update `config.py` on each machine to point to the shared database path

### Step 3: Test
1. Start the application on Machine A
2. Log in as any user - you should get write access
3. Start the application on Machine B
4. Log in - you should see "Read-Only" status
5. Close Machine A's application
6. Within a few seconds, Machine B should automatically gain write access

## Troubleshooting

### "Database is locked" error
- Wait for the timeout (10 minutes) OR
- Have an admin use "File > Force Unlock Database"

### "Permission denied" on lock file
- Ensure the shared folder has write permissions for all users
- Check antivirus isn't blocking file creation

### UI doesn't load
- Verify `.ui` files are in the `ui/` folder
- Check that `PyQt6` is properly installed: `pip install --upgrade PyQt6`

### Heartbeat stops
- Check network connectivity
- The application will auto-timeout after 10 minutes

## Customization

### Adding New Tables
1. Add table schema to `database/db_manager.py` in `_ensure_database_exists()`
2. Add CRUD methods in `DatabaseManager` class
3. Create a new .ui form file
4. Create a Python dialog class to load the .ui file
5. Add tab/interface in `main_window.ui`

### Changing Timeout/Heartbeat
Edit values in `core/lock_manager.py`:
```python
LOCK_TIMEOUT_MINUTES = 10
HEARTBEAT_INTERVAL_SECONDS = 30
```

### Adding More Users
Option 1: Add to database initialization in `db_manager.py`
Option 2: Use a database browser (e.g., DB Browser for SQLite) to add users directly

## License & Support

This is a custom application. Contact your IT department for support.
