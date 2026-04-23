# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Đổi tên Pellet Plan -> Pelleting
cursor.execute("""
    UPDATE tbsys_DanhSachChucNang 
    SET [Chức năng con] = 'Pelleting'
    WHERE [Chức năng con] = 'Pellet Plan' AND [Đã xóa] = 0
""")
pellet_count = cursor.rowcount
print(f"Đổi 'Pellet Plan' → 'Pelleting': {pellet_count} dòng")

# Đổi tên Packing -> Pack
cursor.execute("""
    UPDATE tbsys_DanhSachChucNang 
    SET [Chức năng con] = 'Pack'
    WHERE [Chức năng con] = 'Packing' AND [Đã xóa] = 0
""")
packing_count = cursor.rowcount
print(f"Đổi 'Packing' → 'Pack': {packing_count} dòng")

conn.commit()
conn.close()

print("✅ Hoàn tất! Refresh browser để xem thay đổi.")
