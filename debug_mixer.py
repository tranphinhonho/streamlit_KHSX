"""
Script kiểm tra và debug menu Mixer
"""
import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

print("=" * 60)
print("KIỂM TRA MENU MIXER")
print("=" * 60)

# 1. Kiểm tra tbsys_DanhSachChucNang
print("\n1. DANH SÁCH CHỨC NĂNG:")
cursor.execute("""
    SELECT ID, [Chức năng con], [Thứ tự ưu tiên], [ID Chức năng chính] 
    FROM tbsys_DanhSachChucNang 
    WHERE [Đã xóa] = 0 
    ORDER BY [ID Chức năng chính], [Thứ tự ưu tiên]
""")
for r in cursor.fetchall():
    marker = " <-- MIXER" if 'Mixer' in str(r[1]) else ""
    print(f"  ID={r[0]}, TT={r[2]}, IDCC={r[3]}: {r[1]}{marker}")

# 2. Kiểm tra tbsys_ModuleChucNang
print("\n2. MODULE CHỨC NĂNG:")
cursor.execute("""
    SELECT m.ID, m.ID_DanhSachChucNang, m.ModulePath, d.[Chức năng con]
    FROM tbsys_ModuleChucNang m
    LEFT JOIN tbsys_DanhSachChucNang d ON m.ID_DanhSachChucNang = d.ID
    WHERE m.[Đã xóa] = 0
    ORDER BY m.ID
""")
for r in cursor.fetchall():
    marker = " <-- MIXER" if 'Mixer' in str(r[2]) else ""
    print(f"  ID={r[0]}, DSCN_ID={r[1]}: {r[2]} ({r[3]}){marker}")

# 3. Kiểm tra ChucNangTheoVaiTro cho Admin
print("\n3. QUYỀN ADMIN (ID Vai trò = 1):")
cursor.execute("""
    SELECT cv.ID, cv.[ID Danh sách chức năng], d.[Chức năng con]
    FROM tbsys_ChucNangTheoVaiTro cv
    LEFT JOIN tbsys_DanhSachChucNang d ON cv.[ID Danh sách chức năng] = d.ID
    WHERE cv.[ID Vai trò] = 1 AND cv.[Đã xóa] = 0
    ORDER BY d.[Thứ tự ưu tiên]
""")
for r in cursor.fetchall():
    marker = " <-- MIXER" if 'Mixer' in str(r[2]) else ""
    print(f"  ID={r[0]}, DSCN_ID={r[1]}: {r[2]}{marker}")

# 4. Tìm Mixer cụ thể
print("\n4. TÌM MIXER:")
cursor.execute("SELECT * FROM tbsys_DanhSachChucNang WHERE [Chức năng con] LIKE '%Mixer%'")
mixer_records = cursor.fetchall()
if mixer_records:
    col_names = [d[0] for d in cursor.description]
    for r in mixer_records:
        print(f"  Found: {dict(zip(col_names, r))}")
else:
    print("  KHÔNG TÌM THẤY MIXER TRONG tbsys_DanhSachChucNang!")

conn.close()
