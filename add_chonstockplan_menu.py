"""
Script để thêm menu item 'Chọn Stock Plan' vào database
"""
import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# 1. Tìm ID Chức năng chính "Stock" (hoặc tương tự)
c.execute("""
    SELECT ID FROM tbsys_ChucNangChinh 
    WHERE [Chức năng chính] LIKE '%Stock%' OR [Chức năng chính] LIKE '%Kế hoạch%'
    LIMIT 1
""")
result = c.fetchone()

if result:
    id_chucnang_chinh = result[0]
    print(f"✅ Tìm thấy Chức năng chính: ID = {id_chucnang_chinh}")
else:
    # Nếu không tìm thấy, lấy chức năng chính đầu tiên
    c.execute("SELECT ID FROM tbsys_ChucNangChinh LIMIT 1")
    result = c.fetchone()
    if result:
        id_chucnang_chinh = result[0]
        print(f"⚠️ Dùng Chức năng chính mặc định: ID = {id_chucnang_chinh}")
    else:
        print("❌ Không tìm thấy Chức năng chính nào!")
        conn.close()
        exit()

# 2. Kiểm tra xem đã có 'Chọn Stock Plan' chưa
c.execute("""
    SELECT ID FROM tbsys_DanhSachChucNang 
    WHERE [Chức năng con] = 'Chọn Stock Plan'
""")
existing = c.fetchone()

if existing:
    print(f"⚠️ Menu 'Chọn Stock Plan' đã tồn tại với ID = {existing[0]}")
    id_danhsach = existing[0]
else:
    # 3. Thêm vào tbsys_DanhSachChucNang
    c.execute("""
        INSERT INTO tbsys_DanhSachChucNang ([ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên], [Đã xóa], [Người tạo], [Thời gian tạo])
        VALUES (?, 'Chọn Stock Plan', 2, 0, 'system', datetime('now'))
    """, (id_chucnang_chinh,))
    
    id_danhsach = c.lastrowid
    print(f"✅ Đã thêm 'Chọn Stock Plan' vào tbsys_DanhSachChucNang với ID = {id_danhsach}")

# 4. Kiểm tra tbsys_ModuleChucNang
c.execute("""
    SELECT ID FROM tbsys_ModuleChucNang 
    WHERE ID_DanhSachChucNang = ?
""", (id_danhsach,))
existing_module = c.fetchone()

if existing_module:
    print(f"⚠️ Module liên kết đã tồn tại với ID = {existing_module[0]}")
else:
    # 5. Thêm liên kết module
    c.execute("""
        INSERT INTO tbsys_ModuleChucNang (ID_DanhSachChucNang, [Chức năng con], ModulePath, [Đã xóa], [Người tạo], [Thời gian tạo])
        VALUES (?, 'Chọn Stock Plan', 'PagesKDE.ChonStockPlan', 0, 'system', datetime('now'))
    """, (id_danhsach,))
    print(f"✅ Đã thêm liên kết module 'PagesKDE.ChonStockPlan'")

# 6. Thêm vào tbsys_ChucNangTheoVaiTro cho tất cả vai trò
c.execute("SELECT DISTINCT [ID Vai trò] FROM tbsys_ChucNangTheoVaiTro WHERE [Đã xóa] = 0")
roles = c.fetchall()

for role in roles:
    role_id = role[0]
    c.execute("""
        SELECT ID FROM tbsys_ChucNangTheoVaiTro 
        WHERE [ID Vai trò] = ? AND [ID Danh sách chức năng] = ?
    """, (role_id, id_danhsach))
    
    if not c.fetchone():
        c.execute("""
            INSERT INTO tbsys_ChucNangTheoVaiTro ([ID Vai trò], [ID Danh sách chức năng], [Đã xóa], [Người tạo], [Thời gian tạo])
            VALUES (?, ?, 0, 'system', datetime('now'))
        """, (role_id, id_danhsach))
        print(f"✅ Đã thêm quyền cho vai trò ID = {role_id}")

conn.commit()
conn.close()

print("\n🎉 Hoàn tất! Vui lòng refresh trang Streamlit để thấy menu mới.")
