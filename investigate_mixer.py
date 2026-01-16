# -*- coding: utf-8 -*-
"""
Complete investigation of Mixer menu issue
"""
import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

print("=" * 70)
print("COMPLETE MIXER INVESTIGATION")
print("=" * 70)

# 1. Show all ChucNangChinh (main functions)
print("\n1. MAIN FUNCTIONS (tbsys_ChucNangChinh):")
cursor.execute("SELECT ID, [Chức năng chính] FROM tbsys_ChucNangChinh WHERE [Đã xóa] = 0")
for r in cursor.fetchall():
    print(f"   ID={r[0]}: {r[1]}")

# 2. Show all sub-functions under "Ke hoach san xuat"
print("\n2. SUB-FUNCTIONS under 'Ke hoach san xuat' (ID Chuc nang chinh = ?):")
cursor.execute("SELECT ID FROM tbsys_ChucNangChinh WHERE [Chức năng chính] = 'Kế hoạch sản xuất'")
cc_result = cursor.fetchone()
if cc_result:
    id_cc = cc_result[0]
    print(f"   Found: ID Chuc nang chinh = {id_cc}")
    cursor.execute("""
        SELECT d.ID, d.[Chức năng con], d.[Thứ tự ưu tiên], d.[ID Chức năng chính], d.[Đã xóa]
        FROM tbsys_DanhSachChucNang d
        WHERE d.[ID Chức năng chính] = ?
        ORDER BY d.[Thứ tự ưu tiên]
    """, (id_cc,))
    for r in cursor.fetchall():
        deleted = "(DELETED)" if r[4] == 1 else ""
        mixer_mark = " <-- MIXER" if r[1] == 'Mixer' else ""
        print(f"   ID={r[0]}, TT={r[2]}, IDCC={r[3]}, Da xoa={r[4]}: {r[1]} {deleted}{mixer_mark}")

# 3. Check Mixer specifically
print("\n3. MIXER RECORD DETAILS:")
cursor.execute("SELECT * FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Mixer'")
mixer = cursor.fetchone()
if mixer:
    col_names = [d[0] for d in cursor.description]
    for i, col in enumerate(col_names):
        print(f"   {col}: {mixer[i]}")
else:
    print("   MIXER NOT FOUND IN DATABASE!")

# 4. Check module link
print("\n4. MODULE LINK FOR MIXER:")
cursor.execute("""
    SELECT m.*, d.[Chức năng con]
    FROM tbsys_ModuleChucNang m 
    JOIN tbsys_DanhSachChucNang d ON m.ID_DanhSachChucNang = d.ID
    WHERE d.[Chức năng con] = 'Mixer'
""")
module = cursor.fetchone()
if module:
    print(f"   Module found: {module}")
else:
    print("   NO MODULE LINK FOUND!")

# 5. Check permission for Admin
print("\n5. PERMISSION FOR MIXER:")
cursor.execute("""
    SELECT cv.*, d.[Chức năng con]
    FROM tbsys_ChucNangTheoVaiTro cv
    JOIN tbsys_DanhSachChucNang d ON cv.[ID Danh sách chức năng] = d.ID
    WHERE d.[Chức năng con] = 'Mixer' AND cv.[ID Vai trò] = 1
""")
perm = cursor.fetchone()
if perm:
    print(f"   Permission found: {perm}")
else:
    print("   NO PERMISSION FOR ADMIN!")

# 6. Compare with working menu item like "Bao bi"
print("\n6. COMPARISON WITH 'Bao bi' (working):")
cursor.execute("SELECT * FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Bao bì'")
baobi = cursor.fetchone()
if baobi:
    col_names = [d[0] for d in cursor.description]
    for i, col in enumerate(col_names):
        print(f"   {col}: {baobi[i]}")

conn.close()
