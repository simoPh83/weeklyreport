import sqlite3
from pathlib import Path

db_path = Path("database file/WeeklyReportDB.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Current units table columns:")
print("="*60)
cursor.execute('PRAGMA table_info(units)')
for row in cursor.fetchall():
    not_null = "NOT NULL" if row[3] else ""
    default = f"DEFAULT {row[4]}" if row[4] else ""
    print(f"  {row[1]:25s} {row[2]:10s} {not_null:10s} {default}")

print("\n" + "="*60)
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="unit_relationships"')
print(f"unit_relationships table exists: {bool(cursor.fetchone())}")

print("\n" + "="*60)
print("Indexes on units table:")
cursor.execute('SELECT name FROM sqlite_master WHERE type="index" AND tbl_name="units"')
for row in cursor.fetchall():
    print(f"  - {row[0]}")

conn.close()
