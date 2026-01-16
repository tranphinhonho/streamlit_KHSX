"""
Script thêm Stock hôm nay và Stock Old vào database
Tự động thêm chức năng, liên kết module, và phân quyền
"""

import sqlite3

DB_PATH = "database_new.db"

def add_missing_functions():
    """Thêm Stock hôm nay và Stock Old vào database"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Lấy ID chức năng chính (cùng nhóm với Đặt hàng)
        cursor.execute("""
            SELECT DISTINCT T2.ID, T2.[Chức năng chính]
            FROM tbsys_DanhSachChucNang AS T1
            JOIN tbsys_ChucNangChinh AS T2 ON T1.[ID Chức năng chính] = T2.ID
            WHERE T1.[Chức năng con] = 'Đặt hàng' AND T1.[Đã xóa] = 0
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if not result:
            print("❌ Không tìm thấy chức năng 'Đặt hàng' để lấy ID chức năng chính")
            return False
        
        id_chucnang_chinh, ten_chucnang_chinh = result
        print(f"📂 Nhóm chức năng: {ten_chucnang_chinh} (ID: {id_chucnang_chinh})\n")
        
        # Danh sách chức năng cần thêm
        functions = [
            {
                'name': 'Stock hôm nay',
                'priority': 20,
                'module': 'PagesKDE.StockHomNay'
            },
            {
                'name': 'Stock Old',
                'priority': 60,
                'module': 'PagesKDE.StockOld'
            }
        ]
        
        for func in functions:
            print(f"📝 Thêm chức năng: {func['name']}...")
            
            # 1. Kiểm tra đã tồn tại chưa
            cursor.execute("""
                SELECT ID FROM tbsys_DanhSachChucNang
                WHERE TRIM([Chức năng con]) = ? AND [Đã xóa] = 0
            """, (func['name'],))
            
            existing = cursor.fetchone()
            
            if existing:
                func_id = existing[0]
                print(f"   ⚠️  Chức năng đã tồn tại (ID: {func_id})")
                
                # Update thứ tự ưu tiên
                cursor.execute("""
                    UPDATE tbsys_DanhSachChucNang
                    SET [Thứ tự ưu tiên] = ?
                    WHERE ID = ?
                """, (func['priority'], func_id))
                print(f"   ✅ Đã cập nhật thứ tự ưu tiên: {func['priority']}")
            else:
                # Insert mới
                cursor.execute("""
                    INSERT INTO tbsys_DanhSachChucNang 
                    ([ID Chức năng chính], [Chức năng con], [Thứ tự ưu tiên], [Đã xóa])
                    VALUES (?, ?, ?, 0)
                """, (id_chucnang_chinh, func['name'], func['priority']))
                
                func_id = cursor.lastrowid
                print(f"   ✅ Đã thêm chức năng (ID: {func_id})")
            
            # 2. Liên kết module
            cursor.execute("""
                SELECT ID FROM tbsys_ModuleChucNang
                WHERE [ID_DanhSachChucNang] = ? AND [Đã xóa] = 0
            """, (func_id,))
            
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE tbsys_ModuleChucNang
                    SET ModulePath = ?
                    WHERE [ID_DanhSachChucNang] = ?
                """, (func['module'], func_id))
                print(f"   ✅ Đã cập nhật module: {func['module']}")
            else:
                cursor.execute("""
                    INSERT INTO tbsys_ModuleChucNang
                    ([ID_DanhSachChucNang], ModulePath, [Đã xóa])
                    VALUES (?, ?, 0)
                """, (func_id, func['module']))
                print(f"   ✅ Đã liên kết module: {func['module']}")
            
            # 3. Phân quyền cho tất cả vai trò
            cursor.execute("SELECT ID FROM tbsys_VaiTro WHERE [Đã xóa] = 0")
            roles = cursor.fetchall()
            
            for role in roles:
                role_id = role[0]
                
                cursor.execute("""
                    SELECT ID FROM tbsys_ChucNangTheoVaiTro
                    WHERE [ID Vai trò] = ? AND [ID Danh sách chức năng] = ?
                """, (role_id, func_id))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO tbsys_ChucNangTheoVaiTro
                        ([ID Vai trò], [ID Danh sách chức năng], [Đã xóa])
                        VALUES (?, ?, 0)
                    """, (role_id, func_id))
            
            print(f"   ✅ Đã phân quyền cho {len(roles)} vai trò\n")
        
        conn.commit()
        
        # Kiểm tra kết quả
        print("="*60)
        print("📊 DANH SÁCH CHỨC NĂNG SAU KHI CẬP NHẬT")
        print("="*60)
        
        cursor.execute("""
            SELECT [Chức năng con], [Thứ tự ưu tiên]
            FROM tbsys_DanhSachChucNang
            WHERE [ID Chức năng chính] = ? AND [Đã xóa] = 0
            ORDER BY [Thứ tự ưu tiên]
        """, (id_chucnang_chinh,))
        
        results = cursor.fetchall()
        for idx, (name, priority) in enumerate(results, 1):
            print(f"{idx}. {name:<20} (Thứ tự: {priority})")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 THÊM STOCK HÔM NAY VÀ STOCK OLD")
    print("="*60)
    print(f"📁 Database: {DB_PATH}\n")
    
    success = add_missing_functions()
    
    if success:
        print("\n" + "="*60)
        print("🎉 HOÀN THÀNH!")
        print("="*60)
        print("\n✅ Đã thêm 2 chức năng thành công")
        print("📋 Bước tiếp theo:")
        print("   1. Đăng xuất khỏi ứng dụng")
        print("   2. Đăng nhập lại")
        print("   3. Các chức năng sẽ hiển thị theo thứ tự:")
        print("      1. Đặt hàng (10)")
        print("      2. Stock hôm nay (20)")
        print("      3. Plan (30)")
        print("      4. Sale (40)")
        print("      5. Packing (50)")
        print("      6. Stock Old (60)")
        print("      7. Tiên đoán AI (70)")
    else:
        print("\n❌ Có lỗi xảy ra!")
