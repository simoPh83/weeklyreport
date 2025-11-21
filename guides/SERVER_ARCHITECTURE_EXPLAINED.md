# Server Architecture Deep Dive
## Understanding Client/Server, WebSockets, Sessions, and State Management

**Date:** November 2025  
**For:** Property Management System Migration (SQLite → FastAPI + Supabase)

---

## 🖥️ Single Server Process vs Multiple Clients

### The Fundamental Truth: **ONE server process, MANY concurrent connections**

```
┌─────────────────────────────────────────────────────┐
│                  Railway Cloud Server                │
│                                                      │
│  ┌────────────────────────────────────────────┐   │
│  │     FastAPI Application (Single Process)    │   │
│  │                                             │   │
│  │  Event Loop (handles concurrent requests)  │   │
│  │         ↓        ↓        ↓        ↓       │   │
│  │      Client1  Client2  Client3  Client4    │   │
│  └────────────────────────────────────────────┘   │
│                      ↓                             │
│           ┌──────────────────────┐                │
│           │  Supabase PostgreSQL  │                │
│           │  (Connection Pool)    │                │
│           └──────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

### How It Works

**Server Startup (run ONCE on Railway):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

This creates:
- ✅ **One Python process**
- ✅ **One FastAPI app instance**
- ✅ **Event loop** handling thousands of requests concurrently

**When Clients Connect:**

**Client 1 (London office, 9:00 AM):**
```python
api_repo = APIRepository("https://your-app.railway.app")
buildings = api_repo.get_buildings()  # HTTP request
```

**Server receives request:**
```python
@app.get("/api/buildings")
async def get_buildings(
    user: User = Depends(get_current_user)  # ← From JWT token
):
    # This function runs for Client 1's request
    # Other clients' requests run concurrently
    buildings = await db.query("SELECT * FROM buildings")
    return buildings
```

**Client 2 (New York office, 4:00 AM - simultaneously):**
```python
api_repo = APIRepository("https://your-app.railway.app")
units = api_repo.get_units()  # HTTP request at SAME TIME
```

**Server handles BOTH concurrently:**
```python
# Server's async event loop
async def handle_requests():
    # These run concurrently (not sequentially!)
    task1 = get_buildings(user_id=1)    # Client 1
    task2 = get_units(user_id=2)        # Client 2
    # Both execute "at the same time"
```

---

## 🎯 Stateless Server Explained

### What "Stateless" Really Means

**❌ WRONG Understanding:**
> "Server has zero memory, no data stored anywhere"

**✓ CORRECT Understanding:**
> "Server **code** doesn't keep variables between requests, but queries **databases** for state"

### Example: Login Flow

**Bad (Stateful) - Don't do this:**
```python
class BadServer:
    active_users = {}  # ← Global variable = BAD!
    
    @app.post("/api/login")
    def login(username):
        # Storing in Python memory
        self.active_users[username] = {"logged_in": True}
        # Problems:
        # - Lost if server restarts
        # - Not shared between server instances
        return {"status": "logged in"}
```

**Good (Stateless) - Do this:**
```python
@app.post("/api/login")
async def login(username: str, password: str):
    # 1. Verify credentials (from PostgreSQL)
    user = await db.query(
        "SELECT * FROM users WHERE username = ?", 
        username
    )
    
    # 2. Create session record (in PostgreSQL)
    session_id = await db.execute("""
        INSERT INTO sessions (user_id, username) 
        VALUES (?, ?)
    """, user.id, username)
    
    # 3. Generate JWT token
    token = create_jwt(user_id=user.id, session_id=session_id)
    
    # 4. Return token
    return {"token": token}
    # ← Function ends, local variables gone
    # ← But session exists in database!
```

**Next request from same user:**
```python
@app.get("/api/buildings")
async def get_buildings(token: str = Header()):
    # Server has NO memory of previous login
    # Must decode token and query database
    
    # 1. Decode JWT (who is this?)
    payload = decode_jwt(token)
    # {user_id: 1, session_id: "abc123"}
    
    # 2. Verify session still valid (query PostgreSQL)
    session = await db.query("""
        SELECT * FROM sessions 
        WHERE session_id = ?
    """, payload["session_id"])
    
    if not session or session.expired:
        raise HTTPException(401, "Session expired")
    
    # 3. Get buildings
    buildings = await db.query("SELECT * FROM buildings")
    
    return buildings
    # ← Function ends, everything forgotten again
