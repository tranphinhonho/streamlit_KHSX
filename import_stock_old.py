"""
Script import Stock Old từ file Excel
Ánh xạ: Code cám (A) → ID sản phẩm, Số lượng (F), Day On Hand (G) → Ghi chú
"""

import pandas as pd
import sqlite3
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
EXCEL_FILE = "StockOld 02-12-2025.xlsx"
SHEET_NAME = "S1"  # Tên sheet trong file Excel
START_ROW = 1  # Hàng 2 trong Excel = index 1 (0-based, vì hàng 1 là header)
DB_PATH = "database_new.db"
USERNAME = "phinho"  # Thay bằng username của bạn

# Mapping cột Excel (theo index 0-based: A=0, B=1, C=2, ...)
COL_CODE_CAM = 0        # Cột A: Code cám
COL_TEN_CAM = 1         # Cột B: Tên cám
COL_KICH_CO_EP = 2      # Cột C: Kích cỡ ép viên
COL_KICH_CO_DONG_BAO = 3  # Cột D: Kích cỡ đóng bao
COL_TON_KHO = 5         # Cột F: Tồn kho (Kg)
COL_DAY_ON_HAND = 6     # Cột G: Day on hand

# =========================
# FUNCTIONS
# =========================

def get_id_sanpham_by_code(cursor, code_cam):
    """
    Tìm ID sản phẩm từ Code cám
    """
    cursor.execute("""
        SELECT ID 
        FROM SanPham 
        WHERE TRIM([Code cám]) = ? AND [Đã xóa] = 0
    """, (str(code_cam).strip(),))
    
    result = cursor.fetchone()
    return result[0] if result else None


def generate_next_code(cursor):
    """
    Tạo mã Stock Old tự động (SO00001, SO00002...)
    """
    cursor.execute("""
        SELECT MAX([Mã stock old]) 
        FROM StockOld 
        WHERE [Mã stock old] LIKE 'SO%'
    """)
    
    result = cursor.fetchone()[0]
    
    if result:
        # Lấy phần số từ mã cuối cùng
        last_num = int(result[2:])  # Bỏ 'SO' ở đầu
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"SO{next_num:05d}"


def import_stock_old(excel_file, sheet_name, start_row):
    """
    Import dữ liệu Stock Old từ Excel vào database
    """
    
    # 1. Đọc file Excel
    print(f"📖 Đọc file Excel: {excel_file}")
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    print(f"✅ Đã đọc {len(df)} dòng dữ liệu\n")
    
    # 2. Trích xuất dữ liệu cần thiết
    data = []
    for idx, row in df.iterrows():
        code_cam = row.iloc[COL_CODE_CAM]
        ton_kho = row.iloc[COL_TON_KHO]
        day_on_hand = row.iloc[COL_DAY_ON_HAND]
        
        # Bỏ qua dòng trống
        if pd.isna(code_cam) or pd.isna(ton_kho):
            continue
        
        # Làm sạch dữ liệu
        code_cam = str(code_cam).strip()
        
        try:
            ton_kho = int(float(ton_kho))
        except:
            ton_kho = 0
        
        # Xử lý Day On Hand
        try:
            day_on_hand = float(day_on_hand) if not pd.isna(day_on_hand) else 0
        except:
            day_on_hand = 0
        
        # Chỉ lấy dòng có số lượng > 0
        if ton_kho > 0:
            data.append({
                'code_cam': code_cam,
                'ton_kho': ton_kho,
                'day_on_hand': day_on_hand
            })
    
    print(f"✅ Đã lọc {len(data)} dòng dữ liệu hợp lệ (tồn kho > 0)\n")
    
    # 3. Kết nối database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 4. Tạo mã Stock Old
    ma_stock_old = generate_next_code(cursor)
    ngay_stock_old = datetime.now().strftime('%Y-%m-%d')
    thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"📦 Mã Stock Old: {ma_stock_old}")
    print(f"📅 Ngày Stock Old: {ngay_stock_old}\n")
    
    # 5. Insert dữ liệu
    success_count = 0
    not_found = []
    errors = []
    
    print("🔄 Bắt đầu import...")
    for item in data:
        try:
            # Tìm ID sản phẩm từ Code cám
            id_sanpham = get_id_sanpham_by_code(cursor, item['code_cam'])
            
            if not id_sanpham:
                not_found.append(item['code_cam'])
                continue
            
            # Insert vào StockOld
            cursor.execute("""
                INSERT INTO StockOld 
                ([ID sản phẩm], [Mã stock old], [Số lượng], [Ngày stock old], 
                 [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa])
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                id_sanpham,
                ma_stock_old,
                item['ton_kho'],
                ngay_stock_old,
                f"Day On Hand: {item['day_on_hand']:.1f}",
                USERNAME,
                thoi_gian_tao
            ))
            
            success_count += 1
            
        except Exception as e:
            errors.append(f"{item['code_cam']}: {e}")
    
    # 6. Commit và đóng kết nối
    conn.commit()
    conn.close()
    
    # 7. Báo cáo kết quả
    print("\n" + "="*60)
    print("📊 KẾT QUẢ IMPORT")
    print("="*60)
    print(f"✅ Thành công: {success_count} sản phẩm")
    print(f"⚠️  Không tìm thấy: {len(not_found)} sản phẩm")
    print(f"❌ Lỗi: {len(errors)} sản phẩm\n")
    
    if not_found:
        print("❌ Danh sách Code cám không tìm thấy trong database:")
        for code in not_found[:20]:  # Hiển thị tối đa 20
            print(f"   - {code}")
        if len(not_found) > 20:
            print(f"   ... và {len(not_found) - 20} mã khác")
        print()
    
    if errors:
        print("❌ Danh sách lỗi:")
        for err in errors[:5]:
            print(f"   - {err}")
        if len(errors) > 5:
            print(f"   ... và {len(errors) - 5} lỗi khác")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("="*60)
    print("🚀 IMPORT STOCK OLD TỪ EXCEL")
    print("="*60)
    print(f"📁 File: {EXCEL_FILE}")
    print(f"📄 Sheet: {SHEET_NAME}")
    print(f"📊 Database: {DB_PATH}\n")
    
    try:
        import_stock_old(EXCEL_FILE, SHEET_NAME, START_ROW)
        print("\n✅ HOÀN THÀNH!")
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
