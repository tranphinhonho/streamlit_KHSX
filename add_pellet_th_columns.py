# -*- coding: utf-8 -*-
"""
Script để thêm cột T/h và Kwh/T vào bảng Pellet (nếu chưa có)
"""
import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Lấy danh sách cột hiện có
cursor.execute("PRAGMA table_info(Pellet)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Current columns in Pellet: {len(columns)}")

# Thêm cột T/h nếu chưa có
if 'T/h' not in columns:
    cursor.execute("ALTER TABLE Pellet ADD COLUMN [T/h] REAL")
    print("Added column T/h to Pellet")
else:
    print("Column T/h already exists")

# Thêm cột Kwh/T nếu chưa có
if 'Kwh/T' not in columns:
    cursor.execute("ALTER TABLE Pellet ADD COLUMN [Kwh/T] REAL")
    print("Added column Kwh/T to Pellet")
else:
    print("Column Kwh/T already exists")

conn.commit()
conn.close()
print("Done!")
