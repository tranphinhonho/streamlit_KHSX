"""Kiểm tra cấu trúc file W4 (.xlsx) để xác định vị trí dữ liệu"""
import pandas as pd

file_path = "EXCEL/W4.(19-24-01-) SALEFORECAST 2026.xlsx"

print("="*70)
print("KIỂM TRA CẤU TRÚC FILE W4 (.xlsx)")
print("="*70)

xl = pd.ExcelFile(file_path)
print(f"\n📁 Danh sách Sheets: {xl.sheet_names}")

# Kiểm tra từng sheet
for sheet in xl.sheet_names:
    print(f"\n{'='*70}")
    print(f"📄 Sheet: '{sheet}'")
    print("="*70)
    
    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
    print(f"Kích thước: {len(df)} dòng x {len(df.columns)} cột")
    
    # Hiển thị 5 dòng đầu
    print("\n📋 5 dòng đầu tiên:")
    print(df.head(5).to_string())
    
    # Kiểm tra các cột có dữ liệu
    print("\n📊 Thống kê các cột có dữ liệu (không rỗng):")
    for col_idx in range(min(len(df.columns), 50)):
        non_null = df.iloc[:, col_idx].dropna()
        if len(non_null) > 0:
            # Lấy giá trị đầu tiên không null
            first_val = non_null.iloc[0] if len(non_null) > 0 else ""
            col_letter = ""
            temp = col_idx
            while temp >= 0:
                col_letter = chr(temp % 26 + ord('A')) + col_letter
                temp = temp // 26 - 1
            print(f"  Cột {col_letter} (index {col_idx}): {len(non_null)} giá trị, VD: {str(first_val)[:50]}")
    
    # Chỉ kiểm tra sheet đầu tiên hoặc sheet có tên bắt đầu bằng W
    if not sheet.startswith('W') and sheet != xl.sheet_names[0]:
        continue

print("\n" + "="*70)
print("KẾT THÚC KIỂM TRA")
print("="*70)
