import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database file', 'WeeklyReportDB.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%unit%' ORDER BY name")
tables = cursor.fetchall()

print("Unit-related tables:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()
