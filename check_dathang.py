import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Kiểm tra bảng DatHang
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='DatHang'")
result = cursor.fetchone()

if result:
    print(f"✓ Bảng DatHang tồn tại")
    
    # Kiểm tra cột
    cursor.execute("PRAGMA table_info(DatHang)")
    columns = cursor.fetchall()
    print(f"\nCác cột trong bảng DatHang:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Kiểm tra dữ liệu
    cursor.execute("SELECT COUNT(*) FROM DatHang")
    count = cursor.fetchone()[0]
    print(f"\nSố bản ghi: {count}")
    
    if count > 0:
        cursor.execute("SELECT [Mã đặt hàng] FROM DatHang LIMIT 5")
        samples = cursor.fetchall()
        print("\nMẫu Mã đặt hàng:")
        for s in samples:
            print(f"  - {s[0]}")
else:
    print("✗ Bảng DatHang KHÔNG TỒN TẠI")
    print("\nCần tạo bảng DatHang trước!")

conn.close()
