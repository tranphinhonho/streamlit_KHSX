# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Đổi tên các item thuộc "Theo dõi chất lượng" (ID Chức năng chính = 5)

# QC Pack → QC Packing
cursor.execute("""
    UPDATE tbsys_DanhSachChucNang 
    SET [Chức năng con] = 'QC Packing'
    WHERE [Chức năng con] = 'QC Pack' AND [ID Chức năng chính] = 5
""")
print(f"QC Pack → 'QC Packing': {cursor.rowcount} dòng")

# QC Pelleting → QC Pellet
cursor.execute("""
    UPDATE tbsys_DanhSachChucNang 
    SET [Chức năng con] = 'QC Pellet'
    WHERE [Chức năng con] = 'QC Pelleting' AND [ID Chức năng chính] = 5
""")
print(f"QC Pelleting → 'QC Pellet': {cursor.rowcount} dòng")

conn.commit()
conn.close()

print("\n✅ Hoàn tất!")
