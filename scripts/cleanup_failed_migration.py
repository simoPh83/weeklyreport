import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database file', 'WeeklyReportDB.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop unit_history table that was created during failed migration
cursor.execute("DROP TABLE IF EXISTS unit_history")
conn.commit()

print("✓ Cleaned up unit_history table from failed migration")

conn.close()
