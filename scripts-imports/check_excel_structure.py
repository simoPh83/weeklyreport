"""
Quick check of Excel structure to understand the data layout
"""
import pandas as pd
from pathlib import Path

excel_path = Path(__file__).parent.parent / "data" / "[ORIGINAL] Leasing Bank Schedule June 2025.xlsx"

df = pd.read_excel(excel_path, sheet_name=0, header=2)

print("First 20 rows:")
print("="*100)

for idx, row in df.head(20).iterrows():
    prop = row.get('Property', '')
    unit = row.get('Unit Demise', '')
    tenant = row.get('Tenant Name', '')
    
    if not pd.isna(prop):
        print(f"Row {idx+3}: Property = '{prop}'")
    if not pd.isna(unit):
        print(f"Row {idx+3}:   Unit = '{unit}', Tenant = '{tenant}'")
