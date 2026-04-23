# -*- coding: utf-8 -*-
"""
Thêm cột T/h và Kwh/T vào bảng SanPham
"""
import sqlite3

def add_columns():
    conn = sqlite3.connect('database_new.db')
    cursor = conn.cursor()
    
    # Kiểm tra và thêm cột T/h
    cursor.execute("PRAGMA table_info(SanPham)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'T/h' not in columns:
        cursor.execute("ALTER TABLE SanPham ADD COLUMN [T/h] REAL")
        print("Added column T/h to SanPham")
    else:
        print("Column T/h already exists")
    
    if 'Kwh/T' not in columns:
        cursor.execute("ALTER TABLE SanPham ADD COLUMN [Kwh/T] REAL")
        print("Added column Kwh/T to SanPham")
    else:
        print("Column Kwh/T already exists")
    
    conn.commit()
    conn.close()
    print("Done!")

if __name__ == '__main__':
    add_columns()
