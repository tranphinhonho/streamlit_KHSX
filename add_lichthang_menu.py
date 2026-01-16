"""
Script thêm chức năng Lịch tháng vào menu
"""
import sqlite3
from datetime import datetime

# Đường dẫn database
database_path = "database_new.db"

# Kết nối database
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("=" * 60)
print("THÊM CHỨC NĂNG LỊCH THÁNG")
print("=" * 60)

# 1. Tìm ID của chức năng chính "Kế hoạch sản xuất"
cursor.execute("""
    SELECT ID FROM tbsys_ChucNangChinh 
    WHERE [Chức năng chính] = 'Kế hoạch sản xuất'
    LIMIT 1
""")
result = cursor.fetchone()

if result:
    id_chucnang_chinh = result[0]
    print(f"✓ Tìm thấy chức năng chính 'Kế hoạch sản xuất' (ID: {id_chucnang_chinh})")
else:
    print("✗ Không tìm thấy chức năng chính 'Kế hoạch sản xuất'")
    print("  Đang tạo mới...")
    
    # Lấy ID và thứ tự ưu tiên cao nhất
    cursor.execute("SELECT MAX(ID), MAX([Thứ tự ưu tiên]) FROM tbsys_ChucNangChinh")
    max_result = cursor.fetchone()
    new_id = (max_result[0] or 0) + 1
    new_priority = (max_result[1] or 0) + 1
    
    cursor.execute("""
        INSERT INTO tbsys_ChucNangChinh (
            ID, [Chức năng chính], [Thứ tự ưu tiên], Icon, [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (new_id, 'Kế hoạch sản xuất', new_priority, 'calendar3', 'phinho', current_time))
    
    id_chucnang_chinh = new_id
    print(f"✓ Đã tạo chức năng chính 'Kế hoạch sản xuất' (ID: {id_chucnang_chinh})")

# 2. Kiểm tra xem "Lịch tháng" đã tồn tại trong tbsys_DanhSachChucNang chưa
cursor.execute("""
    SELECT ID FROM tbsys_DanhSachChucNang 
    WHERE [Chức năng con] = 'Lịch tháng' AND [Đã xóa] = 0
    LIMIT 1
""")
existing = cursor.fetchone()

if existing:
    id_lichthang = existing[0]
    print(f"! Chức năng 'Lịch tháng' đã tồn tại (ID: {id_lichthang})")
else:
    # 3. Lấy ID và thứ tự ưu tiên cao nhất trong tbsys_DanhSachChucNang
    cursor.execute("""
        SELECT MAX(ID), MAX([Thứ tự ưu tiên]) FROM tbsys_DanhSachChucNang 
        WHERE [ID Chức năng chính] = ?
    """, (id_chucnang_chinh,))
    max_result = cursor.fetchone()
    
    # Lấy max ID toàn bảng
    cursor.execute("SELECT MAX(ID) FROM tbsys_DanhSachChucNang")
    max_id_global = cursor.fetchone()[0] or 0
    
    new_id = max_id_global + 1
    new_priority = (max_result[1] or 0) + 1
    
    # 4. Thêm chức năng con "Lịch tháng"
    cursor.execute("""
        INSERT INTO tbsys_DanhSachChucNang (
            ID, [ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên],
            Icon, [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (new_id, id_chucnang_chinh, 'Lịch tháng', new_priority, 'calendar-check', 'phinho', current_time))
    
    id_lichthang = new_id
    print(f"✓ Đã thêm chức năng con 'Lịch tháng' (ID: {id_lichthang}, Thứ tự: {new_priority})")

# 5. Kiểm tra và thêm liên kết module
cursor.execute("""
    SELECT ID FROM tbsys_ModuleChucNang 
    WHERE ID_DanhSachChucNang = ? AND [Đã xóa] = 0
    LIMIT 1
""", (id_lichthang,))
existing_module = cursor.fetchone()

if existing_module:
    print(f"! Module đã được liên kết (ID: {existing_module[0]})")
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_ModuleChucNang")
    max_module_id = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        INSERT INTO tbsys_ModuleChucNang (
            ID, ID_DanhSachChucNang, ModulePath, [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (max_module_id + 1, id_lichthang, 'PagesKDE.LichThang', 'Module lịch tháng theo dõi Stock Old, Packing, Sale', 'phinho', current_time))
    
    print(f"✓ Đã liên kết module 'PagesKDE.LichThang'")

# 6. Gán quyền cho vai trò Admin (ID = 1)
cursor.execute("""
    SELECT ID FROM tbsys_ChucNangTheoVaiTro 
    WHERE [ID Vai trò] = 1 AND [ID Danh sách chức năng] = ? AND [Đã xóa] = 0
    LIMIT 1
""", (id_lichthang,))
existing_permission = cursor.fetchone()

if existing_permission:
    print(f"! Quyền đã được gán (ID: {existing_permission[0]})")
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_ChucNangTheoVaiTro")
    max_perm_id = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        INSERT INTO tbsys_ChucNangTheoVaiTro (
            ID, [ID Vai trò], [ID Danh sách chức năng], [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, 0)
    """, (max_perm_id + 1, 1, id_lichthang, 'phinho', current_time))
    
    print(f"✓ Đã gán quyền cho vai trò Admin")

# Commit
conn.commit()

print("\n" + "=" * 60)
print("HOÀN TẤT!")
print("=" * 60)
print("\n🔄 Vui lòng refresh lại trang web (F5) để thấy menu mới")
print("📍 Menu mới: Kế hoạch sản xuất → Lịch tháng")

# Đóng kết nối
conn.close()
