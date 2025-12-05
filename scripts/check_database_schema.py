"""
Check actual database schema to verify column names
"""
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database file', 'WeeklyReportDB.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tables to check
tables = ['buildings', 'units', 'unit_types', 'unit_square_footage', 'leases', 'tenants', 'business_categories']

for table in tables:
    print(f"\n{'='*60}")
    print(f"Table: {table}")
    print('='*60)
    
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        if columns:
            print(f"{'ID':<5} {'Column Name':<30} {'Type':<15} {'NotNull':<8} {'Default':<15}")
            print('-'*80)
            for col in columns:
                cid, name, col_type, notnull, default_val, pk = col
                print(f"{cid:<5} {name:<30} {col_type:<15} {notnull:<8} {str(default_val):<15}")
        else:
            print("Table does not exist or has no columns")
    except Exception as e:
        print(f"Error: {e}")

conn.close()
