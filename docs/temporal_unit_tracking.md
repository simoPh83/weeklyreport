# Temporal Unit Tracking - User Guide

## Overview

The units table now supports temporal tracking, allowing you to record how units change over time (splits, merges, reconfigurations).

---

## Current Schema

### Units Table - Temporal Fields

| Field | Type | Purpose |
|-------|------|---------|
| `effective_from` | DATE | When this unit configuration started existing |
| `effective_to` | DATE | When it stopped existing (NULL = still current) |
| `is_current` | BOOLEAN | Quick filter: 1 = active now, 0 = historical |
| `lifecycle_status` | TEXT | What happened: 'active', 'split', 'merged', 'reconfigured' |
| `parent_unit_id` | INTEGER | If split from another unit, link to parent |
| `superseded_by` | TEXT | JSON array of unit IDs that replaced this (e.g. "[123,124]") |

### Unit_Relationships Table

Tracks the specific relationships between units when they change.

| Field | Type | Purpose |
|-------|------|---------|
| `from_unit_id` | INTEGER | The unit that changed |
| `to_unit_id` | INTEGER | The resulting unit |
| `relationship_type` | TEXT | 'split_into', 'merged_into', 'reconfigured_to', 'renamed_to' |
| `effective_date` | DATE | When this change happened |
| `notes` | TEXT | Explanation of the change |

---

## Usage Examples

### Scenario 1: Split a Unit (1 → 2)

**Example**: "Suite 100" (2000 sq ft) splits into "Suite 100A" (1200 sq ft) and "Suite 100B" (800 sq ft) on 2024-01-01

```sql
-- 1. Close the old unit
UPDATE units 
SET effective_to = '2023-12-31',
    is_current = 0,
    lifecycle_status = 'split',
    superseded_by = '[101,102]'  -- IDs of new units
WHERE id = 100;

-- 2. Insert new units
INSERT INTO units (building_id, unit_name, sq_ft, unit_type_id, effective_from, is_current, lifecycle_status, parent_unit_id)
VALUES 
    (10, 'Suite 100A', 1200, 1, '2024-01-01', 1, 'active', 100),  -- ID will be 101
    (10, 'Suite 100B', 800, 1, '2024-01-01', 1, 'active', 100);   -- ID will be 102

-- 3. Record relationships
INSERT INTO unit_relationships (from_unit_id, to_unit_id, relationship_type, effective_date, notes)
VALUES 
    (100, 101, 'split_into', '2024-01-01', 'North side became Suite A'),
    (100, 102, 'split_into', '2024-01-01', 'South side became Suite B');
```

### Scenario 2: Merge Units (2 → 1)

**Example**: "Office A" and "Office B" merge into "Large Office" on 2025-01-01

```sql
-- 1. Close both old units
UPDATE units 
SET effective_to = '2024-12-31',
    is_current = 0,
    lifecycle_status = 'merged',
    superseded_by = '[300]'
WHERE id IN (200, 201);

-- 2. Insert merged unit
INSERT INTO units (building_id, unit_name, sq_ft, unit_type_id, effective_from, is_current, lifecycle_status)
VALUES (10, 'Large Office', 1200, 1, '2025-01-01', 1, 'active');  -- ID will be 300

-- 3. Record relationships
INSERT INTO unit_relationships (from_unit_id, to_unit_id, relationship_type, effective_date, notes)
VALUES 
    (200, 300, 'merged_into', '2025-01-01', 'Combined with Office B'),
    (201, 300, 'merged_into', '2025-01-01', 'Combined with Office A');
```

### Scenario 3: Simple Rename

**Example**: "Retail Space" renamed to "Retail Hub" on 2025-06-01

```sql
-- 1. Close old unit
UPDATE units 
SET effective_to = '2025-05-31',
    is_current = 0,
    lifecycle_status = 'reconfigured',
    superseded_by = '[400]'
WHERE id = 350;

-- 2. Insert renamed unit (same sq_ft, just new name)
INSERT INTO units (building_id, unit_name, sq_ft, unit_type_id, effective_from, is_current, lifecycle_status, parent_unit_id)
VALUES (10, 'Retail Hub', 2000, 2, '2025-06-01', 1, 'active', 350);  -- ID will be 400

-- 3. Record relationship
INSERT INTO unit_relationships (from_unit_id, to_unit_id, relationship_type, effective_date, notes)
VALUES (350, 400, 'renamed_to', '2025-06-01', 'Rebranding initiative');
```

