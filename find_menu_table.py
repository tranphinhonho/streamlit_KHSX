# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Liệt kê tất cả các bảng
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Các bảng trong database:")
for t in tables:
    print(f"  - {t[0]}")

# Tìm bảng chứa thông tin menu
for t in tables:
    table_name = t[0]
    try:
        cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 1")
        columns = [desc[0] for desc in cursor.description]
        if 'Chức năng con' in columns or 'chức năng con' in [c.lower() for c in columns]:
            print(f"\n✅ Bảng '{table_name}' có cột 'Chức năng con'")
            cursor.execute(f"SELECT DISTINCT [Chức năng con] FROM [{table_name}] WHERE [Đã xóa] = 0")
            for row in cursor.fetchall():
                print(f"    - {row[0]}")
    except Exception as e:
        pass

conn.close()
