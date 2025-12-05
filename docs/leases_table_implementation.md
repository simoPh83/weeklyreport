# Leases Table Implementation Summary

## Migration 018: Leases Table

### Table Structure
```sql
CREATE TABLE leases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    unit_id INTEGER NOT NULL,
    rent_pa REAL NOT NULL,
    start_date TEXT NOT NULL,
    break_date TEXT,
    expiry_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    updated_at TEXT,
    updated_by TEXT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
)
```

### Indexes Created
- `idx_leases_unit_id` - Fast lookups of leases by unit
- `idx_leases_tenant_id` - Fast lookups of leases by tenant
- `idx_leases_expiry_date` - Finding active/expiring leases

## Database Manager Methods Added

### Tenant Management
- `get_all_tenants()` - Get all tenants ordered by name
- `get_tenant_by_id(tenant_id)` - Get specific tenant
- `get_tenant_by_name(tenant_name)` - Find tenant by name
- `create_tenant(data, user_id)` - Create new tenant
- `update_tenant(tenant_id, data, user_id)` - Update tenant
- `delete_tenant(tenant_id, user_id)` - Delete tenant

### Lease Management
- `get_leases()` - Get all leases with tenant and unit info
- `get_lease_by_id(lease_id)` - Get specific lease
- `get_leases_by_unit(unit_id)` - Get all leases for a unit
- `get_current_lease_by_unit(unit_id)` - Get active lease for a unit
- `get_leases_by_tenant(tenant_id)` - Get all leases for a tenant
- `create_lease(data, user_id)` - Create new lease
- `update_lease(lease_id, data, user_id)` - Update lease
- `delete_lease(lease_id, user_id)` - Delete lease

## Actual Database Schema Notes

The database uses different column names than the initial schema definition:

### Units Table
- Uses `unit_name` (not `unit_number`)
- Uses `unit_type_id` (not `unit_type` text)
- Includes temporal tracking: `effective_from`, `effective_to`, `is_current`
- Includes lifecycle: `lifecycle_status`, `parent_unit_id`, `superseded_by`

### Buildings Table
- Uses `property_name` (not `name`)
- Uses `property_code` and `property_address` (not `address`)
- Includes `acquisition_date` and `disposal_date`

### Tenants Table (Already Existed)
- Uses `tenant_name` (not `name`)
- Includes `trading_as`, `b2c`, `category_id`
- No `contact_name`, `email`, `phone`, `address` fields

## Sample Data Created

The verification script created 3 sample leases:

1. **Active Lease** - Basement (South East)
   - Tenant: 111 Skin Limited
   - Rent: £50,000 PA
   - Period: 2024-12-05 to 2030-12-04
   - Break: 2028-12-05

2. **Active Lease (No Break)** - Basement (West)
   - Tenant: 111 Skin Limited
   - Rent: £35,000 PA
   - Period: 2025-06-08 to 2030-06-07

3. **Expired Lease** - Basement 56-57 Eastcastle St.
   - Tenant: 48 Margaret Street Trading Ltd
   - Rent: £42,000 PA
   - Period: 2019-12-07 to 2025-06-08

## Usage Example

```python
# Get current rent for a unit
lease = db.get_current_lease_by_unit(unit_id)
if lease:
    print(f"Current rent: £{lease['rent_pa']:,.2f} PA")
    print(f"Tenant: {lease['tenant_name']}")
    print(f"Expiry: {lease['expiry_date']}")
else:
    print("Unit is vacant")

# Create a new lease
lease_data = {
    'tenant_id': 123,
    'unit_id': 456,
    'rent_pa': 45000.00,
    'start_date': '2025-01-01',
    'break_date': '2028-01-01',
    'expiry_date': '2030-12-31'
}
lease_id = db.create_lease(lease_data, user_id)
```

## Next Steps for Letting Progress Tab

With the leases table in place, you can now:

1. Display current rent for units in the letting progress table
2. Track when leases are expiring to identify upcoming vacancies
3. Show tenant information alongside unit details
4. Calculate total rental income from active leases
5. Compare current rent vs. target rent in letting progress records

The `get_current_lease_by_unit()` method will be particularly useful in the GUI to display rent information for units being tracked in the letting progress system.