```

### What Server Sees Per Request

```python
@app.post("/api/buildings")
async def create_building(
    building: Building,
    current_user: User = Depends(get_current_user)  # ← From JWT
):
    """
    Server perspective - NO CLIENT STATE!
    
    The server doesn't "know" about Client 1, 2, 3...
    It only sees:
    1. An HTTP request
    2. JWT token: "I'm user_id=5, username=john"
    3. The building data to create
    
    After responding, server "forgets" this request.
    """
    
    # Extract user info from token (NOT from memory!)
    user_id = current_user.id
    
    # Create building in database
    building_id = await db.create_building(building, user_id)
    
    # Send response
    return {"id": building_id, "status": "created"}
    # ← Request done, server forgets
```

---

## 🔐 Session Management: PostgreSQL + Redis

### They're COMPLEMENTARY (not alternatives!)

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │          Application Code (Stateless)               │   │
│  │                                                      │   │
│  │  Every request handler has NO memory of previous    │   │
│  │  requests. Gets all info from token/database.       │   │
│  └──────────────┬─────────────────┬────────────────────┘   │
│                 ↓                 ↓                         │
│  ┌──────────────────────┐  ┌──────────────────────┐       │
│  │   PostgreSQL         │  │  Redis (In-Memory)   │       │
│  │   (Persistent)       │  │  (Fast Cache)        │       │
│  │                      │  │                      │       │
│  │ • User accounts      │  │ • WebSocket refs     │       │
│  │ • Buildings/Units    │  │ • Active sessions    │       │
│  │ • Session records    │  │ • Temporary data     │       │
│  │ • Audit logs         │  │ • Rate limiting      │       │
│  │                      │  │                      │       │
│  │ Survives restarts ✓  │  │ Lost on restart ✗    │       │
│  └──────────────────────┘  └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### PostgreSQL (Permanent Storage)

**Purpose:** Long-term data that must survive server restarts

```sql
-- sessions table
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id INT NOT NULL,
    username VARCHAR(100),
    has_lock BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45),
    created_at TIMESTAMP,
    last_heartbeat TIMESTAMP,
    expires_at TIMESTAMP
);
```

**Usage:**
```python
@app.get("/api/lock/status")
async def get_lock_status():
    # Server has NO memory of who has lock
    # Must query database every time
    session = await db.execute("""
        SELECT * FROM sessions 
        WHERE has_lock = true
    """)
    
    if session:
        return {"locked": True, "by": session.username}
    return {"locked": False}
```

**Characteristics:**
- ✅ Persistent (survives crashes/restarts)
- ✅ ACID transactions
- ✅ Complex queries
- ❌ Slower (disk I/O, network latency)
- ❌ Can't store WebSocket objects (not serializable)

### Redis (Fast In-Memory Cache)

**Purpose:** Temporary data needing SPEED

**What is Redis?**
- In-memory key-value store (like a super-fast dictionary in RAM)
- 100x faster than PostgreSQL for simple lookups
- Optional but highly recommended
- Free tier available (Upstash, Railway, etc.)

**Storage structure:**
```python
# Redis stores (in RAM)
redis_store = {
    "session:abc123": {
        "user_id": 1,
        "username": "john",
        "websocket": <WebSocket object>,  # ← Can't store in PostgreSQL!
        "last_seen": "2025-11-21T10:30:00"
    },
    "session:def456": {
        "user_id": 2,
        "username": "jane",
        "websocket": <WebSocket object>,
        "last_seen": "2025-11-21T10:29:55"
    }
}
```

**Usage:**
```python
@app.post("/api/lock/force-unlock")
async def force_unlock():
    # 1. Update PostgreSQL (permanent record)
    await db.execute("""
        DELETE FROM sessions 
        WHERE has_lock = true
    """)
    
    # 2. Get WebSocket from Redis (fast lookup)
    session_data = await redis.get("session:abc123")
    websocket = session_data["websocket"]  # ← Why we need Redis!
    
    # 3. Push notification to client
    await websocket.send_json({"type": "lock_removed"})
    
    return {"success": True}
