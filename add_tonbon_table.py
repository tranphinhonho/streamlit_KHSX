# -*- coding: utf-8 -*-
"""
Script tao bang TonBon (Ton Bon) trong database
Ton Bon: theo doi thanh pham va ban thanh pham trong bon
"""
import sqlite3
from datetime import datetime

database_path = "database_new.db"
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

print("=" * 60)
print("TAO BANG TONBON (TON BON)")
print("=" * 60)

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TonBon'")
existing = cursor.fetchone()

if existing:
    print("! Bang TonBon da ton tai")
else:
    cursor.execute("""
    CREATE TABLE TonBon (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        [Mã tồn bồn] TEXT,
        [Ngày kiểm kho] DATE NOT NULL,
        [ID sản phẩm] INTEGER,
        [Loại sản phẩm] TEXT DEFAULT 'Thành phẩm',
        [Số lượng (kg)] REAL DEFAULT 0,
        [Số bồn] TEXT,
        [Trạng thái] TEXT DEFAULT 'Chờ đóng bao',
        [Kích cỡ đóng bao] TEXT DEFAULT '25 kg',
        [Ca sản xuất] TEXT DEFAULT 'Ca 1',
        [Ghi chú] TEXT,
        [Người tạo] TEXT,
        [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
        [Người sửa] TEXT,
        [Thời gian sửa] DATETIME,
        [Đã xóa] INTEGER DEFAULT 0
    )
    """)
    print("OK: Da tao bang TonBon")

# Create indexes
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tonbon_ngay ON TonBon([Ngày kiểm kho])")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tonbon_sanpham ON TonBon([ID sản phẩm])")
    print("OK: Da tao index")
except Exception as e:
    print(f"! Index: {e}")

conn.commit()

print("\n" + "=" * 60)
print("HOAN TAT!")
print("=" * 60)

# Show structure
cursor.execute("PRAGMA table_info(TonBon)")
columns = cursor.fetchall()
print("\nCau truc bang TonBon:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
