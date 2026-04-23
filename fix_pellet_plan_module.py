"""
Script để fix module path cho Pellet Plan
"""

import sqlite3

DB_PATH = 'database_new.db'

def fix_pellet_plan_module():
    """Kiểm tra và sửa module path cho Pellet Plan"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("KIỂM TRA VÀ SỬA MODULE PATH CHO PELLET PLAN")
        print("=" * 60)
        
        # Bước 1: Tìm ID của chức năng Pellet Plan
        print("\n📋 Tìm chức năng 'Pellet Plan'...")
        cursor.execute("""
            SELECT ID, [Chức năng con] 
            FROM tbsys_DanhSachChucNang 
            WHERE [Chức năng con] = 'Pellet Plan' AND [Đã xóa] = 0
        """)
        result = cursor.fetchone()
        
        if not result:
            print("❌ Không tìm thấy 'Pellet Plan' trong database!")
            return
        
        id_chucnang = result[0]
        print(f"✓ Tìm thấy: ID = {id_chucnang}, Tên = {result[1]}")
        
        # Bước 2: Kiểm tra module path hiện tại
        print(f"\n📋 Kiểm tra ModulePath cho ID = {id_chucnang}...")
        cursor.execute("""
            SELECT ID, ID_DanhSachChucNang, ModulePath, [Đã xóa]
            FROM tbsys_ModuleChucNang 
            WHERE ID_DanhSachChucNang = ?
        """, (id_chucnang,))
        module_rows = cursor.fetchall()
        
        if module_rows:
            print("ℹ️ Module hiện tại:")
            for row in module_rows:
                print(f"   - ID: {row[0]}, ModulePath: {row[2]}, Đã xóa: {row[3]}")
        else:
            print("⚠️ Chưa có ModulePath nào được liên kết!")
        
        # Bước 3: Tạo hoặc cập nhật module path đúng
        correct_path = "PagesKDE.Pellet"
        print(f"\n🔄 Đảm bảo ModulePath = '{correct_path}'...")
        
        # Xóa các module path cũ (set Đã xóa = 1)
        cursor.execute("""
            UPDATE tbsys_ModuleChucNang 
            SET [Đã xóa] = 1 
            WHERE ID_DanhSachChucNang = ?
        """, (id_chucnang,))
        
        # Tạo module path mới
        cursor.execute("""
            INSERT INTO tbsys_ModuleChucNang (ID_DanhSachChucNang, ModulePath, [Đã xóa])
            VALUES (?, ?, 0)
        """, (id_chucnang, correct_path))
        
        conn.commit()
        print(f"✅ Đã tạo ModulePath mới: {correct_path}")
        
        # Bước 4: Xác nhận
        print("\n📋 Xác nhận cấu hình...")
        cursor.execute("""
            SELECT T1.[Chức năng con], T2.ModulePath
            FROM tbsys_DanhSachChucNang AS T1
            LEFT JOIN tbsys_ModuleChucNang AS T2 
                ON T1.ID = T2.ID_DanhSachChucNang AND T2.[Đã xóa] = 0
            WHERE T1.[Chức năng con] = 'Pellet Plan' AND T1.[Đã xóa] = 0
        """)
        final = cursor.fetchall()
        for row in final:
            print(f"   ✓ {row[0]} -> {row[1]}")
        
        print("\n" + "=" * 60)
        print("HOÀN TẤT! Vui lòng khởi động lại ứng dụng Streamlit.")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_pellet_plan_module()
