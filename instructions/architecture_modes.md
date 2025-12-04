# Architecture & Configuration Modes

## Overview
The application is designed with a flexible architecture that supports multiple deployment scenarios. Configuration is controlled via `config.py` with environment variable overrides.

## Configuration Flags

### 1. `USE_LOCAL_MODE` (Data Access Layer)
Controls **HOW** the application accesses data.

- **`True` (Current)**: Direct SQLite file access via `LocalRepository`
  - App directly reads/writes SQLite database file
  - Suitable for: Single-user, LAN shared file, development
  
- **`False` (Future)**: HTTP API access via `APIRepository`
  - App makes REST API calls to FastAPI backend
  - Backend handles database operations
  - Suitable for: Production with proper client-server architecture

**Note**: `APIRepository` is currently a stub for future implementation.

### 2. `USE_FILE_LOCK` (Concurrency Control)
Controls **WHETHER** file-based locking is enforced (only relevant when `USE_LOCAL_MODE = True`).

- **`True` (Current Production)**: File-based write locking enabled
  - Uses `LockManager` with file locks for multi-user safety
  - Prevents concurrent writes on shared LAN database
  - UI shows lock status and enforces read-only mode
  
- **`False` (Development/Future)**: File locking bypassed
  - All users get write access immediately
  - No lock status checks or enforcement
  - Suitable for: Single-user dev mode, or when using API mode

## Deployment Scenarios

### Scenario 1: Current Production (LAN Shared Database)
```python
USE_LOCAL_MODE = True   # Direct SQLite access
USE_FILE_LOCK = True    # Enforce file locking
```
**Use Case**: Multiple users accessing SQLite database on shared network drive.

### Scenario 2: Local Development
```python
USE_LOCAL_MODE = True   # Direct SQLite access
USE_FILE_LOCK = False   # No locking needed
```
**Use Case**: Single developer working on local SQLite database.

### Scenario 3: Future Production (Client-Server)
```python
USE_LOCAL_MODE = False  # API mode
USE_FILE_LOCK = False   # Not applicable (server handles concurrency)
```
**Use Case**: Production deployment with FastAPI backend + PostgreSQL/MySQL.

## Setting Configuration

### Method 1: Environment Variables (Recommended for Production)
```bash
# Windows PowerShell
$env:USE_LOCAL_MODE = "true"
$env:USE_FILE_LOCK = "true"

# Linux/Mac
export USE_LOCAL_MODE=true
export USE_FILE_LOCK=true
```

### Method 2: Edit config.py (Development)
```python
# config.py
USE_LOCAL_MODE = True
USE_FILE_LOCK = False  # Disable for local dev
```

## Migration Path to Client-Server

When ready to implement client-server architecture:

1. **Build FastAPI Backend** (not yet implemented)
   - Create REST API endpoints
   - Implement authentication with JWT
   - Add database connection to PostgreSQL/MySQL
   - Handle concurrency at database level

2. **Implement APIRepository**
   - Currently a stub in `repositories/api_repository.py`
   - Add HTTP calls using `httpx`
   - Implement WebSocket for real-time updates

3. **Switch Configuration**
   ```python
   USE_LOCAL_MODE = False
   USE_FILE_LOCK = False
   API_BASE_URL = "https://your-server.com"
   ```

4. **No Code Changes Needed**
   - All business logic uses `BaseRepository` interface
   - Repository factory in `config.py` handles switching
   - UI and services work with either implementation

## File Lock Implementation Details

When `USE_FILE_LOCK = True`, the following components are active:

- **LockManager** (`core/lock_manager.py`): File-based lock implementation
- **LocalRepository**: Wraps lock checks around database operations
- **MainWindow**: Shows lock status, enforces read-only mode
- **AuthService**: Provides lock verification methods

When `USE_FILE_LOCK = False`:
- Lock methods return success immediately
- UI always shows "Read-Write" mode
- No lock status checks performed
- All edit buttons remain enabled (subject to permissions)

## Testing Different Modes

```bash
# Test without file locking (single user dev)
$env:USE_FILE_LOCK = "false"
python main.py

# Test with file locking (production mode)
$env:USE_FILE_LOCK = "true"
python main.py

# Unset to restore default
Remove-Item Env:\USE_FILE_LOCK
```

## Future: Local Development Server

Currently, there is **no local development server** included. When implementing client-server architecture, you can:

1. Create a local FastAPI server that connects to SQLite
2. Test API mode locally before deploying
3. Use `USE_LOCAL_MODE = False` with `API_BASE_URL = "http://localhost:8000"`

This would allow testing the full client-server flow without a production deployment.
