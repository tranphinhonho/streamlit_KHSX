# -*- coding: utf-8 -*-
"""Test import PL file with updated Kwh/T logic"""
from utils.pellet_capacity_importer import PelletCapacityImporter

importer = PelletCapacityImporter()

# Test read 1 sheet first to check Kwh/T values
file_path = 'EXCEL/PL1 1.2026.xlsx'
print(f"Testing read sheet 2 from: {file_path}")

df = importer.read_sheet(file_path, '2')
print(f"Records found: {len(df)}")

if len(df) > 0:
    # Check if Kwh/T has values
    kwh_count = df['Kwh/T'].notna().sum()
    print(f"Records with Kwh/T: {kwh_count}")
    
    # Print first few records
    for i, row in df.head(5).iterrows():
        print(f"  {row['Code cám']}: T/h={row['T/h']:.2f}, Kwh/T={row['Kwh/T'] if row['Kwh/T'] else 'N/A'}")

# Re-import file
print(f"\nRe-importing {file_path}...")
result = importer.import_file(file_path, nguoi_import='test', overwrite=True)

if result.get('success'):
    print(f"SUCCESS! Imported: {result.get('imported')} records")
else:
    print(f"FAILED: {result.get('error')}")