```

**Characteristics:**
- ✅ EXTREMELY fast (microseconds)
- ✅ Can store Python objects (WebSockets)
- ✅ Built-in expiration (auto-cleanup)
- ✅ Pub/Sub for real-time events
- ❌ Not permanent (lost on restart) ← But that's OK for WebSockets!

### Data Storage Decision Matrix

| Data Type | PostgreSQL | Redis | Python Variable |
|-----------|-----------|-------|-----------------|
| User accounts | ✓ Primary | Cache | ✗ |
| Buildings/Units | ✓ Primary | Cache | ✗ |
| Session records | ✓ Primary | - | ✗ |
| WebSocket objects | ✗ Can't | ✓ Primary | Temp only |
| Active lock status | ✓ Primary | Cache | ✗ |
| Audit logs | ✓ Primary | - | ✗ |
| Rate limiting | - | ✓ Primary | ✗ |
| Temporary data | - | ✓ Primary | ✗ |

---

## 🌐 HTTP API vs WebSockets

### HTTP API (Request/Response)

**How it works:**
```
Client                          Server
  |                               |
  |--- GET /api/buildings ------->|
  |                               | (query database)
  |<---- [building1, building2]---|
  |                               |
  | Connection CLOSED ✗           |
  |                               |
  |--- POST /api/units ---------->|
  |                               | (create unit)
  |<---- {id: 123} ---------------|
  |                               |
  | Connection CLOSED ✗           |
```

**Characteristics:**
- ✅ Simple, stateless
- ✅ Server doesn't keep connection open
- ✅ Works with firewalls/proxies
- ❌ No push notifications (must poll)
- ❌ Higher latency for real-time updates

**Example:**
```python
# Client
response = httpx.get(
    "/api/buildings",
    headers={"Authorization": f"Bearer {token}"}
)
buildings = response.json()
```

### WebSocket (Persistent Connection)

**How it works:**
```
Client                          Server
  |                               |
  |--- WS Connect --------------->|
  |<--- Connected (keep open) ----|
  |                               |
  |=== STAYS OPEN ===============|
  |                               |
  |                          (admin force-unlocks)
  |<--- {type: "lock_lost"} ------|  ← Server PUSHES to you
  |                               |
  |=== STILL OPEN ===============|
  |                               |
  |--- {type: "heartbeat"} ------>|
  |<--- {status: "ok"} -----------|
  |                               |
  |=== STAYS OPEN ===============|
```

**Characteristics:**
- ✅ Real-time bidirectional communication
- ✅ Server can push to client instantly
- ✅ No polling needed
- ✅ Lower bandwidth for frequent updates
- ⚠️ More complex to implement
- ⚠️ Requires special handling for reconnection

**Example:**
```python
# Client
async with websockets.connect("wss://api.example.com/ws") as ws:
    # Send
    await ws.send(json.dumps({"type": "heartbeat"}))
    
    # Receive
    message = await ws.receive()
    data = json.loads(message)
```

---

## 🔄 Complete Flow: Admin Force Unlock

### Initial State

**PostgreSQL (permanent):**
```sql
-- sessions table
session_id | user_id | username | has_lock | created_at
-----------+---------+----------+----------+-------------------
abc123     | 1       | john     | true     | 2025-11-21 09:00:00
```

**Redis (temporary):**
```python
{
    "session:abc123": {
        "websocket": <john's WebSocket object>,
        "last_ping": "2025-11-21 10:30:00"
    }
}
```

**Client State (john's computer):**
```python
self.current_user = User(id=1, username="john")
self.token = "eyJhbGc..."
self.session_id = "abc123"
self.has_write_lock = True
```

### Action: Admin Clicks "Force Unlock"

**Step 1: Client sends request**
```python
# Admin's computer
response = httpx.post(
    "/api/lock/force-unlock",
    headers={"Authorization": f"Bearer {admin_token}"}
)
```

**Step 2: Server processes (stateless handler)**
```python
@app.post("/api/lock/force-unlock")
async def force_unlock(current_user: User = Depends(verify_admin)):
    # Handler starts with NO knowledge of previous requests
    
    # A. Find who has lock (query PostgreSQL)
    locked_session = await db.execute("""
        SELECT session_id, user_id, username 
        FROM sessions 
        WHERE has_lock = true
    """)
    # Result: {session_id: "abc123", user_id: 1, username: "john"}
    
    # B. Remove lock from database (permanent)
    await db.execute("""
        DELETE FROM sessions 
        WHERE session_id = ?
    """, locked_session.session_id)
    
    # C. Get WebSocket from Redis (fast lookup)
    session_key = f"session:{locked_session.session_id}"
    session_data = await redis.get(session_key)
    
    if session_data and session_data.get("websocket"):
        # D. Push notification via WebSocket
        ws = session_data["websocket"]
        await ws.send_json({
            "type": "lock_removed",
            "reason": "Admin force unlock",
            "timestamp": datetime.now().isoformat()
        })
        
        # E. Clean up Redis
        await redis.delete(session_key)
    
    # F. Log audit event (PostgreSQL)
    await db.execute("""
        INSERT INTO audit_log (user_id, action, details)
        VALUES (?, 'force_unlock', ?)
    """, current_user.id, f"Unlocked {locked_session.username}")
    
    return {
        "success": True, 
        "unlocked_user": locked_session.username
    }
    # ← Handler ends, all local variables discarded
