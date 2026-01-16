# -*- coding: utf-8 -*-
"""
Final fix for Mixer module with full details
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print("=" * 60)
print("FULL MIXER DIAGNOSIS AND FIX")
print("=" * 60)

# 1. Get Mixer ID
cursor.execute("SELECT ID, [Chức năng con] FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Mixer'")
mixer = cursor.fetchone()
print(f"\n1. DanhSachChucNang:")
print(f"   Mixer: {mixer}")

if mixer:
    id_mixer = mixer[0]
    
    # 2. Get all module links for this ID
    cursor.execute("SELECT ID, ID_DanhSachChucNang, ModulePath, [Đã xóa] FROM tbsys_ModuleChucNang WHERE ID_DanhSachChucNang = ?", (id_mixer,))
    modules = cursor.fetchall()
    print(f"\n2. ModuleChucNang for Mixer ID {id_mixer}:")
    for m in modules:
        print(f"   ID={m[0]}, Path={m[2]}, Deleted={m[3]}")
    
    # 3. Fix wrong path or add if missing
    if modules:
        for m in modules:
            if m[2] != 'PagesKDE.Mixer':
                print(f"\n3. FIXING: Module ID {m[0]} has wrong path '{m[2]}'")
                cursor.execute("UPDATE tbsys_ModuleChucNang SET ModulePath = 'PagesKDE.Mixer', [Đã xóa] = 0 WHERE ID = ?", (m[0],))
                conn.commit()
                print(f"   -> Updated to 'PagesKDE.Mixer'")
            else:
                print(f"\n3. Module ID {m[0]} path is correct")
                if m[3] == 1:  # If deleted
                    cursor.execute("UPDATE tbsys_ModuleChucNang SET [Đã xóa] = 0 WHERE ID = ?", (m[0],))
                    conn.commit()
                    print(f"   -> Undeleted")
    else:
        print(f"\n3. NO MODULE FOUND - Creating new...")
        cursor.execute("SELECT MAX(ID) FROM tbsys_ModuleChucNang")
        max_id = cursor.fetchone()[0] or 0
        cursor.execute("""
            INSERT INTO tbsys_ModuleChucNang (
                ID, ID_DanhSachChucNang, ModulePath, [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa]
            ) VALUES (?, ?, 'PagesKDE.Mixer', 'Module mixer', 'phinho', ?, 0)
        """, (max_id + 1, id_mixer, current_time))
        conn.commit()
        print(f"   -> Created module ID {max_id + 1}")

# 4. Verify
print(f"\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)
cursor.execute("""
    SELECT d.[Chức năng con], m.ModulePath, m.[Đã xóa]
    FROM tbsys_DanhSachChucNang d
    LEFT JOIN tbsys_ModuleChucNang m ON d.ID = m.ID_DanhSachChucNang
    WHERE d.[Chức năng con] = 'Mixer'
""")
result = cursor.fetchall()
for r in result:
    status = "ACTIVE" if r[2] == 0 else "DELETED"
    print(f"   Function: {r[0]} -> Module: {r[1]} ({status})")

conn.close()
print("\nDONE! Refresh page F5")
