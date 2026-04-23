# -*- coding: utf-8 -*-
"""Debug script to analyze SILO Excel file structure"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# File path
file_path = "EXCEL/SILO W5-25-31-01-2026.xlsx"
sheet_name = "25-31-01-2026"

# Read Excel
df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

print(f"=== File: {file_path} ===")
print(f"Sheet: {sheet_name}")
print(f"Total rows: {len(df)}, columns: {len(df.columns)}")

# Check row 5 (index 4) - header dates
print("\n=== Row 5 (index 4) - Column Headers ===")
row5 = df.iloc[4]
for col_idx in range(12):  # Check first 12 columns
    val = row5[col_idx] if col_idx < len(row5) else None
    print(f"  Col {col_idx} ({chr(65+col_idx)}): {val}")

# Calculate totals with different column ranges
print("\n=== Total Calculation ===")

# Current code: C-H (index 2-7)
total_current = 0
for row_idx in range(5, len(df)):
    row = df.iloc[row_idx]
    ten_cam = row[0]
    if pd.notna(ten_cam) and str(ten_cam).strip():
        for col_idx in range(2, 8):  # C to H
            val = row[col_idx] if col_idx < len(row) else None
            if pd.notna(val):
                try:
                    num = float(val)
                    if num > 99:
                        total_current += num
                except:
                    pass

print(f"Current code (C-H, index 2-7): {total_current:,.0f} kg")

# Correct: C-I (index 2-8) - 7 days
total_correct = 0
for row_idx in range(5, len(df)):
    row = df.iloc[row_idx]
    ten_cam = row[0]
    if pd.notna(ten_cam) and str(ten_cam).strip():
        for col_idx in range(2, 9):  # C to I
            val = row[col_idx] if col_idx < len(row) else None
            if pd.notna(val):
                try:
                    num = float(val)
                    if num > 99:
                        total_correct += num
                except:
                    pass

print(f"Correct (C-I, index 2-8): {total_correct:,.0f} kg")

# Check column I specifically
total_col_i = 0
for row_idx in range(5, len(df)):
    row = df.iloc[row_idx]
    ten_cam = row[0]
    if pd.notna(ten_cam) and str(ten_cam).strip():
        val = row[8] if 8 < len(row) else None  # Column I
        if pd.notna(val):
            try:
                num = float(val)
                if num > 99:
                    total_col_i += num
            except:
                pass

print(f"Column I only (index 8): {total_col_i:,.0f} kg")
print(f"\nDifference: {total_correct - total_current:,.0f} kg (this is what's missing)")
print(f"\nExpected total from Excel: 3,151,000 kg")
