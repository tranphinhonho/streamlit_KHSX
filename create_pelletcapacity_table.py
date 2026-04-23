# -*- coding: utf-8 -*-
"""
Tạo bảng PelletCapacity để lưu dữ liệu T/h từ các file vận hành cám viên
"""
import sqlite3

def create_table():
    conn = sqlite3.connect('database_new.db')
    cursor = conn.cursor()
    
    # Tạo bảng PelletCapacity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PelletCapacity (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        [Ngày] DATE,
        [Số máy] TEXT,
        [Code cám] TEXT,
        [Tên cám] TEXT,
        [T/h] REAL,
        [Kwh/T] REAL,
        [ID sản phẩm] INTEGER,
        [Số lô] INTEGER DEFAULT 1,
        [Nguồn file] TEXT,
        [Thời gian import] DATETIME,
        [Người import] TEXT,
        [Đã xóa] INTEGER DEFAULT 0,
        FOREIGN KEY ([ID sản phẩm]) REFERENCES SanPham(ID)
    )
    """)
    print("Created table PelletCapacity")
    
    # Tạo indexes
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_pelletcapacity_ngay 
    ON PelletCapacity([Ngày])
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_pelletcapacity_somay 
    ON PelletCapacity([Số máy])
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_pelletcapacity_codecam 
    ON PelletCapacity([Code cám])
    """)
    
    print("Created indexes for PelletCapacity")
    
    conn.commit()
    conn.close()
    print("Done!")

if __name__ == '__main__':
    create_table()