```

**Step 3: John's client receives push**
```python
# John's computer - WebSocket listener
async def listen_for_notifications():
    async for message in websocket:
        data = json.loads(message)
        
        if data["type"] == "lock_removed":
            # Update LOCAL state
            self.has_write_lock = False
            
            # Update GUI (switch to read-only mode)
            self.gui.show_read_only_mode()
            self.gui.show_notification(
                "Write access removed by administrator"
            )
```

### Final State

**PostgreSQL:**
```sql
-- sessions table (john's session deleted)
session_id | user_id | username | has_lock | created_at
-----------+---------+----------+----------+-------------------
(empty)
```

**Redis:**
```python
{
    # John's WebSocket reference removed
}
```

**Client State (john's computer):**
```python
self.has_write_lock = False  # Updated!
# GUI now showing read-only mode
```

---

## 🌊 WebSocket Implementation Details

### Client Setup

```python
# Client side (john's computer)
class APIRepository:
    async def connect_websocket(self):
        # 1. Establish WebSocket connection
        self.ws = await websockets.connect(
            "wss://your-app.railway.app/ws"
        )
        
        # 2. Authenticate
        await self.ws.send(json.dumps({
            "type": "auth",
            "token": self.jwt_token  # From login
        }))
        
        # 3. Start listener in background
        asyncio.create_task(self._listen_for_messages())
    
    async def _listen_for_messages(self):
        """Background task listening for server pushes"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                if data["type"] == "lock_removed":
                    # Update local state
                    self.has_write_lock = False
                    # Notify GUI
                    self.lock_lost_callback()
                
                elif data["type"] == "heartbeat_ack":
                    # Server confirms we're alive
                    self.last_heartbeat = datetime.now()
        
        except websockets.ConnectionClosed:
            # Handle reconnection
            await self.reconnect_websocket()
```

### Server Setup

```python
# Server side (FastAPI)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # 1. Wait for auth message
    auth_msg = await websocket.receive_json()
    token = auth_msg["token"]
    
    # 2. Verify JWT token
    try:
        payload = decode_jwt(token)
        session_id = payload["session_id"]
        user_id = payload["user_id"]
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # 3. Store WebSocket in Redis
    await redis.set(
        f"session:{session_id}",
        {
            "websocket": websocket,  # ← Key storage!
            "user_id": user_id,
            "connected_at": datetime.now().isoformat()
        },
        ex=3600  # Expire after 1 hour
    )
    
    # 4. Keep connection alive
    try:
        while True:
            # Wait for client messages
            message = await websocket.receive_json()
            
            if message["type"] == "heartbeat":
                # Update PostgreSQL
                await db.execute("""
                    UPDATE sessions 
                    SET last_heartbeat = NOW()
                    WHERE session_id = ?
                """, session_id)
                
                # Respond
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "server_time": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        # 5. Clean up when client disconnects
        await redis.delete(f"session:{session_id}")
        await db.execute("""
            DELETE FROM sessions 
            WHERE session_id = ?
        """, session_id)
```

### Push Notification Utility

```python
async def notify_user(session_id: str, message: dict):
    """
    Send message to specific user via WebSocket
    Can be called from anywhere in your code!
    """
    
    # 1. Get WebSocket from Redis
    session_data = await redis.get(f"session:{session_id}")
    
    if session_data and session_data.get("websocket"):
        # 2. Send message
        ws = session_data["websocket"]
        try:
            await ws.send_json(message)
        except Exception as e:
            # Connection died, clean up
            await redis.delete(f"session:{session_id}")
    else:
        # User not connected (offline or no WebSocket)
        # Could queue message or log for later
        logger.info(f"User {session_id} not connected, message not sent")
```

---

## ⚡ Concurrent Request Processing

### How FastAPI Handles Multiple Requests

**Example: 3 simultaneous requests**

```python
# Time: 0ms - All 3 requests arrive
# Client 1: GET /api/buildings (takes 100ms)
# Client 2: POST /api/units (takes 50ms)
# Client 3: GET /api/audit (takes 200ms)

# Server execution timeline (async/concurrent):
"""
0ms:   Start all 3 request handlers
50ms:  Client 2 response sent ✓
100ms: Client 1 response sent ✓
200ms: Client 3 response sent ✓

Total time: 200ms (concurrent)
"""

# NOT this (sequential blocking):
"""
0-100ms:   Client 1 completes (blocking others)
100-150ms: Client 2 completes (blocking Client 3)
150-350ms: Client 3 completes

Total time: 350ms (sequential) ← BAD!
"""
```

**How async/await enables this:**

```python
@app.get("/api/buildings")
async def get_buildings():
    # This is async - doesn't block other requests
    buildings = await db.query("SELECT * FROM buildings")
    # ↑ While waiting for database, server handles other requests
    return buildings

@app.post("/api/units")
async def create_unit(unit: Unit):
    # Runs concurrently with get_buildings()
    unit_id = await db.insert("INSERT INTO units ...", unit)
    return {"id": unit_id}
```

---

## 🎯 What Each Component "Knows"

### Server State (Single Server Process)

**In PostgreSQL (permanent):**
```sql
-- All users, buildings, units, sessions
SELECT * FROM users;
SELECT * FROM sessions WHERE has_lock = true;
SELECT * FROM audit_log;
```

**In Redis (temporary):**
```python
# Active WebSocket connections
{
    "session:abc123": <john's WebSocket>,
    "session:def456": <jane's WebSocket>,
    "session:ghi789": <admin's WebSocket>
}
```

**NOT in server code (stateless):**
```python
# ❌ Server does NOT have:
current_logged_in_users = []  # NO!
active_locks = {}  # NO!
user_sessions = {}  # NO!

# ✓ Server queries database each request
```

### Client State (Each Client's Memory)

**Client 1 (john's computer):**
```python
self.current_user = User(id=1, username="john")
self.token = "eyJhbGc..."  # JWT token
self.session_id = "abc123"
self.has_write_lock = True
self.buildings = [...]  # Local cache
```

**Client 2 (jane's computer - different process/machine):**
```python
self.current_user = User(id=2, username="jane")
self.token = "eyJxyz..."  # Different JWT
self.session_id = "def456"
self.has_write_lock = False
self.buildings = [...]  # Her own local cache
```

**Clients do NOT know:**
- Other users' tokens
- Other users' session IDs
- Server's internal state
- Each other's existence (server coordinates)

---

## 🖥️ Server Instances: Single vs Multiple

### What Are Instances?

Railway (and other cloud platforms) let you control how many **replicas** of your app run:

**Single Instance (1 replica):**
```
Railway runs ONE container with your FastAPI app

┌─────────────────────────────────┐
│    Railway Container (1)        │
│                                 │
│  ┌──────────────────────────┐  │
│  │   FastAPI Process        │  │
│  │   Python RAM: 512MB      │  │
│  │                          │  │
│  │   active_connections={}  │  │ ← In RAM
│  └──────────────────────────┘  │
└─────────────────────────────────┘
         ↑
    All clients connect here
```

**Multiple Instances (3 replicas - horizontal scaling):**
```
Railway runs MULTIPLE containers with load balancer

                 ┌──────────────┐
                 │ Load Balancer│
                 └──────┬───────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Container 1 │ │ Container 2 │ │ Container 3 │
│             │ │             │ │             │
│ FastAPI     │ │ FastAPI     │ │ FastAPI     │
│ RAM: 512MB  │ │ RAM: 512MB  │ │ RAM: 512MB  │
│             │ │             │ │             │
│ connections │ │ connections │ │ connections │
│ = {user1}   │ │ = {user2}   │ │ = {user3}   │
└─────────────┘ └─────────────┘ └─────────────┘
```

### Railway Configuration

**In `railway.toml`:**
```toml
[deploy]
replicas = 1  # ← Start here (single instance)

# Later for scaling:
# replicas = 3  # ← Multiple instances for high traffic
```

**Or in Railway Dashboard:**
```
Settings → Scaling → Replicas: 1
```

**Pricing:**
- 1 instance ≈ $5/month
- 3 instances ≈ 3× the cost

**Handles:**
- 1 instance: ~100-500 concurrent users
- 3 instances: ~1,000+ concurrent users

---

## 🧠 RAM Storage: The Critical Problem

### The Temptation (Looks Like It Works)

With a **single instance**, RAM appears persistent:

```python
# This LOOKS like it works:
active_users = {}  # Python dictionary in RAM

@app.post("/api/login")
async def login(user_id: int):
    active_users[user_id] = {"logged_in": True}
    return {"success": True}

@app.get("/api/check")
async def check(user_id: int):
    # This works because SAME RAM!
    if user_id in active_users:
        return {"status": "logged in"}
    return {"status": "not found"}
```

### ❌ Problem 1: Server Restarts

```python
active_users = {
    "user1": {...},
    "user2": {...},
    "user3": {...}
}  # In RAM

# Railway restarts server:
# - New deployment
# - Server crash
# - Auto-restart
# - Scale up/down

# After restart:
active_users = {}  # ← ALL DATA GONE!

# User makes request:
@app.get("/api/check")
async def check(user_id: int):
    return active_users.get(user_id)
    # ← Returns None! Users "logged out"
```

### ❌ Problem 2: Multiple Instances (Load Balancing)

```python
# Container 1 RAM (separate memory):
active_users = {"user1": {...}}

# Container 2 RAM (separate memory):
active_users = {}  # Empty!

# Flow:
# 1. Client 1 logs in → Load balancer sends to Container 1
#    → Container 1 stores in RAM
# 2. Client 1's next request → Load balancer sends to Container 2
#    → Container 2 doesn't have user1 in RAM
#    → Returns "not logged in"!
```

### ❌ Problem 3: RAM Overflow

```python
# Storing too much in RAM
active_connections = {
    "user1": <WebSocket>,
    "user2": <WebSocket>,
    # ... thousands of entries ...
}

# Memory usage:
# 1,000 users × 10KB/WebSocket = ~10MB (OK)
# 10,000 users × 10KB = ~100MB (getting big)
# 100,000 users × 10KB = ~1GB (critical!)

# Railway kills your process:
# "Error: Out of Memory"
```

---

## ✅ The Golden Rule: RAM is Temporary

### What to Store in RAM vs External Storage

**✅ Safe to Store in RAM (temporary data):**

```python
# 1. Request-scoped variables (destroyed after response)
@app.get("/api/buildings")
async def get_buildings():
    buildings = await db.query("SELECT * FROM buildings")
    # ↑ Local variable, destroyed when function returns
    return buildings

# 2. Short-lived caches (OK to rebuild)
from functools import lru_cache

@lru_cache(maxsize=100)
def get_state_name(code: str) -> str:
    # Function result cached in RAM
    # If server restarts, cache rebuilds automatically
    return STATE_MAP.get(code, "Unknown")

# 3. Configuration (reloaded on startup)
CONFIG = load_config_from_file()  # Loaded once at startup

# 4. WebSocket connections (special case - see below)
active_websockets: Dict[str, WebSocket] = {}
```

**❌ NEVER Store in RAM (persistent data):**

```python
# NO! User sessions
logged_in_users = {}

# NO! Lock state  
current_lock_holder = {"user_id": 1}

# NO! Database records
all_buildings = []

# NO! Anything that must survive restart
user_preferences = {}
```

### The Correct Pattern: External State Storage

```python
# ✅ Correct: Use PostgreSQL/Redis for state
@app.post("/api/login")
async def login(username: str, password: str):
    # 1. Verify user (from PostgreSQL)
    user = await db.query("""
        SELECT * FROM users 
        WHERE username = ?
    """, username)
    
    # 2. Create session (in PostgreSQL - survives restart!)
    session_id = str(uuid.uuid4())
    await db.execute("""
        INSERT INTO sessions (session_id, user_id, created_at)
        VALUES (?, ?, NOW())
    """, session_id, user.id)
    
    # 3. Optional: Cache in Redis for speed
    await redis.set(
        f"session:{session_id}",
        json.dumps({"user_id": user.id, "username": username}),
        ex=3600  # Auto-expire in 1 hour
    )
    
    # 4. Return JWT token (client stores this)
    token = create_jwt(session_id=session_id, user_id=user.id)
    return {"token": token}
    # ← Function ends, NO state in RAM

@app.get("/api/check")
async def check(token: str = Header()):
    # Next request can be handled by ANY instance!
    
    # 1. Decode JWT
    payload = decode_jwt(token)
    session_id = payload["session_id"]
    
    # 2. Check Redis first (fast - ~1ms)
    cached = await redis.get(f"session:{session_id}")
    if cached:
        return {"status": "logged in", "data": json.loads(cached)}
    
    # 3. Fallback to PostgreSQL (~10ms)
    session = await db.query("""
        SELECT * FROM sessions 
        WHERE session_id = ?
    """, session_id)
    
    if session:
        # Re-cache in Redis for next time
        await redis.set(f"session:{session_id}", json.dumps(dict(session)))
        return {"status": "logged in"}
    
    return {"status": "not found"}
```

**Why This Works:**
- ✅ Server restarts → Session in PostgreSQL survives
- ✅ Multiple instances → All read same PostgreSQL/Redis
- ✅ Scaling → Add instances, state is shared
- ✅ RAM overflow → Only temporary data in RAM

---

## 🌐 WebSocket Special Case

WebSocket objects **MUST** be in RAM (can't serialize), but that's acceptable:

### Single Instance Approach

```python
# This is OK for single instance:
active_websockets: Dict[str, WebSocket] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = authenticate(websocket)
    
    # Store in RAM (this instance only)
    active_websockets[session_id] = websocket
    
    try:
        while True:
            message = await websocket.receive_text()
            # Handle message
    except WebSocketDisconnect:
        # Clean up when disconnected
        del active_websockets[session_id]
```

**Why it's acceptable:**
- Clients auto-reconnect on connection loss
- WebSockets are inherently temporary (user closes app = gone)
- Connection loss detection is built-in

### Multiple Instance Approach (with Redis)

When you have multiple instances, use Redis Pub/Sub:

```python
# Instance 1 stores WebSocket in local RAM
active_websockets: Dict[str, WebSocket] = {}

# But uses Redis for coordination
redis_pubsub = redis_client.pubsub()
await redis_pubsub.subscribe("notifications")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = authenticate(websocket)
    
    # Store WebSocket locally
    active_websockets[session_id] = websocket
    
    # Register in Redis (which instance has this session)
    await redis.hset("websocket_locations", session_id, INSTANCE_ID)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        del active_websockets[session_id]
        await redis.hdel("websocket_locations", session_id)

# Push notification from anywhere:
async def notify_user(session_id: str, message: dict):
    # Check which instance has the WebSocket
    instance_id = await redis.hget("websocket_locations", session_id)
    
    # Publish to that instance
    await redis.publish(f"notify_{instance_id}", json.dumps({
        "session_id": session_id,
        "message": message
    }))

# Each instance listens for its own notifications
async def listen_for_notifications():
    async for message in redis_pubsub.listen():
        data = json.loads(message["data"])
        session_id = data["session_id"]
        
        # Check if we have this WebSocket locally
        if session_id in active_websockets:
            ws = active_websockets[session_id]
            await ws.send_json(data["message"])
```

---

## 📊 Storage Decision Matrix

| Data Type | RAM | PostgreSQL | Redis | Why |
|-----------|-----|-----------|-------|-----|
| User accounts | ✗ | ✓ Primary | Cache | Permanent |
| Buildings/Units | ✗ | ✓ Primary | Cache | Permanent |
| Session records | ✗ | ✓ Primary | Cache | Must survive restart |
| Lock status | ✗ | ✓ Primary | Cache | Shared state |
| WebSocket objects | ✓ Only | ✗ Can't | Coordinate | Not serializable |
| Audit logs | ✗ | ✓ Primary | - | Permanent |
| Request variables | ✓ Only | - | - | Function-scoped |
| Config data | ✓ Only | - | - | Reloaded on startup |
| Rate limiting | - | - | ✓ Primary | Temporary counters |
| Temp cache | ✓ OK | - | ✓ Better | Short-lived |

---

## 🚀 Practical Deployment Strategy

### Phase 2: Start Simple (Single Instance)

```toml
# railway.toml
[deploy]
replicas = 1
```

**Code approach:**
```python
# WebSockets: Simple Python dict
active_connections: Dict[str, WebSocket] = {}

# Everything else: PostgreSQL
# - User sessions → sessions table
# - Lock state → sessions table (has_lock column)
# - Buildings/Units → respective tables
```

**Pros:**
- ✅ Simple implementation
- ✅ No Redis needed yet
- ✅ Fine for 100-500 users
- ✅ Cost: ~$5-10/month

**Acceptable trade-offs:**
- ⚠️ WebSocket connections lost on restart (clients auto-reconnect)
- ⚠️ Can't scale horizontally yet

### Phase 3: Scale with Redis (Multiple Instances)

```toml
# railway.toml
[deploy]
replicas = 3  # or more as needed
```

**Add Redis:**
```python
import redis.asyncio as redis

redis_client = redis.Redis(
    host="your-redis.railway.app",
    port=6379,
    password=os.getenv("REDIS_PASSWORD")
)

# Use Redis for:
# 1. Session caching (fast lookups)
# 2. WebSocket coordination (pub/sub)
# 3. Rate limiting
# 4. Temporary data
```

**When to scale:**
- 500+ concurrent users
- Need high availability (if one instance crashes, others handle traffic)
- International audience (better response times)

**Cost:** ~$15-30/month (3 instances + Redis)

---

## 🎯 Key Takeaways

1. **Railway Controls Instances** - Set `replicas` in config
2. **RAM is Temporary** - Only for data you can lose on restart
3. **Single Instance = RAM Persists Between Requests** - But NOT across restarts!
4. **Multiple Instances = Separate RAM** - Must use external storage
5. **Best Practice** - ALWAYS use PostgreSQL/Redis for state, even with 1 instance
6. **WebSockets Exception** - OK in RAM, clients reconnect automatically
7. **Start Simple** - 1 instance, add Redis when scaling
8. **Think of RAM as a Whiteboard** - Great for temporary work, don't write permanent data

### The Golden Rule:

> **Never store anything in RAM that you're not willing to lose on server restart**

If the answer to "Can I lose this data on restart?" is NO, then use PostgreSQL.

---

## 📊 Architecture Comparison

### Current (Local Mode)

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Client 1 │     │ Client 2 │     │ Client 3 │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └────────────────┼────────────────┘
                      ↓
              ┌───────────────┐
              │ Shared Folder │
              │  SQLite + .lock│
              └───────────────┘
              
Problems:
- File lock = corruption risk
- Polling every 30 seconds
- Network drive performance
- Not cloud-ready
```

### Future (API Mode)

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Client 1 │     │ Client 2 │     │ Client 3 │
│ (London) │     │(New York)│     │ (Tokyo)  │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │ HTTP/WS         │ HTTP/WS        │ HTTP/WS
     └────────────────┼────────────────┘
                      ↓
          ┌─────────────────────┐
          │   FastAPI Server    │
          │   (Railway Cloud)   │
          └──────────┬──────────┘
                     ↓
          ┌──────────────────────┐
          │ PostgreSQL (Supabase)│
          └──────────────────────┘
          
Benefits:
- Real-time push notifications
- ACID transactions
- Cloud-scale
- Audit logging
- Automatic backups
```

---

## 🎓 Key Takeaways

1. **Single Server Process** - One FastAPI app handles all clients via event loop
2. **Stateless Handlers** - Each request is independent, queries database for state
3. **PostgreSQL** - Permanent storage (users, data, sessions)
4. **Redis** - Fast cache (WebSockets, temporary data)
5. **JWT Tokens** - Client sends identity with every request
6. **WebSockets** - Persistent connection for push notifications
7. **Async/Await** - Concurrent request processing without blocking
8. **Session Table** - Database tracks who has lock
9. **Client State** - Each client manages own state locally

---

## 📚 Further Reading

- **FastAPI**: https://fastapi.tiangolo.com/
- **WebSockets**: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
- **JWT**: https://jwt.io/introduction
- **Redis**: https://redis.io/docs/about/
- **Async Python**: https://realpython.com/async-io-python/
- **Supabase**: https://supabase.com/docs

---

**Last Updated:** November 21, 2025  
**Status:** Architecture documentation for migration planning  
**Next:** Phase 2 implementation (services + integration)
