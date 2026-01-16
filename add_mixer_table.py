"""
Script tạo bảng Mixer trong database
Mixer: máy trộn cám với batch size 8000 hoặc 8400 kg
"""
import sqlite3
from datetime import datetime

# Đường dẫn database
database_path = "database_new.db"

# Kết nối database
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

print("=" * 60)
print("TẠO BẢNG MIXER")
print("=" * 60)

# Kiểm tra bảng đã tồn tại chưa
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='Mixer'
""")
existing = cursor.fetchone()

if existing:
    print("! Bảng Mixer đã tồn tại")
else:
    cursor.execute("""
    CREATE TABLE Mixer (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        [Mã mixer] TEXT,
        [Ngày trộn] DATE NOT NULL,
        [ID sản phẩm] INTEGER,
        [Batch size] REAL DEFAULT 8400,
        [Số lượng thực tế] REAL DEFAULT 0,
        [Loss (kg)] REAL DEFAULT 0,
        [Loss (%)] REAL DEFAULT 0,
        [Đích đến] TEXT DEFAULT 'Pellet',
        [Số máy] TEXT,
        [Ca sản xuất] TEXT DEFAULT 'Ca 1',
        [Ghi chú] TEXT,
        [Người tạo] TEXT,
        [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
        [Người sửa] TEXT,
        [Thời gian sửa] DATETIME,
        [Đã xóa] INTEGER DEFAULT 0
    )
    """)
    print("✓ Đã tạo bảng Mixer")

# Tạo index cho truy vấn nhanh hơn
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mixer_ngay ON Mixer([Ngày trộn])")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mixer_sanpham ON Mixer([ID sản phẩm])")
    print("✓ Đã tạo index")
except Exception as e:
    print(f"! Index: {e}")

# Commit
conn.commit()

print("\n" + "=" * 60)
print("HOÀN TẤT!")
print("=" * 60)

# Hiển thị cấu trúc bảng
cursor.execute("PRAGMA table_info(Mixer)")
columns = cursor.fetchall()
print("\nCấu trúc bảng Mixer:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Đóng kết nối
conn.close()
