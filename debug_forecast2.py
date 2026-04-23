# -*- coding: utf-8 -*-
"""Debug script to compare aggregated vs non-aggregated totals"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Import the actual importer
sys.path.insert(0, '.')
from utils.forecast_importer import ForecastImporter

# File path
file_path = "EXCEL/W5.(25-31-01-) SALEFORECAST 2026.xlsx"
sheet_name = "W5.25-31-01-2026"

importer = ForecastImporter()

# Get preview data (what UI displays)
print("=== Preview Data (UI uses this) ===")
preview_df = importer.preview_data(file_path=file_path, sheet_name=sheet_name, limit=500)
if len(preview_df) > 0:
    print(f"Number of rows: {len(preview_df)}")
    total_preview = preview_df['Số lượng (tấn)'].sum()
    print(f"Total from preview: {total_preview:,.1f} tấn")

# Get GRAND TOTAL from Excel
print("\n=== GRAND TOTAL from Excel ===")
grand_total = importer.get_grand_total_from_excel(file_path=file_path, sheet_name=sheet_name)
print(f"GRAND TOTAL: {grand_total:,.1f} tấn")

# Check for duplicates in preview_df
print("\n=== Check for duplicates ===")
if 'Tên cám' in preview_df.columns:
    duplicate_names = preview_df[preview_df.duplicated(['Tên cám'], keep=False)]['Tên cám'].unique()
    if len(duplicate_names) > 0:
        print(f"Found {len(duplicate_names)} duplicate product names:")
        for name in duplicate_names[:10]:
            count = len(preview_df[preview_df['Tên cám'] == name])
            total = preview_df[preview_df['Tên cám'] == name]['Số lượng (tấn)'].sum()
            print(f"  - {name}: {count} rows, total = {total:.1f} tấn")
        
        # Calculate difference
        print(f"\n=== Difference Analysis ===")
        print(f"Preview total: {total_preview:,.1f} tấn")
        print(f"GRAND TOTAL: {grand_total:,.1f} tấn")
        print(f"Difference: {total_preview - grand_total:,.1f} tấn")
    else:
        print("No duplicates found")