---

## Query Patterns

### Get Current Units Only

```sql
SELECT id, unit_name, sq_ft 
FROM units 
WHERE building_id = 10 
  AND is_current = 1
ORDER BY unit_name;
```

**Why fast?** Uses `idx_units_current` index.

---

### Get Units That Existed During a Specific Year

```sql
-- Example: What units existed in 2023?
SELECT id, unit_name, sq_ft, effective_from, effective_to
FROM units 
WHERE building_id = 10
  AND effective_from <= '2023-12-31'
  AND (effective_to IS NULL OR effective_to >= '2023-01-01')
ORDER BY unit_name;
```

**Why fast?** Uses `idx_units_temporal` index.

---

### Trace Unit Lineage (What Happened to a Unit?)

```sql
-- Example: What happened to unit ID 100?
SELECT 
    u_from.unit_name AS original_unit,
    ur.relationship_type,
    u_to.unit_name AS became,
    u_to.sq_ft,
    ur.effective_date,
    ur.notes
FROM units u_from
JOIN unit_relationships ur ON u_from.id = ur.from_unit_id
JOIN units u_to ON ur.to_unit_id = u_to.id
WHERE u_from.id = 100
ORDER BY ur.effective_date;
```

---

### Find Parent of a Unit (Where Did This Come From?)

```sql
-- Example: Where did unit ID 101 come from?
SELECT 
    u_parent.id AS parent_id,
    u_parent.unit_name AS parent_name,
    u_parent.sq_ft AS parent_sqft,
    u_child.unit_name AS child_name,
    u_child.sq_ft AS child_sqft
FROM units u_child
LEFT JOIN units u_parent ON u_child.parent_unit_id = u_parent.id
WHERE u_child.id = 101;
```

---

### Complete Unit History for a Building

```sql
-- Shows all units (past and present) with their time periods
SELECT 
    unit_name,
    sq_ft,
    effective_from,
    effective_to,
    CASE 
        WHEN is_current = 1 THEN 'CURRENT'
        ELSE lifecycle_status
    END AS status
FROM units
WHERE building_id = 10
ORDER BY unit_name, effective_from;
```

---

## Import Script Integration

When importing ERVs or other historical data, use temporal matching:

```python
def find_unit_for_year(property_name, unit_name, year):
    """Find unit that existed during the specified year"""
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"
    
    cursor.execute("""
        SELECT u.id, u.unit_name, u.sq_ft
        FROM units u
        JOIN buildings b ON u.building_id = b.id
        WHERE b.property_address = ?
          AND u.unit_name = ?
          AND u.effective_from <= ?
          AND (u.effective_to IS NULL OR u.effective_to >= ?)
    """, (property_name, unit_name, year_end, year_start))
    
    return cursor.fetchone()
```

---

## Best Practices

### 1. **Never Delete Units** - Always Close Them
```sql
-- ❌ DON'T DO THIS
DELETE FROM units WHERE id = 100;

-- ✅ DO THIS
UPDATE units 
SET effective_to = CURRENT_DATE, 
    is_current = 0, 
    lifecycle_status = 'split'
WHERE id = 100;
```

### 2. **Always Record Why Units Changed**
Use the `notes` field in `unit_relationships` to explain what happened.

### 3. **Maintain Data Integrity**
- `effective_from` must be < `effective_to` (if `effective_to` is not NULL)
- Only one unit with same `unit_name` in a building should have `is_current = 1`
- If `lifecycle_status` is 'split' or 'merged', `superseded_by` should be populated

### 4. **Use Indexes**
All the temporal queries above are optimized with indexes. Don't add `WHERE` clauses that bypass the indexes.

---

## Performance Notes

The indexes ensure:
- **Current unit queries**: O(log n) - extremely fast even with 10,000+ historical units
- **Temporal range queries**: O(log n + k) where k = matching units
- **Lineage tracing**: O(depth) - fast even for complex split/merge chains

As your database grows with historical units, query performance remains constant thanks to the indexes.

---

## Next Steps

1. ✅ Schema is ready
2. ⏳ Update ERV import script to use temporal matching
3. ⏳ Create UI helper functions for common queries
4. ⏳ Add validation to prevent invalid temporal data
5. ⏳ Create management tools for recording splits/merges

