# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Lấy danh sách hiện tại
cursor.execute("""
    SELECT ID, [Chức năng con] 
    FROM tbsys_DanhSachChucNang 
    WHERE [Đã xóa] = 0 
    AND [Chức năng con] IN ('Hammer', 'Mixer', 'Pelleting', 'Pack')
""")
current = cursor.fetchall()
print("Trước khi đổi:")
for r in current:
    print(f"  ID {r[0]}: {r[1]}")

# Tìm và đổi tên các item thuộc "Theo dõi chất lượng"
# Cần tìm ID của chức năng chính "Theo dõi chất lượng"
cursor.execute("""
    SELECT ID FROM tbsys_ChucNangChinh 
    WHERE LOWER([Chức năng chính]) LIKE '%theo dõi%' OR LOWER([Chức năng chính]) LIKE '%chất lượng%'
    AND [Đã xóa] = 0
""")
qc_main = cursor.fetchone()
print(f"\nChức năng chính 'Theo dõi chất lượng' ID: {qc_main}")

# Xem cấu trúc tbsys_DanhSachChucNang
cursor.execute("PRAGMA table_info(tbsys_DanhSachChucNang)")
columns = cursor.fetchall()
print("\nColumns in tbsys_DanhSachChucNang:")
for c in columns:
    print(f"  {c}")

# Xem dữ liệu chi tiết
cursor.execute("""
    SELECT * FROM tbsys_DanhSachChucNang 
    WHERE [Đã xóa] = 0 
    AND [Chức năng con] IN ('Hammer', 'Mixer', 'Pelleting', 'Pack')
""")
data = cursor.fetchall()
print("\nChi tiết:")
for d in data:
    print(f"  {d}")

conn.close()
