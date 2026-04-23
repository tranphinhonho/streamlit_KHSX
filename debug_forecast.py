# -*- coding: utf-8 -*-
"""Debug script to analyze SALEFORECAST Excel file discrepancy"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# File path - adjust as needed
file_path = "EXCEL/W5.(25-31-01-) SALEFORECAST 2026.xlsx"
sheet_name = "W5.25-31-01-2026"

# Read Excel
df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

print(f"=== File: {file_path} ===")
print(f"Sheet: {sheet_name}")
print(f"Total rows: {len(df)}, columns: {len(df.columns)}")

# Column mapping for .xlsx
XLSX_COL_SO_LUONG = 20       # Cột U - Số lượng (tấn)
XLSX_COL_KICH_CO_EP = 1      # Cột B - Kích cỡ ép viên
XLSX_TEN_CAM_PRIORITY = [8, 3, 4, 5, 6, 7]  # Cột I, D, E, F, G, H
XLSX_START_ROW = 9
XLSX_END_MARKERS = ['***GOAT***', '***GRAND***', '***Laboratory***']

def get_ten_cam(row):
    """Get product name from row using priority logic"""
    for cot_ten_cam in XLSX_TEN_CAM_PRIORITY:
        if cot_ten_cam < len(row):
            ten_cam = row[cot_ten_cam]
            if pd.notna(ten_cam):
                ten_cam_str = str(ten_cam).strip()
                if ten_cam_str:
                    return ten_cam_str
    return None

def is_end_marker(row):
    if len(row) == 0:
        return False
    col_a = row[0]
    if pd.isna(col_a):
        return False
    return str(col_a).strip() in XLSX_END_MARKERS

# Calculate total using current code logic
total_code = 0
items_code = 0
aggregated = {}

for idx in range(XLSX_START_ROW, len(df)):
    row = df.iloc[idx]
    
    if is_end_marker(row):
        print(f"End marker found at row {idx+1}")
        break
    
    # Check quantity in column U
    so_luong = row[XLSX_COL_SO_LUONG] if XLSX_COL_SO_LUONG < len(row) else None
    
    try:
        so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
    except (ValueError, TypeError):
        continue
    
    if so_luong_val <= 0:
        continue
    
    # Get product name
    ten_cam = get_ten_cam(row)
    if ten_cam is None:
        # This row has quantity but no name - this might be the issue!
        print(f"!!WARNING Row {idx+1}: Has quantity {so_luong_val} but NO product name! Col A: {row[0]}")
        continue
    
    items_code += 1
    total_code += so_luong_val
    
    # Aggregate by product name
    if ten_cam in aggregated:
        aggregated[ten_cam] += so_luong_val
    else:
        aggregated[ten_cam] = so_luong_val

print(f"\n=== Calculation Summary ===")
print(f"Total from code logic: {total_code:,.1f} tấn")
print(f"Number of items: {items_code}")

# Find GRAND TOTAL from Excel
print(f"\n=== Looking for GRAND TOTAL ===")
for idx in range(len(df)):
    row = df.iloc[idx]
    col_a = row[0] if 0 < len(row) else None
    col_u = row[XLSX_COL_SO_LUONG] if XLSX_COL_SO_LUONG < len(row) else None
    
    if pd.notna(col_a):
        col_a_str = str(col_a).strip().upper()
        if 'GRAND' in col_a_str or 'TOTAL' in col_a_str:
            print(f"Row {idx+1}: Col A = '{col_a}', Col U = {col_u}")

# Calculate raw sum from column U (ignoring name logic)
print(f"\n=== Raw Sum from Column U (ignoring name logic) ===")
raw_sum = 0
raw_items = 0
for idx in range(XLSX_START_ROW, len(df)):
    row = df.iloc[idx]
    
    if is_end_marker(row):
        break
    
    so_luong = row[XLSX_COL_SO_LUONG] if XLSX_COL_SO_LUONG < len(row) else None
    
    try:
        so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
    except (ValueError, TypeError):
        continue
    
    if so_luong_val > 0:
        raw_sum += so_luong_val
        raw_items += 1

print(f"Raw sum from Col U: {raw_sum:,.1f} tấn")
print(f"Raw items: {raw_items}")
print(f"\nDifference: {raw_sum - total_code:,.1f} tấn (this is what's missing)")
