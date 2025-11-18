# Property Management System - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT MACHINES (Multiple)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   PyQt6 GUI Layer                         │  │
│  │  - LoginDialog: User selection                           │  │
│  │  - MainWindow: Main interface with tabs                  │  │
│  │  - BuildingFormDialog: Building CRUD                     │  │
│  │  - UnitFormDialog: Unit CRUD                             │  │
│  └────────────┬─────────────────────────────────────────────┘  │
│               │                                                  │
│  ┌────────────▼─────────────────────────────────────────────┐  │
│  │                 Business Logic Layer                      │  │
│  │  - DatabaseManager: All DB operations                    │  │
│  │  - LockManager: Hybrid locking system                    │  │
│  │  - Utils: Helper functions                               │  │
│  └────────────┬─────────────────────────────────────────────┘  │
│               │                                                  │
└───────────────┼──────────────────────────────────────────────┘
                │
                │ Network Connection (LAN/SMB)
                │
┌───────────────▼──────────────────────────────────────────────┐
│              SHARED NETWORK STORAGE                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  property_management.db         ◄─── SQLite Database           │
│  property_management.db.lock    ◄─── Lock File                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ username        │
│ display_name    │
│ is_admin        │
│ is_active       │
│ created_at      │
└────────┬────────┘
         │
         │ (created_by, updated_by)
         │
    ┌────▼─────────────┐
    │    buildings     │
    ├──────────────────┤
    │ id (PK)          │
    │ name             │
    │ address          │
    │ city             │
    │ state            │
    │ zip_code         │
    │ total_units      │
    │ notes            │
    │ created_at       │
    │ created_by (FK)  │
    │ updated_at       │
    │ updated_by (FK)  │
    └────────┬─────────┘
             │
             │ (building_id)
             │
    ┌────────▼─────────┐
    │      units       │
    ├──────────────────┤
    │ id (PK)          │
    │ building_id (FK) │
    │ unit_number      │
    │ floor            │
    │ bedrooms         │
    │ bathrooms        │
    │ square_feet      │
    │ rent_amount      │
    │ status           │
    │ tenant_name      │
    │ lease_start      │
    │ lease_end        │
    │ notes            │
    │ created_at       │
    │ created_by (FK)  │
    │ updated_at       │
    │ updated_by (FK)  │
    └──────────────────┘

┌─────────────────┐         ┌──────────────────┐
│    sessions     │         │    audit_log     │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │         │ id (PK)          │
│ user_id (FK)    │         │ user_id (FK)     │
│ username        │         │ username         │
│ session_start   │         │ action           │
│ last_heartbeat  │         │ table_name       │
│ is_write_lock   │         │ record_id        │
│ machine_name    │         │ old_values       │
└─────────────────┘         │ new_values       │
                            │ timestamp        │
                            └──────────────────┘
```

## Hybrid Locking Mechanism

### Component 1: File-Based Lock
```
Location: property_management.db.lock

Contents:
  username@machine_name
  2025-11-18T10:30:45
  user_id

Purpose:
  - Fast, OS-level lock detection
  - Visible to external tools
  - First line of defense
```

### Component 2: Database-Based Lock
```
Table: sessions

Active Lock Record:
  {
    user_id: 1,
    username: "admin",
    session_start: "2025-11-18 10:30:45",
    last_heartbeat: "2025-11-18 10:35:15",  ← Updated every 30s
    is_write_lock: 1,
    machine_name: "WORKSTATION-01"
  }

Purpose:
  - Tracks active sessions
  - Enables timeout detection
  - Provides lock holder information
  - Survives file system issues
```

## Lock Acquisition Flow

```
User starts application
         │
         ▼
Select username (LoginDialog)
         │
         ▼
Check for existing locks
         │
    ┌────┴────┐
    │         │
 Locked?    Unlocked?
    │         │
    ▼         ▼
Read-Only   Try Acquire Lock
Mode            │
    │      ┌────┴────┐
    │      │         │
    │   Success?   Failed?
    │      │         │
    │      ▼         ▼
    │   Read-Write Read-Only
    │   Mode       Mode
    │      │         │
    └──────┴─────────┘
         │
         ▼
Main Window Opens
         │
         ▼
Start Heartbeat Thread (if write lock acquired)
   └─→ Update last_heartbeat every 30s
```

## Lock Release Flow

```
User closes application
         │
         ▼
Stop heartbeat thread
         │
         ▼
