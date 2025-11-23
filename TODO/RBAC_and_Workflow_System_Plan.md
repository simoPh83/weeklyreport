# Role-Based Access Control (RBAC) & Workflow System - Implementation Plan

**Date**: November 23, 2025  
**Status**: Planning Phase - Not Yet Implemented

---

## Overview

The application will support multiple user types with different roles, each having:
- Different UI interfaces (visible/hidden elements)
- Different available functionalities (enabled/disabled operations)
- Workflow-based operations requiring approval from higher-ranking users

**Goal**: Implement a clean, maintainable architecture that avoids spaghetti if/else code.

---

## Recommended Architecture

### 1. Role-Based Access Control (RBAC) System

**Core Components:**
- **Roles Table**: Define user roles (Admin, Property Manager, Accountant, Viewer, etc.)
- **Permissions Table**: Granular permissions (create_building, approve_lease, view_financials, etc.)
- **Role-Permission Mapping**: Many-to-many relationship
- **User-Role Assignment**: Users can have multiple roles

**Benefits:**
- No hardcoded if/else chains
- Easy to add new roles/permissions
- Testable and auditable

---

### 2. Declarative Permission System

Instead of scattered if/else statements, use decorators and centralized checks:

```python
# services/auth_service.py
class Permission(Enum):
    VIEW_BUILDINGS = "view_buildings"
    CREATE_BUILDING = "create_building"
    EDIT_BUILDING = "edit_building"
    DELETE_BUILDING = "delete_building"
    APPROVE_LEASE = "approve_lease"
    VIEW_FINANCIALS = "view_financials"
    MANAGE_USERS = "manage_users"
    FORCE_UNLOCK = "force_unlock"

class AuthService:
    def has_permission(self, user_id: int, permission: Permission) -> bool:
        """Check if user has specific permission"""
        # Query database for user's roles and their permissions
        pass
    
    def require_permission(self, permission: Permission):
        """Decorator for service methods"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.has_permission(self.current_user.id, permission):
                    raise PermissionDeniedError(f"User lacks {permission.value}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
```

---

### 3. UI Visibility Controller

Centralized logic to show/hide UI elements based on permissions:

```python
# gui/permission_manager.py
class UIPermissionManager:
    def __init__(self, auth_service):
        self.auth_service = auth_service
    
    def configure_ui(self, main_window):
        """Configure UI elements based on user permissions"""
        user = self.auth_service.current_user
        
        # Buildings tab
        main_window.addBuildingButton.setVisible(
            self.auth_service.has_permission(user.id, Permission.CREATE_BUILDING)
        )
        main_window.editBuildingButton.setVisible(
            self.auth_service.has_permission(user.id, Permission.EDIT_BUILDING)
        )
        # ... etc
        
        # Hide entire tabs if no permissions
        if not self.auth_service.has_any_permission(user.id, [
            Permission.VIEW_FINANCIALS, Permission.EDIT_FINANCIALS
        ]):
            main_window.tabWidget.removeTab(main_window.financialsTabIndex)
```

---

### 4. Workflow/Approval System

For operations requiring approval:

```python
# models/workflow.py
class WorkflowStatus(Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class WorkflowRequest:
    id: int
    request_type: str  # 'lease_approval', 'building_modification', etc.
    requested_by: int  # user_id
    data: dict  # JSON data of the request
    status: WorkflowStatus
    approver: Optional[int]  # user_id who can approve
    created_at: datetime
    notes: str

# Database table: workflow_requests
# Fields: id, request_type, requested_by, data (JSON), status, 
#         approver, approved_by, approved_at, notes, created_at
```

---

### 5. Proposed Database Schema

