# -*- coding: utf-8 -*-
"""
Hide Tien doan AI menu
"""
import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Soft delete Tien doan AI
cursor.execute("UPDATE tbsys_DanhSachChucNang SET [Đã xóa] = 1 WHERE [Chức năng con] = 'Tiên đoán AI'")
conn.commit()
print(f"Rows affected: {cursor.rowcount}")

# Verify
cursor.execute("SELECT [Chức năng con], [Đã xóa] FROM tbsys_DanhSachChucNang WHERE [Chức năng con] = 'Tiên đoán AI'")
result = cursor.fetchone()
if result:
    print(f"Tien doan AI: Da xoa = {result[1]}")
else:
    print("Not found")

conn.close()
print("\nDONE! Refresh page F5")
