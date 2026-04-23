# -*- coding: utf-8 -*-
"""Test PL3 import with updated column structure"""
from utils.pellet_capacity_importer import PelletCapacityImporter

importer = PelletCapacityImporter()

# Test read PL3 sheet 2
file_path = 'EXCEL/PL3 1.2026.xlsx'
print(f"Testing PL3 read sheet 2: {file_path}")

df = importer.read_sheet(file_path, '2')
print(f"Records found: {len(df)}")

if len(df) > 0:
    kwh_count = df['Kwh/T'].notna().sum()
    print(f"Records with Kwh/T: {kwh_count}")
    
    for i, row in df.head(5).iterrows():
        kwh_val = f"{row['Kwh/T']:.2f}" if row['Kwh/T'] else 'N/A'
        print(f"  {row['Code cám']}: T/h={row['T/h']:.2f}, Kwh/T={kwh_val}")
else:
    print("No data found!")
    
# Test import PL3
print(f"\nImporting {file_path}...")
result = importer.import_file(file_path, nguoi_import='test', overwrite=True)

if result.get('success'):
    print(f"SUCCESS! Imported: {result.get('imported')} records")
else:
    print(f"FAILED: {result.get('error')}")
