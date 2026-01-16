# -*- coding: utf-8 -*-
"""
Script them chuc nang Mixer vao menu
Vi tri: giua Bao bi va Lich thang
"""
import sqlite3
from datetime import datetime

# Database path
database_path = "database_new.db"

# Connect
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("=" * 60)
print("THEM CHUC NANG MIXER VAO MENU")
print("=" * 60)

# 1. Find ID of main function "Ke hoach san xuat"
cursor.execute("""
    SELECT ID FROM tbsys_ChucNangChinh 
    WHERE [Chức năng chính] = 'Kế hoạch sản xuất'
    LIMIT 1
""")
result = cursor.fetchone()

if result:
    id_chucnang_chinh = result[0]
    print(f"OK: Found main function (ID: {id_chucnang_chinh})")
else:
    print("ERROR: Main function not found")
    conn.close()
    exit(1)

# 2. Find priority of Bao bi
cursor.execute("""
    SELECT [Thứ tự ưu tiên] FROM tbsys_DanhSachChucNang 
    WHERE [Chức năng con] = 'Bao bì' AND [Đã xóa] = 0
    LIMIT 1
""")
baobi_result = cursor.fetchone()
baobi_priority = baobi_result[0] if baobi_result else 100
print(f"OK: Bao bi priority = {baobi_priority}")

# Mixer priority = baobi + 5
mixer_priority = baobi_priority + 5
print(f"OK: Mixer priority = {mixer_priority}")

# 3. Check if Mixer already exists
cursor.execute("""
    SELECT ID FROM tbsys_DanhSachChucNang 
    WHERE [Chức năng con] = 'Mixer' AND [Đã xóa] = 0
    LIMIT 1
""")
existing = cursor.fetchone()

if existing:
    id_mixer = existing[0]
    print(f"INFO: Mixer already exists (ID: {id_mixer})")
else:
    # Get max ID
    cursor.execute("SELECT MAX(ID) FROM tbsys_DanhSachChucNang")
    max_id_global = cursor.fetchone()[0] or 0
    
    new_id = max_id_global + 1
    
    # Insert Mixer
    cursor.execute("""
        INSERT INTO tbsys_DanhSachChucNang (
            ID, [ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên],
            Icon, [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (new_id, id_chucnang_chinh, 'Mixer', mixer_priority, 'sliders', 'phinho', current_time))
    
    id_mixer = new_id
    print(f"OK: Added Mixer (ID: {id_mixer}, Priority: {mixer_priority})")

# 4. Link module
cursor.execute("""
    SELECT ID FROM tbsys_ModuleChucNang 
    WHERE ID_DanhSachChucNang = ? AND [Đã xóa] = 0
    LIMIT 1
""", (id_mixer,))
existing_module = cursor.fetchone()

if existing_module:
    print(f"INFO: Module already linked (ID: {existing_module[0]})")
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_ModuleChucNang")
    max_module_id = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        INSERT INTO tbsys_ModuleChucNang (
            ID, ID_DanhSachChucNang, ModulePath, [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (max_module_id + 1, id_mixer, 'PagesKDE.Mixer', 'Module mixer', 'phinho', current_time))
    
    print(f"OK: Linked module PagesKDE.Mixer")

# 5. Assign permission to Admin (ID = 1)
cursor.execute("""
    SELECT ID FROM tbsys_ChucNangTheoVaiTro 
    WHERE [ID Vai trò] = 1 AND [ID Danh sách chức năng] = ? AND [Đã xóa] = 0
    LIMIT 1
""", (id_mixer,))
existing_permission = cursor.fetchone()

if existing_permission:
    print(f"INFO: Permission already assigned (ID: {existing_permission[0]})")
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_ChucNangTheoVaiTro")
    max_perm_id = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        INSERT INTO tbsys_ChucNangTheoVaiTro (
            ID, [ID Vai trò], [ID Danh sách chức năng], [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, ?, ?, ?, 0)
    """, (max_perm_id + 1, 1, id_mixer, 'phinho', current_time))
    
    print(f"OK: Assigned permission to Admin")

# Commit
conn.commit()

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
print("\nPlease refresh the web page (F5)")

# Close connection
conn.close()
