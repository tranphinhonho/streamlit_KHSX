"""Debug chi tiết file W4 (.xlsx) - in ra từng dòng để xác định đúng vị trí"""
import pandas as pd

file_path = "EXCEL/W4.(19-24-01-) SALEFORECAST 2026.xlsx"

print("="*80)
print("DEBUG FILE W4 - KIỂM TRA CẤU TRÚC DỮ LIỆU")
print("="*80)

xl = pd.ExcelFile(file_path)
print(f"\nSheets: {xl.sheet_names}")

# Tìm sheet W4
week_sheets = [s for s in xl.sheet_names if s.startswith('W')]
print(f"Week sheets: {week_sheets}")

if week_sheets:
    sheet = week_sheets[-1]
    print(f"\nĐọc sheet: {sheet}")
    
    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
    print(f"Kích thước: {len(df)} dòng x {len(df.columns)} cột")
    
    # Column indices (0-based)
    # A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8
    # J=9, K=10, L=11, M=12, N=13, O=14, P=15, Q=16, R=17
    # S=18, T=19, U=20
    
    COL_U = 20  # TOTAL (GRAND TOTAL)
    COL_B = 1   # DIE Size (Kích cỡ ép viên)
    COL_C = 2   # PACKING SIZE (Kích cỡ bao)
    
    # Mapping: (condition col, name col)
    MAPPING = [
        (17, 8, "R -> I (FARM)"),
        (9, 3, "J -> D (HIGRO)"),
        (10, 4, "K -> E (CP)"),
        (11, 5, "L -> F (STAR)"),
        (12, 6, "M -> G (NUVO)"),
        (13, 7, "N -> H (NASA)"),
    ]
    
    print("\n" + "="*80)
    print("KIỂM TRA TỪNG DÒNG (từ dòng 10 = index 9)")
    print("="*80)
    
    found_count = 0
    for idx in range(9, min(len(df), 50)):  # Dòng 10-50
        row = df.iloc[idx]
        
        # Kiểm tra cột A có phải end marker
        col_a = str(row[0]) if pd.notna(row[0]) else ""
        if "GOAT" in col_a or "GRAND" in col_a or "Laboratory" in col_a:
            print(f"\n🛑 End marker tại dòng {idx+1}: '{col_a}'")
            break
        
        # Lấy giá trị cột U
        u_val = row[COL_U] if COL_U < len(row) else None
        try:
            u_num = float(u_val) if pd.notna(u_val) else 0
        except:
            u_num = 0
        
        if u_num <= 0:
            continue
        
        # Tìm tên cám
        ten_cam = None
        matched_rule = None
        for cond_col, name_col, rule_name in MAPPING:
            cond_val = row[cond_col] if cond_col < len(row) else None
            try:
                cond_num = float(cond_val) if pd.notna(cond_val) else 0
            except:
                cond_num = 0
            
            if cond_num > 0:
                name_val = row[name_col] if name_col < len(row) else None
                if pd.notna(name_val) and str(name_val).strip():
                    ten_cam = str(name_val).strip()
                    matched_rule = rule_name
                    break
        
        if ten_cam:
            found_count += 1
            kich_co_ep = row[COL_B] if COL_B < len(row) else None
            kich_co_bao = row[COL_C] if COL_C < len(row) else None
            
            print(f"\n✅ Dòng {idx+1}:")
            print(f"   Tên cám: '{ten_cam}' ({matched_rule})")
            print(f"   Số lượng (U): {u_num}")
            print(f"   Kích cỡ ép (B): {kich_co_ep}")
            print(f"   Kích cỡ bao (C): {kich_co_bao}")
            
            if found_count >= 15:
                print("\n... (hiển thị 15 dòng đầu)")
                break
        else:
            # Debug dòng có U > 0 nhưng không tìm thấy tên
            print(f"\n⚠️ Dòng {idx+1}: U={u_num} nhưng không tìm thấy tên cám")
            print(f"   Các giá trị: D={row[3] if 3<len(row) else '-'}, E={row[4] if 4<len(row) else '-'}, I={row[8] if 8<len(row) else '-'}")
            print(f"   Điều kiện: J={row[9] if 9<len(row) else '-'}, K={row[10] if 10<len(row) else '-'}, R={row[17] if 17<len(row) else '-'}")
    
    print(f"\n{'='*80}")
    print(f"TỔNG KẾT: Tìm thấy {found_count} sản phẩm")
    print("="*80)
