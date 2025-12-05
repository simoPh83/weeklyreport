"""
Check actual table structures in the database
"""
import sqlite3

DB_PATH = "database file/WeeklyReportDB.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get units table structure
print("Units table columns:")
cursor.execute("PRAGMA table_info(units)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Get buildings table structure
print("\nBuildings table columns:")
cursor.execute("PRAGMA table_info(buildings)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Get tenants table structure
print("\nTenants table columns:")
cursor.execute("PRAGMA table_info(tenants)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
