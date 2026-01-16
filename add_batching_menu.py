# -*- coding: utf-8 -*-
"""
Add Batching menu under Ke hoach san xuat (ID = 3)
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("=" * 60)
print("ADD BATCHING MENU")
print("=" * 60)

# Check ID for Ke hoach san xuat - should be 3 based on image
cursor.execute("SELECT ID FROM tbsys_ChucNangChinh WHERE [Chức năng chính] = 'Kế hoạch sản xuất'")
result = cursor.fetchone()
id_chucnang_chinh = result[0] if result else 3
print(f"1. ID Chuc nang chinh (Ke hoach san xuat): {id_chucnang_chinh}")

# Get priority of Bao bi
cursor.execute("SELECT [Thứ tự ưu tiên] FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Bao bì' AND [Đã xóa] = 0")
baobi = cursor.fetchone()
baobi_priority = baobi[0] if baobi else 100
print(f"2. Bao bi priority: {baobi_priority}")

# Batching priority = Bao bi + 5
batching_priority = baobi_priority + 5
print(f"3. Batching priority: {batching_priority}")

# Check if Batching already exists
cursor.execute("SELECT ID FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Batching'")
existing = cursor.fetchone()

if existing:
    id_batching = existing[0]
    print(f"4. Batching already exists (ID: {id_batching})")
    # Make sure it's not deleted
    cursor.execute("UPDATE tbsys_DanhSachChucNang SET [Đã xóa] = 0 WHERE ID = ?", (id_batching,))
else:
    # Get max ID
    cursor.execute("SELECT MAX(ID) FROM tbsys_DanhSachChucNang")
    max_id = cursor.fetchone()[0] or 0
    
    id_batching = max_id + 1
    
    # Insert Batching
    cursor.execute("""
        INSERT INTO tbsys_DanhSachChucNang (
            ID, [ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên],
            Icon, [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, 'Batching', ?, 'sliders', 'phinho', ?, 0)
    """, (id_batching, id_chucnang_chinh, batching_priority, current_time))
    
    print(f"4. Created Batching (ID: {id_batching})")

conn.commit()

# Add module link
cursor.execute("SELECT ID FROM tbsys_ModuleChucNang WHERE ID_DanhSachChucNang = ? AND [Đã xóa] = 0", (id_batching,))
existing_module = cursor.fetchone()

if existing_module:
    # Update path to PagesKDE.Batching
    cursor.execute("UPDATE tbsys_ModuleChucNang SET ModulePath = 'PagesKDE.Batching' WHERE ID = ?", (existing_module[0],))
    print(f"5. Updated module path (ID: {existing_module[0]})")
else:
    cursor.execute("SELECT MAX(ID) FROM tbsys_ModuleChucNang")
    max_module_id = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        INSERT INTO tbsys_ModuleChucNang (
            ID, ID_DanhSachChucNang, ModulePath, [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa]
        ) VALUES (?, ?, 'PagesKDE.Batching', 'Module batching', 'phinho', ?, 0)
    """, (max_module_id + 1, id_batching, current_time))
    
    print(f"5. Created module link (ID: {max_module_id + 1})")

conn.commit()

# Add permission for Admin
cursor.execute("SELECT ID FROM tbsys_ChucNangTheoVaiTro WHERE [ID Vai trò] = 1 AND [ID Danh sách chức năng] = ?", (id_batching,))
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
    """, (max_perm_id + 1, id_batching, current_time))
    
    print(f"6. Created permission (ID: {max_perm_id + 1})")

conn.commit()

# Verification
print("\n" + "=" * 60)
print("VERIFICATION - Menu under Ke hoach san xuat:")
print("=" * 60)
cursor.execute("""
    SELECT d.ID, d.[Chức năng con], d.[Thứ tự ưu tiên], m.ModulePath
    FROM tbsys_DanhSachChucNang d
    LEFT JOIN tbsys_ModuleChucNang m ON d.ID = m.ID_DanhSachChucNang AND m.[Đã xóa] = 0
    WHERE d.[ID Chức năng chính] = ? AND d.[Đã xóa] = 0
    ORDER BY d.[Thứ tự ưu tiên]
""", (id_chucnang_chinh,))
for r in cursor.fetchall():
    marker = " <-- NEW" if r[1] == 'Batching' else ""
    print(f"   {r[1]} (ID={r[0]}, TT={r[2]}) -> {r[3]}{marker}")

conn.close()
print("\nDONE! Refresh page F5")
