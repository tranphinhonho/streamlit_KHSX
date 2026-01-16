"""
Script tạo bảng Plan
"""

import sqlite3

DB_PATH = "database_new.db"

def create_plan_table():
    """Tạo bảng Plan"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📦 Tạo bảng Plan...")
        
        # Tạo bảng
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Plan (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            [ID sản phẩm] INTEGER,
            [Mã plan] TEXT,
            [Số lượng] INTEGER DEFAULT 0,
            [Ngày lấy] DATETIME,
            [Ngày plan] DATE,
            [Khách vãng lai] INTEGER DEFAULT 0,
            [Ghi chú] TEXT,
            [Người tạo] TEXT,
            [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
            [Người sửa] TEXT,
            [Thời gian sửa] DATETIME,
            [Đã xóa] INTEGER DEFAULT 0,
            FOREIGN KEY ([ID sản phẩm]) REFERENCES SanPham(ID)
        )
        """)
        
        # Tạo index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plan_code ON Plan([Mã plan])")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plan_date ON Plan([Ngày plan])")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plan_product ON Plan([ID sản phẩm])")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plan_deleted ON Plan([Đã xóa])")
        
        conn.commit()
        
        # Kiểm tra cấu trúc
        cursor.execute("PRAGMA table_info(Plan)")
        columns = cursor.fetchall()
        
        print(f"✅ Bảng Plan: {len(columns)} cột")
        print("\n" + "="*60)
        print("📊 CẤU TRÚC BẢNG PLAN")
        print("="*60)
        for col in columns:
            print(f"{col[0]+1:2}. {col[1]:<25} {col[2]:<15}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 TẠO BẢNG PLAN")
    print("="*60)
    print(f"📁 Database: {DB_PATH}\n")
    
    success = create_plan_table()
    
    if success:
        print("\n" + "="*60)
        print("🎉 HOÀN THÀNH!")
        print("="*60)
        print("\n✅ Bảng Plan đã sẵn sàng")
        print("📋 Bước tiếp theo:")
        print("   1. Vào Admin KDE > Danh sách chức năng")
        print("   2. Thêm chức năng: Plan")
        print("   3. Vào Liên kết Module: Plan → PagesKDE.Plan")
        print("   4. Phân quyền trong Chức năng theo vai trò")
        print("   5. Reload trang Streamlit")
        print("\n📌 Mã prefix: PL (PL00001, PL00002...)")
