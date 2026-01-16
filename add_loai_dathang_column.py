import sqlite3

# Kết nối đến database
conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

try:
    # Kiểm tra xem cột đã tồn tại chưa
    cursor.execute("PRAGMA table_info(DatHang)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'Loại đặt hàng' not in columns:
        print("Đang thêm cột 'Loại đặt hàng' vào bảng DatHang...")
        cursor.execute("""
            ALTER TABLE DatHang 
            ADD COLUMN [Loại đặt hàng] TEXT
        """)
        conn.commit()
        print("✅ Đã thêm cột 'Loại đặt hàng' thành công!")
        
        # Cập nhật giá trị mặc định cho dữ liệu cũ
        cursor.execute("""
            UPDATE DatHang 
            SET [Loại đặt hàng] = CASE 
                WHEN [Khách vãng lai] = 1 THEN 'Khách vãng lai'
                ELSE 'Đơn hàng thường'
            END
            WHERE [Loại đặt hàng] IS NULL
        """)
        conn.commit()
        print("✅ Đã cập nhật giá trị mặc định cho dữ liệu cũ!")
        
    else:
        print("ℹ️ Cột 'Loại đặt hàng' đã tồn tại trong bảng DatHang")
    
    # Hiển thị cấu trúc bảng sau khi thêm
    cursor.execute("PRAGMA table_info(DatHang)")
    print("\n📋 Cấu trúc bảng DatHang:")
    for row in cursor.fetchall():
        print(f"  - {row[1]} ({row[2]})")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\n✅ Hoàn tất!")
