"""
Script tạo bảng cho Packing, Sale, StockOld
Chạy script này để tạo tất cả bảng cần thiết
"""

import sqlite3

DB_PATH = "database_new.db"

def create_tables():
    """Tạo 3 bảng: Packing, Sale, StockOld"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables_config = [
        {
            'name': 'Packing',
            'prefix': 'PK',
            'code_field': 'Mã packing',
            'date_field': 'Ngày packing'
        },
        {
            'name': 'Sale',
            'prefix': 'SL',
            'code_field': 'Mã sale',
            'date_field': 'Ngày sale'
        },
        {
            'name': 'StockOld',
            'prefix': 'SO',
            'code_field': 'Mã stock old',
            'date_field': 'Ngày stock old'
        }
    ]
    
    try:
        for config in tables_config:
            table_name = config['name']
            code_field = config['code_field']
            date_field = config['date_field']
            
            print(f"\n📦 Tạo bảng {table_name}...")
            
            # Tạo bảng
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                [ID sản phẩm] INTEGER,
                [{code_field}] TEXT,
                [Số lượng] INTEGER DEFAULT 0,
                [Ngày lấy] DATETIME,
                [{date_field}] DATE,
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
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name.lower()}_code ON {table_name}([{code_field}])")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name.lower()}_date ON {table_name}([{date_field}])")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name.lower()}_product ON {table_name}([ID sản phẩm])")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name.lower()}_deleted ON {table_name}([Đã xóa])")
            
            # Kiểm tra cấu trúc
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"✅ Bảng {table_name}: {len(columns)} cột")
            
        conn.commit()
        
        print("\n" + "="*60)
        print("📊 TÓM TẮT")
        print("="*60)
        
        for config in tables_config:
            cursor.execute(f"PRAGMA table_info({config['name']})")
            cols = cursor.fetchall()
            print(f"✓ {config['name']:<15} {len(cols)} cột - Prefix: {config['prefix']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 TẠO BẢNG PACKING, SALE, STOCKOLD")
    print("="*60)
    print(f"📁 Database: {DB_PATH}\n")
    
    success = create_tables()
    
    if success:
        print("\n" + "="*60)
        print("🎉 HOÀN THÀNH!")
        print("="*60)
        print("\n✅ Đã tạo 3 bảng thành công")
        print("📋 Bước tiếp theo:")
        print("   1. Vào Admin KDE > Danh sách chức năng")
        print("   2. Thêm 3 chức năng: Packing, Sale, Stock Old")
        print("   3. Vào Liên kết Module:")
        print("      - Packing → PagesKDE.Packing")
        print("      - Sale → PagesKDE.Sale")
        print("      - Stock Old → PagesKDE.StockOld")
        print("   4. Phân quyền trong Chức năng theo vai trò")
        print("   5. Reload trang Streamlit")
    else:
        print("\n❌ Có lỗi xảy ra!")
