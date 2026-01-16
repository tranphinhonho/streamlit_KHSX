# -*- coding: utf-8 -*-
"""
Check Mixer in database
"""
import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check Mixer exists
cursor.execute("SELECT ID FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Mixer'")
result = cursor.fetchall()
print(f"Mixer in DanhSachChucNang: {result}")

# Check module link
cursor.execute("SELECT * FROM tbsys_ModuleChucNang WHERE ModulePath LIKE '%Mixer%'")
result2 = cursor.fetchall()
print(f"Mixer module: {result2}")

# Check permission
cursor.execute("""
    SELECT cv.*, d.[Chức năng con] 
    FROM tbsys_ChucNangTheoVaiTro cv
    JOIN tbsys_DanhSachChucNang d ON cv.[ID Danh sách chức năng] = d.ID
    WHERE d.[Chức năng con] = 'Mixer'
""")
result3 = cursor.fetchall()
print(f"Mixer permission: {result3}")

conn.close()
