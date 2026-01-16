import sqlite3
import pandas as pd

def test_product_lookup():
    """Test function để kiểm tra việc tìm sản phẩm từ tên"""
    
    # Kết nối database
    conn = sqlite3.connect('database_new.db')
    
    # Lấy danh sách tên sản phẩm có sẵn
    cursor = conn.cursor()
    cursor.execute("""
        SELECT [Tên cám], [Code cám], ID, [Kích cỡ ép viên]
        FROM SanPham 
        WHERE [Đã xóa] = 0
        ORDER BY [Tên cám]
    """)
    
    products = cursor.fetchall()
    
    print("=== DANH SÁCH SẢN PHẨM CÓ SẴN ===")
    print(f"Tìm thấy {len(products)} sản phẩm:")
    print("Tên cám | Code cám | ID | Kích cỡ ép viên")
    print("-" * 80)
    
    for product in products:
        ten_cam, code_cam, id_sp, kich_co = product
        print(f"{ten_cam:<15} | {code_cam:<30} | {id_sp:<5} | {kich_co}")
    
    print("\n=== TEST LOOKUP ===")
    # Test với một vài tên sản phẩm
    test_names = ['55', '505', '524P', 'BR001', 'TC202']
    
    for test_name in test_names:
        cursor.execute("""
            SELECT ID, [Code cám], [Tên cám], [Kích cỡ ép viên] 
            FROM SanPham 
            WHERE [Tên cám] = ? AND [Đã xóa] = 0
        """, (test_name,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ '{test_name}' → Tìm thấy: ID={result[0]}, Code='{result[1]}'")
        else:
            print(f"❌ '{test_name}' → Không tìm thấy")
    
    conn.close()

if __name__ == "__main__":
    test_product_lookup()