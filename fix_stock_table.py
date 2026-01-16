"""
Script thêm các cột còn thiếu vào bảng StockHomNay
"""

import sqlite3

DB_PATH = "database_new.db"

def add_missing_columns():
    """Thêm các cột còn thiếu"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Danh sách các cột cần thêm
        columns_to_add = [
            ("[ID sản phẩm]", "INTEGER"),
            ("[Mã stock]", "TEXT"),
            ("[Số lượng]", "INTEGER DEFAULT 0"),
            ("[Ngày lấy]", "DATETIME"),
            ("[Ngày stock]", "DATE"),
            ("[Khách vãng lai]", "INTEGER DEFAULT 0"),
            ("[Ghi chú]", "TEXT"),
        ]
        
        # Kiểm tra cột hiện có
        cursor.execute("PRAGMA table_info(StockHomNay)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Các cột hiện có: {existing_columns}\n")
        
        # Thêm từng cột nếu chưa có
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE StockHomNay ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"✅ Đã thêm cột: {col_name} ({col_type})")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Cột {col_name} đã tồn tại")
                    else:
                        print(f"❌ Lỗi khi thêm {col_name}: {e}")
            else:
                print(f"✓ Cột {col_name} đã có sẵn")
        
        conn.commit()
        
        # Hiển thị cấu trúc cuối cùng
        cursor.execute("PRAGMA table_info(StockHomNay)")
        columns = cursor.fetchall()
        
        print("\n" + "="*60)
        print(f"📊 CẤU TRÚC BẢNG STOCKHOMNAY ({len(columns)} cột):")
        print("="*60)
        for col in columns:
            print(f"{col[0]+1:2}. {col[1]:<25} {col[2]:<15} {'NOT NULL' if col[3] else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🔧 THÊM CỘT VÀO BẢNG STOCKHOMNAY")
    print("="*60)
    print(f"📁 Database: {DB_PATH}\n")
    
    success = add_missing_columns()
    
    if success:
        print("\n" + "="*60)
        print("🎉 HOÀN THÀNH!")
        print("="*60)
        print("\n✅ Bảng StockHomNay đã sẵn sàng")
        print("🔄 Reload trang Streamlit để sử dụng")