Delete lock file (if exists)
         │
         ▼
Delete session record (if exists)
         │
         ▼
Application exits
```

## Lock Timeout Flow

```
Heartbeat Thread Running
         │
         ▼
Update last_heartbeat
    (every 30 seconds)
         │
    ┌────┴────┐
    │         │
 Normal?   Crashed?
    │         │
    │         ▼
    │    No heartbeat updates
    │         │
    │         ▼
    │    Wait 10 minutes
    │         │
    │         ▼
    │    Other client checks
    │         │
    │         ▼
    │    Detects stale lock
    │    (last_heartbeat > 10 min old)
    │         │
    │         ▼
    │    Auto-cleanup stale lock
    │         │
    └─────────┴──────────┐
                         │
                         ▼
                Lock becomes available
```

## Admin Force Unlock Flow

```
Admin user logged in
         │
         ▼
Menu: File > Force Unlock
         │
         ▼
Confirmation dialog
         │
    ┌────┴────┐
    │         │
 Cancel?    Confirm?
    │         │
    │         ▼
    │    Delete lock file
    │         │
    │         ▼
    │    Delete all write-lock sessions
    │         │
    └─────────┴──────────┐
                         │
                         ▼
                Success message
                         │
                         ▼
                Lock immediately available
```

## Read-Only vs Read-Write Mode

### Read-Write Mode (Has Write Lock)
```
Features:
  ✓ View all data
  ✓ Add new records
  ✓ Edit existing records
  ✓ Delete records
  ✓ Heartbeat active
  ✓ Green status indicator

UI State:
  - All CRUD buttons enabled
  - Status: "Database Status: Read-Write"
```

### Read-Only Mode (No Write Lock)
```
Features:
  ✓ View all data
  ✓ Refresh data
  ✗ Add new records
  ✗ Edit existing records
  ✗ Delete records
  ✗ No heartbeat

UI State:
  - All CRUD buttons disabled
  - Status: "Database Status: Read-Only (Locked by [user])"
  - Orange status indicator
```

## File Structure

```
weeklyreport/
│
├── main.py                 # Application entry point
├── config.py               # Configuration settings
├── utils.py                # Utility functions
├── requirements.txt        # Python dependencies
├── README.md               # Project overview
├── SETUP_GUIDE.md          # Setup instructions
│
├── ui/                     # Qt Designer .ui files
│   ├── login_dialog.ui
│   ├── main_window.ui
│   ├── building_form.ui
│   └── unit_form.ui
│
├── gui/                    # Python GUI classes
│   ├── __init__.py
│   ├── login_dialog.py     # Loads login_dialog.ui
│   ├── main_window.py      # Loads main_window.ui
│   ├── building_form.py    # Loads building_form.ui
│   └── unit_form.py        # Loads unit_form.ui
│
├── database/               # Database layer
│   ├── __init__.py
│   └── db_manager.py       # All DB operations
│
└── core/                   # Core business logic
    ├── __init__.py
    └── lock_manager.py     # Hybrid locking system
```

## Key Design Decisions

### 1. Why Hybrid Locking?
- **File lock**: Fast detection, visible externally
- **Database lock**: Survives file system issues, enables heartbeat
- **Combined**: Maximum reliability

### 2. Why No Authentication?
- Small team, trusted environment
- Simplifies deployment
- Users still tracked for audit purposes

### 3. Why SQLite Instead of Server?
- Small project scope
- No server infrastructure needed
- Simple deployment
- Works well for <10 concurrent users

### 4. Why Qt Designer .ui Files?
- Visual editing without code changes
- Separation of design and logic
- Easy for non-programmers to customize
- Professional-looking interfaces

### 5. Why 10-Minute Timeout?
- Balance between responsiveness and false timeouts
- Typical lunch break duration
- Prevents indefinite locks from crashes
- Can be adjusted in configuration

## Scaling Considerations

### Current Limitations
- Single write user at a time
- SQLite has limited concurrent write performance
- Network latency affects lock acquisition
- No conflict resolution

### When to Move to Client-Server
Consider upgrading when:
- More than 10 concurrent users
- Frequent write conflicts
- Need for real-time collaboration
- Complex business logic required
- Mobile/web access needed

### Migration Path
1. Keep same UI layer
2. Replace DatabaseManager with REST API client
3. Implement server with FastAPI/Flask
4. Use PostgreSQL/MySQL
5. Add proper authentication
6. Implement optimistic locking or transactions
