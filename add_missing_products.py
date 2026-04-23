# -*- coding: utf-8 -*-
"""Script them 8 san pham missing vao SanPham"""
import sqlite3
from datetime import datetime

# 8 san pham can them
products = [
    ('6951XS87', 'H'),
    ('GT12AN', 'G'),
    ('566XS74', 'H'),
    ('567SXS74', 'H'),
    ('571', 'B'),
    ('521PRO', 'G'),
    ('GT11NS', 'G'),
    ('544P', 'V'),
]

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
inserted = 0

for code_cam, vat_nuoi in products:
    cursor.execute("""
        INSERT INTO SanPham ([Code cám], [Tên cám], [Vật nuôi], [Người tạo], [Thời gian tạo], [Đã xóa])
        VALUES (?, ?, ?, ?, ?, 0)
    """, (code_cam, code_cam, vat_nuoi, 'system', now))
    inserted += 1

conn.commit()
conn.close()

print(f"Inserted: {inserted} products")
