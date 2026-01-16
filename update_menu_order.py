"""
Script cập nhật thứ tự hiển thị các chức năng
Thứ tự: Đặt hàng -> StockHomNay -> Plan -> Sale -> Packing -> StockOld -> Tiên đoán AI
"""

import sqlite3

DB_PATH = "database_new.db"

def update_menu_order():
    """Cập nhật thứ tự ưu tiên cho các chức năng"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Mapping tên chức năng -> thứ tự ưu tiên
    priority_map = {
        'Đặt hàng': 10,
        'Stock hôm nay': 20,
        'Plan': 30,
        'Sale': 40,
        'Packing': 50,
        'Stock Old': 60,
        'Tiên đoán AI': 70,
    }
    
    try:
        print("📋 Cập nhật thứ tự hiển thị menu...\n")
        
        updated_count = 0
        not_found = []
        
        for func_name, priority in priority_map.items():
            # Tìm và update
            cursor.execute("""
                UPDATE tbsys_DanhSachChucNang
                SET [Thứ tự ưu tiên] = ?
                WHERE TRIM([Chức năng con]) = ? AND [Đã xóa] = 0
            """, (priority, func_name))
            
            if cursor.rowcount > 0:
                print(f"✅ {func_name:<20} → Thứ tự: {priority}")
                updated_count += cursor.rowcount
            else:
                not_found.append(func_name)
                print(f"⚠️  {func_name:<20} → Không tìm thấy")
        
        conn.commit()
        
        # Kiểm tra kết quả
        print("\n" + "="*60)
        print("📊 KẾT QUẢ SAU KHI CẬP NHẬT")
        print("="*60)
        
        cursor.execute("""
            SELECT [Chức năng con], [Thứ tự ưu tiên]
            FROM tbsys_DanhSachChucNang
            WHERE [Chức năng con] IN (?, ?, ?, ?, ?, ?, ?)
            AND [Đã xóa] = 0
            ORDER BY [Thứ tự ưu tiên]
        """, tuple(priority_map.keys()))
        
        results = cursor.fetchall()
        
        if results:
            for idx, (name, priority) in enumerate(results, 1):
                print(f"{idx}. {name:<20} (Thứ tự: {priority})")
        
        print("\n" + "="*60)
        print(f"✅ Đã cập nhật: {updated_count} chức năng")
        if not_found:
            print(f"⚠️  Không tìm thấy: {', '.join(not_found)}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🔄 CẬP NHẬT THỨ TỰ MENU")
    print("="*60)
    print(f"📁 Database: {DB_PATH}\n")
    
    success = update_menu_order()
    
    if success:
        print("\n" + "="*60)
        print("🎉 HOÀN THÀNH!")
        print("="*60)
        print("\n📋 Bước tiếp theo:")
        print("   1. Đăng xuất khỏi ứng dụng")
        print("   2. Đăng nhập lại")
        print("   3. Menu sẽ hiển thị theo thứ tự mới:")
        print("      • Đặt hàng")
        print("      • Stock hôm nay")
        print("      • Plan")
        print("      • Sale")
        print("      • Packing")
        print("      • Stock Old")
        print("      • Tiên đoán AI")
