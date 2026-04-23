# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io

# Encoding fix for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read file PL1
file_path = 'EXCEL/PL1 1.2026.xlsx'
df = pd.read_excel(file_path, sheet_name='2', header=None, engine='openpyxl')

print("=== Data Structure ===")
print("Col B (1): Ten cam")
print("Col AW (48): T/h")
print("Col AU (46): Kwh/T")
print()

# Get data from rows 9-44 (Excel row 10-45)
print("=== Data in B10:B44, AU10:AU44, AW10:AW44 ===")
print("Row | Col B (Ten cam)  | Col AU (Kwh/T) | Col AW (T/h)")
print("-" * 60)

for row in range(9, min(45, len(df))):
    ten_cam = df.iloc[row, 1] if 1 < len(df.columns) else None
    kwh_t = df.iloc[row, 46] if 46 < len(df.columns) else None
    t_h = df.iloc[row, 48] if 48 < len(df.columns) else None
    
    # Only show rows with data
    if pd.notna(ten_cam) or (pd.notna(t_h) and t_h != 0):
        ten_cam_str = str(ten_cam)[:15] if pd.notna(ten_cam) else ""
        kwh_str = str(kwh_t)[:10] if pd.notna(kwh_t) and kwh_t != 0 else ""
        t_h_str = str(t_h)[:10] if pd.notna(t_h) and t_h != 0 else ""
        print(f"{row+1:3} | {ten_cam_str:16} | {kwh_str:14} | {t_h_str}")

print()
print("=== T/h Summary by Feed Code ===")
th_summary = {}
for row in range(9, min(45, len(df))):
    ten_cam = df.iloc[row, 1]
    t_h = df.iloc[row, 48] if 48 < len(df.columns) else None
    
    if pd.notna(ten_cam) and pd.notna(t_h) and t_h != 0 and not isinstance(t_h, str):
        ten_cam_str = str(ten_cam).strip()
        if ten_cam_str not in th_summary:
            th_summary[ten_cam_str] = []
        try:
            th_summary[ten_cam_str].append(float(t_h))
        except:
            pass

for cam, vals in th_summary.items():
    if vals:
        avg = sum(vals) / len(vals)
        print(f"{cam}: Avg T/h = {avg:.2f} (from {len(vals)} batches)")
