"""
Script để đổi tên tab "Pellet" thành "Pellet Plan" trong database
"""

import sqlite3

DB_PATH = 'database_new.db'

def rename_pellet_to_pellet_plan():
    """Đổi tên chức năng Pellet thành Pellet Plan"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("ĐỔI TÊN TAB PELLET -> PELLET PLAN")
        print("=" * 60)
        
        # Kiểm tra giá trị hiện tại
        print("\n📋 Kiểm tra tên hiện tại...")
        cursor.execute("""
            SELECT ID, [Chức năng con] 
            FROM tbsys_DanhSachChucNang 
            WHERE [Chức năng con] = 'Pellet' AND [Đã xóa] = 0
        """)
        result = cursor.fetchall()
        
        if result:
            print(f"✓ Tìm thấy {len(result)} bản ghi với tên 'Pellet'")
            for row in result:
                print(f"   - ID: {row[0]}, Tên: {row[1]}")
            
            # Cập nhật tên
            print("\n🔄 Đang cập nhật tên...")
            cursor.execute("""
                UPDATE tbsys_DanhSachChucNang 
                SET [Chức năng con] = 'Pellet Plan' 
                WHERE [Chức năng con] = 'Pellet' AND [Đã xóa] = 0
            """)
            
            conn.commit()
            print(f"✅ Đã cập nhật {cursor.rowcount} bản ghi!")
            
            # Xác nhận thay đổi
            print("\n📋 Xác nhận thay đổi...")
            cursor.execute("""
                SELECT ID, [Chức năng con] 
                FROM tbsys_DanhSachChucNang 
                WHERE [Chức năng con] = 'Pellet Plan' AND [Đã xóa] = 0
            """)
            new_result = cursor.fetchall()
            for row in new_result:
                print(f"   - ID: {row[0]}, Tên: {row[1]}")
        else:
            print("⚠️ Không tìm thấy chức năng nào có tên 'Pellet'")
            
            # Kiểm tra xem đã đổi tên chưa
            cursor.execute("""
                SELECT ID, [Chức năng con] 
                FROM tbsys_DanhSachChucNang 
                WHERE [Chức năng con] = 'Pellet Plan' AND [Đã xóa] = 0
            """)
            existing = cursor.fetchall()
            if existing:
                print("ℹ️ Đã có chức năng 'Pellet Plan' trong database:")
                for row in existing:
                    print(f"   - ID: {row[0]}, Tên: {row[1]}")
        
        print("\n" + "=" * 60)
        print("HOÀN TẤT!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    rename_pellet_to_pellet_plan()
