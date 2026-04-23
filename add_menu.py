# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Use "Kế hoạch sản xuất" (ID: 2) as parent
parent_id = 2

print(f"Using parent ID: {parent_id} (Kế hoạch sản xuất)")

# Add new menu item
cursor.execute("""
    INSERT INTO tbsys_DanhSachChucNang 
    ([ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên], [Đã xóa], [Người tạo], [Thời gian tạo])
    VALUES (?, 'Chọn Stock → Plan', 1, 0, 'phinho', datetime('now'))
""", (parent_id,))

new_func_id = cursor.lastrowid
print(f"Created menu item with ID: {new_func_id}")

# Link to module
cursor.execute("""
    INSERT INTO tbsys_ModuleChucNang 
    ([ID_DanhSachChucNang], [ModulePath], [Đã xóa], [Người tạo], [Thời gian tạo])
    VALUES (?, 'PagesKDE.ChonStockPlan', 0, 'phinho', datetime('now'))
""", (new_func_id,))

conn.commit()
print("SUCCESS! Menu item 'Chọn Stock → Plan' added to 'Kế hoạch sản xuất'!")

conn.close()
