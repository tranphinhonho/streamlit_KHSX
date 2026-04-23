# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Đổi tên các item thuộc "Kế hoạch sản xuất" (không phải ID 5 - Theo dõi chất lượng)

# ID 12: Pack → Packing (ID Chức năng chính = 3)
cursor.execute("""
    UPDATE tbsys_DanhSachChucNang 
    SET [Chức năng con] = 'Packing'
    WHERE ID = 12 AND [ID Chức năng chính] = 3
""")
print(f"ID 12 Pack → 'Packing': {cursor.rowcount} dòng")

# ID 18: Pelleting → Pellet Plan (ID Chức năng chính = 2)
cursor.execute("""
    UPDATE tbsys_DanhSachChucNang 
    SET [Chức năng con] = 'Pellet Plan'
    WHERE ID = 18 AND [ID Chức năng chính] = 2
""")
print(f"ID 18 Pelleting → 'Pellet Plan': {cursor.rowcount} dòng")

conn.commit()
conn.close()

print("\n✅ Hoàn tất! Refresh browser để xem thay đổi.")
