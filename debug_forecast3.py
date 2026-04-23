# -*- coding: utf-8 -*-
"""Debug script to find duplicate merge issue"""
import pandas as pd
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')
from utils.forecast_importer import ForecastImporter

# File path
file_path = "EXCEL/W5.(25-31-01-) SALEFORECAST 2026.xlsx"
sheet_name = "W5.25-31-01-2026"

importer = ForecastImporter()

# Get preview data (94 products)
print("=== Step 1: Preview Data (before merge) ===")
preview_df = importer.preview_data(file_path=file_path, sheet_name=sheet_name, limit=500)
print(f"Rows before merge: {len(preview_df)}")
print(f"Total before merge: {preview_df['Số lượng (tấn)'].sum():,.1f} tấn")

# Get SanPham data (simulate what DatHang.py does)
print("\n=== Step 2: Get SanPham data ===")
conn = sqlite3.connect('database_new.db')
sanpham_df = pd.read_sql("SELECT [Tên cám], [Vật nuôi] FROM SanPham WHERE [Đã xóa] = 0", conn)
conn.close()

print(f"SanPham rows: {len(sanpham_df)}")

# Check for duplicates in SanPham
duplicate_sanpham = sanpham_df[sanpham_df.duplicated(['Tên cám'], keep=False)]
if len(duplicate_sanpham) > 0:
    print(f"\n!!! Found {len(duplicate_sanpham)} duplicate 'Tên cám' entries in SanPham table !!!")
    print("Duplicates:")
    for name in duplicate_sanpham['Tên cám'].unique()[:20]:
        count = len(sanpham_df[sanpham_df['Tên cám'] == name])
        print(f"  - {name}: {count} entries")

# Simulate merge
print("\n=== Step 3: After merge (like DatHang.py) ===")
merged_df = preview_df.merge(
    sanpham_df[['Tên cám', 'Vật nuôi']],
    on='Tên cám',
    how='left'
)
print(f"Rows after merge: {len(merged_df)}")
print(f"Total after merge: {merged_df['Số lượng (tấn)'].sum():,.1f} tấn")

# Difference
print(f"\n=== Difference ===")
print(f"Extra rows after merge: {len(merged_df) - len(preview_df)}")
print(f"Extra tons after merge: {merged_df['Số lượng (tấn)'].sum() - preview_df['Số lượng (tấn)'].sum():,.1f}")

# Find which products got duplicated
if len(merged_df) > len(preview_df):
    print("\n=== Products that got duplicated after merge ===")
    # Group by Tên cám and count
    for _, row in preview_df.iterrows():
        ten_cam = row['Tên cám']
        before_count = len(preview_df[preview_df['Tên cám'] == ten_cam])
        after_count = len(merged_df[merged_df['Tên cám'] == ten_cam])
        if after_count > before_count:
            qty = row['Số lượng (tấn)']
            print(f"  - {ten_cam}: {before_count} -> {after_count} rows (qty: {qty:.1f} tấn)")
