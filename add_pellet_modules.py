"""
Script thêm 3 module mới vào menu: Pellet, Packing Plan, Bao bì
Chạy sau khi đã tạo database với init_database.py
"""

import sqlite3
from datetime import datetime

# Kết nối database
conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("=" * 60)
print("THÊM 3 MODULE MỚI VÀO MENU")
print("=" * 60)

# Bước 1: Kiểm tra ID Chức năng chính "Báo cáo" hoặc tạo mới nếu chưa có
print("\n[1/4] Kiểm tra chức năng chính...")

# Lấy ID của chức năng chính "Báo cáo" (hoặc tạo mới)
cursor.execute("SELECT ID FROM tbsys_ChucNangChinh WHERE [Chức năng chính] = 'Báo cáo' AND [Đã xóa] = 0")
result = cursor.fetchone()

if result:
    id_chucnang_chinh = result[0]
    print(f"✓ Đã tìm thấy chức năng chính 'Báo cáo' với ID = {id_chucnang_chinh}")
else:
    # Tạo mới chức năng chính "Báo cáo"
    cursor.execute("""
        INSERT INTO tbsys_ChucNangChinh ([Chức năng chính], Router, [Thứ tự ưu tiên], Icon, [Người tạo], [Thời gian tạo])
        VALUES ('Báo cáo', NULL, 2, 'file-text', 'phinho', ?)
    """, (current_time,))
    id_chucnang_chinh = cursor.lastrowid
    print(f"✓ Đã tạo chức năng chính 'Báo cáo' với ID = {id_chucnang_chinh}")

# Bước 2: Lấy thứ tự ưu tiên lớn nhất hiện tại
print("\n[2/4] Xác định thứ tự ưu tiên...")
cursor.execute("""
    SELECT MAX([Thứ tự ưu tiên]) 
    FROM tbsys_DanhSachChucNang 
    WHERE [ID Chức năng chính] = ? AND [Đã xóa] = 0
""", (id_chucnang_chinh,))
max_priority = cursor.fetchone()[0]
next_priority = (max_priority or 0) + 1
print(f"✓ Thứ tự ưu tiên tiếp theo: {next_priority}")

# Bước 3: Thêm 3 chức năng con mới
print("\n[3/4] Thêm chức năng con...")

new_functions = [
    (id_chucnang_chinh, 'Pellet', None, 'gear', next_priority, 'phinho', current_time),
    (id_chucnang_chinh, 'Packing Plan', None, 'package', next_priority + 1, 'phinho', current_time),
    (id_chucnang_chinh, 'Bao bì', None, 'shopping-bag', next_priority + 2, 'phinho', current_time)
]

cursor.executemany("""
    INSERT INTO tbsys_DanhSachChucNang (
        [ID Chức năng chính], [Chức năng con], Router, Icon, 
        [Thứ tự ưu tiên], [Người tạo], [Thời gian tạo]
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", new_functions)

# Lấy ID của 3 chức năng con vừa thêm
cursor.execute("""
    SELECT ID, [Chức năng con]
    FROM tbsys_DanhSachChucNang
    WHERE [Chức năng con] IN ('Pellet', 'Packing Plan', 'Bao bì')
    AND [Đã xóa] = 0
    ORDER BY [Thứ tự ưu tiên]
""")
new_ids = cursor.fetchall()
print(f"✓ Đã thêm {len(new_ids)} chức năng con:")
for id_func, name in new_ids:
    print(f"  - {name} (ID: {id_func})")

# Bước 4: Liên kết module
print("\n[4/4] Liên kết module...")

modules = []
for id_func, name in new_ids:
    if name == 'Pellet':
        module_path = 'PagesKDE.Pellet'
        description = 'Module quản lý ép viên Pellet (7 máy)'
    elif name == 'Packing Plan':
        module_path = 'PagesKDE.PackingPlan'
        description = 'Module quản lý kế hoạch đóng bao (8 lines)'
    elif name == 'Bao bì':
        module_path = 'PagesKDE.BaoBi'
        description = 'Module quản lý tồn kho bao bì với cảnh báo 3 mức'
    
    modules.append((id_func, module_path, description, 'phinho', current_time))

cursor.executemany("""
    INSERT INTO tbsys_ModuleChucNang (
        ID_DanhSachChucNang, ModulePath, [Ghi chú], [Người tạo], [Thời gian tạo]
    ) VALUES (?, ?, ?, ?, ?)
""", modules)
print(f"✓ Đã liên kết {len(modules)} module")

# Bước 5: Gán quyền cho Admin (ID Vai trò = 1)
print("\n[5/5] Gán quyền cho vai trò Admin...")

permissions = []
for id_func, name in new_ids:
    permissions.append((1, id_func, 'phinho', current_time))

cursor.executemany("""
    INSERT INTO tbsys_ChucNangTheoVaiTro (
        [ID Vai trò], [ID Danh sách chức năng], [Người tạo], [Thời gian tạo]
    ) VALUES (?, ?, ?, ?)
""", permissions)
print(f"✓ Đã gán {len(permissions)} quyền cho Admin")

# Commit tất cả thay đổi
conn.commit()

print("\n" + "=" * 60)
print("HOÀN TẤT THÊM MODULE")
print("=" * 60)
print("\n✅ Đã thêm thành công 3 module mới:")
print("  1. Pellet - Quản lý ép viên (7 máy: 10+10+9+9+8+8+8 tấn/giờ)")
print("  2. Packing Plan - Kế hoạch đóng bao (8 lines)")
print("  3. Bao bì - Quản lý tồn kho với cảnh báo 3 mức")
print("\n🔄 BƯỚC TIẾP THEO:")
print("  1. Khởi động lại Streamlit: streamlit run main.py")
print("  2. Đăng nhập với tài khoản Admin")
print("  3. Kiểm tra menu 'Báo cáo' - sẽ thấy 3 module mới")
print("\n" + "=" * 60)

# Đóng kết nối
cursor.close()
conn.close()

print("\n✓ Đã đóng kết nối database")
print("✓ Hoàn tất!")
