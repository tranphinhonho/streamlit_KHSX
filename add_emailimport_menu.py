"""
Script thêm chức năng Nhận email vào menu
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
print("THÊM CHỨC NĂNG NHẬN EMAIL")
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
    conn.close()
    exit(1)

# 2. Kiểm tra xem "Nhận email" đã tồn tại chưa
cursor.execute("""
    SELECT ID FROM tbsys_DanhSachChucNang 
    WHERE [Chức năng con] = 'Nhận email' AND [Đã xóa] = 0
    LIMIT 1
""")
existing = cursor.fetchone()

if existing:
    id_nhanemail = existing[0]
    print(f"! Chức năng 'Nhận email' đã tồn tại (ID: {id_nhanemail})")
else:
    # 3. Lấy ID và thứ tự ưu tiên
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
    
    # 4. Thêm chức năng con "Nhận email"
    cursor.execute("""
        INSERT INTO tbsys_DanhSachChucNang (
            ID, [ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên],
            Icon, [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (new_id, id_chucnang_chinh, 'Nhận email', new_priority, 'envelope-arrow-down', 'phinho', current_time))
    
    id_nhanemail = new_id
    print(f"✓ Đã thêm chức năng con 'Nhận email' (ID: {id_nhanemail}, Thứ tự: {new_priority})")

# 5. Kiểm tra và thêm liên kết module
cursor.execute("""
    SELECT ID FROM tbsys_ModuleChucNang 
    WHERE ID_DanhSachChucNang = ? AND [Đã xóa] = 0
    LIMIT 1
""", (id_nhanemail,))
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
    """, (max_module_id + 1, id_nhanemail, 'PagesKDE.EmailImport', 'Module nhận email và import FFSTOCK', 'phinho', current_time))
    
    print(f"✓ Đã liên kết module 'PagesKDE.EmailImport'")

# 6. Gán quyền cho vai trò Admin (ID = 1)
cursor.execute("""
    SELECT ID FROM tbsys_ChucNangTheoVaiTro 
    WHERE [ID Vai trò] = 1 AND [ID Danh sách chức năng] = ? AND [Đã xóa] = 0
    LIMIT 1
""", (id_nhanemail,))
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
    """, (max_perm_id + 1, 1, id_nhanemail, 'phinho', current_time))
    
    print(f"✓ Đã gán quyền cho vai trò Admin")

# Commit
conn.commit()

print("\n" + "=" * 60)
print("HOÀN TẤT!")
print("=" * 60)
print("\n🔄 Vui lòng refresh lại trang web (F5) để thấy menu mới")
print("📍 Menu mới: Kế hoạch sản xuất → Nhận email")

# Đóng kết nối
conn.close()
