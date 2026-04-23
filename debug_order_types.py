# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Get distinct order types
cursor.execute("SELECT DISTINCT [Loại đặt hàng] FROM DatHang WHERE [Đã xóa] = 0")
results = cursor.fetchall()
print("Loại đặt hàng:")
for r in results:
    print(f"  - {r[0]}")

conn.close()