```sql
-- Roles table
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    rank INTEGER DEFAULT 0  -- Higher rank = more authority
);

-- Permissions table
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,  -- 'create_building', 'approve_lease', etc.
    description TEXT,
    category TEXT  -- 'buildings', 'units', 'financials', 'admin'
);

-- Role-Permission mapping
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id),
    permission_id INTEGER REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

-- User-Role assignment (users can have multiple roles)
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

-- Workflow requests
CREATE TABLE workflow_requests (
    id INTEGER PRIMARY KEY,
    request_type TEXT NOT NULL,  -- 'lease_approval', 'building_edit', etc.
    requested_by INTEGER REFERENCES users(id),
    data TEXT,  -- JSON
    status TEXT DEFAULT 'pending_approval',
    required_approver_role INTEGER REFERENCES roles(id),  -- Which role can approve
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    rejected_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 6. Configuration-Driven Approach

Create a YAML or JSON config file defining your RBAC structure:

```yaml
# config/rbac_config.yaml
roles:
  - name: "Super Admin"
    rank: 100
    permissions: ["*"]  # All permissions
  
  - name: "Property Manager"
    rank: 80
    permissions:
      - view_buildings
      - create_building
      - edit_building
      - view_units
      - create_unit
      - edit_unit
      - approve_lease
      - view_audit_log
  
  - name: "Accountant"
    rank: 60
    permissions:
      - view_buildings
      - view_units
      - view_financials
      - edit_financials
      - export_reports
  
  - name: "Leasing Agent"
    rank: 40
    permissions:
      - view_buildings
      - view_units
      - create_unit  # Can add new units
      - edit_unit    # Can update unit info
      - request_lease_approval  # Can submit for approval
  
  - name: "Viewer"
    rank: 10
    permissions:
      - view_buildings
      - view_units

workflows:
  lease_approval:
    requires_role: "Property Manager"
    minimum_rank: 80
    
  building_modification:
    requires_role: "Property Manager"
    minimum_rank: 80
```

---

### 7. Clean Service Layer Pattern

```python
# services/building_service.py
class BuildingService:
    def __init__(self, repository, auth_service):
        self.repository = repository
        self.auth = auth_service
    
    def create_building(self, building_data: dict) -> int:
        # Check permission
        if not self.auth.has_permission(
            self.auth.current_user.id, 
            Permission.CREATE_BUILDING
        ):
            raise PermissionDeniedError("Cannot create buildings")
        
        # Check if requires approval workflow
        if self.auth.requires_approval('building_creation'):
            # Create workflow request instead
            return self.create_approval_request(
                'building_creation', 
                building_data
            )
        
        # Otherwise, create directly
        return self.repository.create_building(building_data, self.auth.current_user.id)
```

---

## Implementation Roadmap

### Phase 1: Basic RBAC Foundation
**Tasks:**
- Create roles, permissions, and mapping tables
- Implement `has_permission()` in AuthService
- Add permission checks to critical operations
- Create migration scripts
- Extend User model to include roles
- Implement Permission enum
- Create basic RBAC config

### Phase 2: UI Permission System
**Tasks:**
- Create UIPermissionManager class
- Make buttons/tabs visible based on permissions
- Update main_window to use permission manager
- Add visual indicators for permission levels

### Phase 3: Workflow System
**Tasks:**
- Create workflow_requests table
- Implement approval dialogs
- Add "Pending Approvals" tab for managers
- Create notification system for pending approvals

### Phase 4: Advanced Features
**Tasks:**
- Audit log for permission changes
- Role delegation
- Time-based permissions
- Custom approval chains

---

## Key Principles

1. **Declarative, Not Imperative**: Define what users can do in configuration, not scattered if/else
2. **Database-Driven**: Roles and permissions stored in database, not hardcoded
3. **Separation of Concerns**: Permission logic in AuthService, UI logic separate
4. **Testable**: Each component can be unit tested independently
5. **Scalable**: Easy to add new roles, permissions, or workflows without touching existing code

---

## Benefits of This Approach

✅ **No Spaghetti Code**: All permission logic centralized  
✅ **Easy to Extend**: Add new roles/permissions without code changes  
✅ **Maintainable**: Clear separation between permission checks and business logic  
✅ **Auditable**: All permission checks logged and traceable  
✅ **Flexible**: Support complex approval workflows  
✅ **User-Friendly**: UI automatically adapts to user's permissions  

---

## Next Steps (When Ready)

1. Review and refine the role structure based on actual business needs
2. Define complete list of permissions required
3. Create detailed workflow diagrams for approval processes
4. Implement Phase 1 (RBAC Foundation)
5. Test with sample users and roles
6. Iterate based on feedback

---

## Notes

- Current system has basic `is_admin` flag - this will be replaced with role-based system
- Existing `force_unlock` is admin-only - will become a permission check
- Lock system already in place - integrates well with permission system
- Audit log exists - can be extended to track permission changes

---

## Questions to Consider Before Implementation

1. What are all the user roles we need? (Start with 3-5, expand later)
2. What operations require approval vs direct execution?
3. Should some users have time-limited permissions?
4. Do we need role hierarchies (role inheritance)?
5. Should users be able to have multiple roles simultaneously?
6. What's the approval chain? (Single approver vs multi-level?)

---

**Remember**: This is a foundational architectural decision. Taking time to plan now will save significant refactoring later.
