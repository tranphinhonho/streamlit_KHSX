# -*- coding: utf-8 -*-
"""
Add TonBon menu under Ke hoach san xuat (ID = 3)
Position: after Batching
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("=" * 60)
print("ADD TONBON MENU")
print("=" * 60)

# Get ID for Ke hoach san xuat
cursor.execute("SELECT ID FROM tbsys_ChucNangChinh WHERE [Chức năng chính] = 'Kế hoạch sản xuất'")
result = cursor.fetchone()
id_chucnang_chinh = result[0] if result else 3
print(f"1. ID Chuc nang chinh: {id_chucnang_chinh}")

# Get priority of Batching
cursor.execute("SELECT [Thứ tự ưu tiên] FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Batching' AND [Đã xóa] = 0")
batching = cursor.fetchone()
batching_priority = batching[0] if batching else 8
print(f"2. Batching priority: {batching_priority}")

# TonBon priority = Batching + 2
tonbon_priority = batching_priority + 2
print(f"3. TonBon priority: {tonbon_priority}")

# Check if TonBon already exists
cursor.execute("SELECT ID FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Tồn bồn'")
existing = cursor.fetchone()

if existing:
    id_tonbon = existing[0]
    print(f"4. TonBon already exists (ID: {id_tonbon})")
    cursor.execute("UPDATE tbsys_DanhSachChucNang SET [Đã xóa] = 0 WHERE ID = ?", (id_tonbon,))
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_DanhSachChucNang")
    max_id = cursor.fetchone()[0] or 0
    
    id_tonbon = max_id + 1
    
    cursor.execute("""
        INSERT INTO tbsys_DanhSachChucNang (
            ID, [ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên],
            Icon, [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, 'Tồn bồn', ?, 'database', 'phinho', ?, 0)
    """, (id_tonbon, id_chucnang_chinh, tonbon_priority, current_time))
    
    print(f"4. Created TonBon (ID: {id_tonbon})")

conn.commit()

# Add module link
cursor.execute("SELECT ID FROM tbsys_ModuleChucNang WHERE ID_DanhSachChucNang = ? AND [Đã xóa] = 0", (id_tonbon,))
existing_module = cursor.fetchone()

if existing_module:
    cursor.execute("UPDATE tbsys_ModuleChucNang SET ModulePath = 'PagesKDE.TonBon' WHERE ID = ?", (existing_module[0],))
    print(f"5. Updated module path (ID: {existing_module[0]})")
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_ModuleChucNang")
    max_module_id = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        INSERT INTO tbsys_ModuleChucNang (
            ID, ID_DanhSachChucNang, ModulePath, [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, 'PagesKDE.TonBon', 'Module ton bon', 'phinho', ?, 0)
    """, (max_module_id + 1, id_tonbon, current_time))
    
    print(f"5. Created module link (ID: {max_module_id + 1})")

conn.commit()

# Add permission for Admin
cursor.execute("SELECT ID FROM tbsys_ChucNangTheoVaiTro WHERE [ID Vai trò] = 1 AND [ID Danh sách chức năng] = ?", (id_tonbon,))
existing_perm = cursor.fetchone()

if existing_perm:
    cursor.execute("UPDATE tbsys_ChucNangTheoVaiTro SET [Đã xóa] = 0 WHERE ID = ?", (existing_perm[0],))
    print(f"6. Updated permission (ID: {existing_perm[0]})")
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_ChucNangTheoVaiTro")
    max_perm_id = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        INSERT INTO tbsys_ChucNangTheoVaiTro (
            ID, [ID Vai trò], [ID Danh sách chức năng], [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, 1, ?, 'phinho', ?, 0)
    """, (max_perm_id + 1, id_tonbon, current_time))
    
    print(f"6. Created permission (ID: {max_perm_id + 1})")

conn.commit()

# Verification
print("\n" + "=" * 60)
print("VERIFICATION:")
print("=" * 60)
cursor.execute("""
    SELECT d.[Chức năng con], d.[Thứ tự ưu tiên], m.ModulePath
    FROM tbsys_DanhSachChucNang d
    LEFT JOIN tbsys_ModuleChucNang m ON d.ID = m.ID_DanhSachChucNang AND m.[Đã xóa] = 0
    WHERE d.[ID Chức năng chính] = ? AND d.[Đã xóa] = 0
    ORDER BY d.[Thứ tự ưu tiên]
""", (id_chucnang_chinh,))
for r in cursor.fetchall():
    marker = " <-- NEW" if r[0] == 'Tồn bồn' else ""
    print(f"   {r[0]} (TT={r[1]}) -> {r[2]}{marker}")

conn.close()
print("\nDONE! Refresh page F5")
