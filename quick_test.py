import pandas as pd

# Read the xlsx file directly
file_path = "EXCEL/W4.(19-24-01-) SALEFORECAST 2026.xlsx"
df = pd.read_excel(file_path, sheet_name="W4", header=None)

# Constants matching VBA logic
XLSX_COL_SO_LUONG = 20      # Column U
XLSX_TEN_CAM_PRIORITY = [8, 3, 4, 5, 6, 7]  # I, D, E, F, G, H
XLSX_START_ROW = 9  # Start from row 10

print(f"Total rows: {len(df)}")
print(f"\nPreview data from row 10 (index 9):")

count = 0
for idx in range(XLSX_START_ROW, min(len(df), XLSX_START_ROW + 50)):
    row = df.iloc[idx]
    
    # Check end marker
    col_a = row[0]
    if pd.notna(col_a) and str(col_a).strip() in ['***GOAT***', '***GRAND***', '***Laboratory***']:
        print(f"\nEnd marker found at row {idx+1}: {col_a}")
        break
    
    # Check U > 0
    so_luong = row[XLSX_COL_SO_LUONG] if XLSX_COL_SO_LUONG < len(row) else None
    try:
        so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
    except:
        continue
    
    if so_luong_val <= 0:
        continue
    
    # Get product name by priority
    ten_cam = None
    for col in XLSX_TEN_CAM_PRIORITY:
        if col < len(row):
            val = row[col]
            if pd.notna(val) and str(val).strip():
                ten_cam = str(val).strip()
                break
    
    if ten_cam:
        kich_co_ep = row[1] if 1 < len(row) else None  # Column B
        kich_co_bao = row[2] if 2 < len(row) else None  # Column C
        print(f"Row {idx+1}: {ten_cam} | Ep: {kich_co_ep} | Bao: {kich_co_bao} | SL: {so_luong_val}")
        count += 1
        if count >= 15:
            print(f"\n... (showing first 15 records)")
            break

print(f"\n=== Total records found: {count}+ ===")
