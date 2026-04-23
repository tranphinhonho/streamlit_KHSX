# -*- coding: utf-8 -*-
"""Script để ẩn menu 'Chọn Stock → Plan'"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Đánh dấu menu item là đã xóa (ẩn)
cursor.execute("""
    UPDATE tbsys_DanhSachChucNang 
    SET [Đã xóa] = 1 
    WHERE [Chức năng con] = 'Chọn Stock → Plan'
""")

print(f"Đã cập nhật {cursor.rowcount} menu item")
conn.commit()
conn.close()

print("✅ Menu 'Chọn Stock → Plan' đã được ẩn!")
print("💡 Reload lại trang Streamlit (F5) để thấy thay đổi.")
