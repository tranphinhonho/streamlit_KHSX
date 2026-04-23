# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Đổi tên các item thuộc "Theo dõi chất lượng" (ID Chức năng chính = 5)
updates = [
    (6, 'QC Hammer'),
    (7, 'QC Mixer'),
    (8, 'QC Pelleting'),
    (9, 'QC Pack')
]

for id_val, new_name in updates:
    cursor.execute("""
        UPDATE tbsys_DanhSachChucNang 
        SET [Chức năng con] = ?
        WHERE ID = ? AND [ID Chức năng chính] = 5
    """, (new_name, id_val))
    print(f"ID {id_val} → '{new_name}'")

conn.commit()
conn.close()

print("\n✅ Hoàn tất! Refresh browser để xem thay đổi.")
