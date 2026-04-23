# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Xem cấu trúc bảng SanPham
cursor.execute("PRAGMA table_info(SanPham)")
columns = cursor.fetchall()
print("Cột trong bảng SanPham:")
for c in columns:
    print(f"  {c[1]} ({c[2]})")

# Xem một vài dòng dữ liệu mẫu
cursor.execute("SELECT * FROM SanPham WHERE [Đã xóa] = 0 LIMIT 3")
data = cursor.fetchall()
print("\nDữ liệu mẫu:")
for d in data:
    print(f"  {d}")

conn.close()
