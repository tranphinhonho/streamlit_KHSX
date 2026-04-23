"""Debug tìm GRAND TOTAL trong file Excel"""
import pandas as pd

# Test với file .xlsm (đang dùng)
file_path = "EXCEL/W3.(12-17-01-) SALEFORECAST 2026.xlsm"
sheet_name = "W4.19-24-01-2025"

print("="*70)
print(f"DEBUG TÌM GRAND TOTAL")
print(f"File: {file_path}")
print(f"Sheet: {sheet_name}")
print("="*70)

xl = pd.ExcelFile(file_path)
print(f"Sheets: {xl.sheet_names}")

df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
print(f"Kích thước: {len(df)} dòng x {len(df.columns)} cột")

# Tìm các dòng có chứa "GRAND" hoặc "TOTAL" trong cột A
print("\n🔍 Tìm các dòng có chứa 'GRAND' hoặc 'TOTAL' trong cột A:")
for idx in range(len(df)):
    row = df.iloc[idx]
    col_a = row[0]
    if pd.notna(col_a):
        col_a_str = str(col_a).strip().upper()
        if 'GRAND' in col_a_str or 'TOTAL' in col_a_str:
            # Lấy giá trị cột U (index 20) và cột AI (index 34)
            col_u = row[20] if 20 < len(row) else None
            col_ai = row[34] if 34 < len(row) else None
            print(f"  Dòng {idx+1}: A='{col_a}' | U={col_u} | AI={col_ai}")

# Thử tìm trong cột khác
print("\n🔍 Tìm trong tất cả các cột (50 cột đầu):")
for idx in range(len(df)):
    row = df.iloc[idx]
    for col_idx in range(min(len(row), 50)):
        val = row[col_idx]
        if pd.notna(val):
            val_str = str(val).strip().upper()
            if 'GRAND TOTAL' in val_str:
                col_u = row[20] if 20 < len(row) else None
                col_ai = row[34] if 34 < len(row) else None
                col_letter = chr(col_idx + ord('A')) if col_idx < 26 else f"Col{col_idx}"
                print(f"  Dòng {idx+1}, Cột {col_letter}='{val}' | U={col_u} | AI={col_ai}")

print("\n" + "="*70)
