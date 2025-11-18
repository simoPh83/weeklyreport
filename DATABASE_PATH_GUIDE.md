# Database Path Configuration - User Guide

## Overview

The Property Management System now allows you to configure the database location through a user-friendly dialog. The selected path is saved automatically and remembered for future sessions.

## First Run

When you run the application for the first time (or after clearing settings), you'll see the **Database Path Selection Dialog**:

![Database Path Dialog]
- **Database Path field**: Shows the suggested or current database path
- **Browse button**: Opens a file picker to select the database location
- **OK button**: Saves the path and continues to login
- **Cancel button**: Exits the application

### Suggested Default Path
The dialog suggests a default path in your home directory:
```
C:\Users\YourName\property_management.db
```

### For Network Shares
For multi-user deployments on a LAN, use paths like:
```
Windows UNC: \\SERVER\Share\property_management.db
Mapped Drive: Z:\SharedFolder\property_management.db
```

## Where Settings Are Saved

The database path is saved using the OS-appropriate application data directory:

### Windows
```
C:\Users\YourName\AppData\Roaming\PropertyManagement\settings.pkl
```

### macOS
```
~/Library/Application Support/PropertyManagement/settings.pkl
```

### Linux
```
~/.config/PropertyManagement/settings.pkl
```

## Changing the Database Path

Once the application is running, you can change the database path:

1. **Open File Menu** → **Change Database Path...**
2. You'll see a confirmation dialog warning that the app will close
3. Click **Yes** to continue
4. Select the new database location in the dialog
5. Click **OK**
6. The application will close
7. Restart the application to connect to the new database

## Database Path Information

The current database path is shown in two places:

1. **Window Title**: Shows the database filename
   ```
   Property Management System - property_management.db
   ```

2. **About Dialog** (Help → About): Shows the full path
   ```
   Database: property_management.db
   Full Path: C:\Users\simon\property_management.db
   ```

## Manual Configuration

If you need to manually reset or configure the database path:

### Option 1: Delete Settings File (Windows)
```powershell
Remove-Item "$env:APPDATA\PropertyManagement\settings.pkl"
```

### Option 2: Use Python
```python
from utils import clear_database_path
clear_database_path()
```

## Deployment Tips

### Single User / Testing
Use the default suggested path in your home directory.

### Multi-User / Production
1. Set up a network share accessible by all users
2. The first user to run the app should:
   - Click "Browse..."
   - Navigate to the network share
   - Enter filename: `property_management.db`
   - Click OK
3. All other users will see the same dialog
4. Each user independently selects the same network path

**Note**: The database path is saved per-user, not globally. Each user needs to configure their path to point to the shared database.

## Troubleshooting

### "Database is locked" immediately after changing path
- This is normal if another user already has the database open
- You'll enter read-only mode automatically

### Path saved but database not found
- Check network connectivity
- Verify the network share is accessible
- Ensure you have read/write permissions

### Want to use a different database temporarily
1. File → Change Database Path
2. Select the temporary database
3. Repeat to switch back to the original

### Settings not persisting
- Check that the AppData folder is writable
- Antivirus software may block pickle files
- Try running as administrator (Windows)

## Advanced: Scripted Deployment

For IT departments deploying to many machines, you can pre-configure the database path:

```python
# deploy_config.py
from utils import save_database_path

# Set company database path
COMPANY_DB_PATH = r"\\CompanyServer\PropertyMgmt\database.db"
save_database_path(COMPANY_DB_PATH)
print(f"Configured database path: {COMPANY_DB_PATH}")
```

Run this script on each client before users launch the app:
```powershell
python deploy_config.py
```

## Benefits of This Approach

✅ **User-Friendly**: No editing config files
✅ **Flexible**: Easy to switch between databases
✅ **OS-Agnostic**: Works on Windows, macOS, Linux
✅ **Per-User**: Each user can have different paths (useful for testing)
✅ **Persistent**: Settings saved across sessions
✅ **Secure**: Settings stored in user's private app data folder
