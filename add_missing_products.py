"""
Script thêm nhanh 4 mã sản phẩm thiếu
"""
import sqlite3
from datetime import datetime

database_path = "database_new.db"
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 4 mã cần thêm - bạn có thể điều chỉnh thông tin
# Format: (Code cám, Tên cám, Kích cỡ ép viên, Kích cỡ đóng bao)
san_pham_moi = [
    ('433060', 'Sản phẩm 433060', '', 25),
    ('433760', 'Sản phẩm 433760', '', 25),
    ('31408887', 'Sản phẩm 31408887', '', 25),
    ('332401', 'Sản phẩm 332401', '', 25),
]

print("=" * 60)
print("THÊM SẢN PHẨM MỚI")
print("=" * 60)

# Lấy max ID
cursor.execute("SELECT MAX(ID) FROM SanPham")
max_id = cursor.fetchone()[0] or 0

added = 0
for code, ten, kich_co_ep, kich_co_bao in san_pham_moi:
    # Kiểm tra đã tồn tại chưa
    cursor.execute("SELECT ID FROM SanPham WHERE [Code cám] = ?", (code,))
    if cursor.fetchone():
        print(f"⚠️ {code} đã tồn tại, bỏ qua")
        continue
    
    max_id += 1
    cursor.execute("""
        INSERT INTO SanPham (
            ID, [Code cám], [Tên cám], [Kích cỡ ép viên], [Kích cỡ đóng bao],
            [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (max_id, code, ten, kich_co_ep, kich_co_bao, 'phinho', current_time))
    
    print(f"✅ Đã thêm: {code} - {ten}")
    added += 1

conn.commit()
conn.close()

print(f"\n✅ Đã thêm {added} sản phẩm mới")
print("Bây giờ bạn có thể import lại file FFSTOCK")
