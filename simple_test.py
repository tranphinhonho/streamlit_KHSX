import sqlite3
import pandas as pd

def simple_test_product_lookup():
    """Test đơn giản việc lookup sản phẩm từ tên"""
    
    print("=== TEST LOOKUP TỪ TÊN SẢN PHẨM ===")
    
    # Test data
    test_products = ['524P', '502', '510', '511', 'NOTFOUND', '550S']
    
    conn = sqlite3.connect('database_new.db')
    
    for product_name in test_products:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, [Code cám], [Tên cám], [Kích cỡ ép viên] 
            FROM SanPham 
            WHERE [Tên cám] = ? AND [Đã xóa] = 0
        """, (product_name,))
        result = cursor.fetchone()
        
        if result:
            id_sp, code_cam, ten_cam, kich_co = result
            print(f"✅ '{product_name}' → ID: {id_sp} | Code: {code_cam} | Kích cỡ: {kich_co}")
        else:
            print(f"❌ '{product_name}' → Không tìm thấy")
    
    conn.close()
    
    print("\n=== DEMO PROCESS IMPORT ===")
    
    # Mô phỏng quá trình import
    test_data = [
        {'Tên sản phẩm': '524P', 'Số lượng': 1000, 'Ghi chú': 'Test 1'},
        {'Tên sản phẩm': '502', 'Số lượng': 2000, 'Ghi chú': 'Test 2'},
        {'Tên sản phẩm': 'NOTFOUND', 'Số lượng': 3000, 'Ghi chú': 'Test 3'},
    ]
    
    conn = sqlite3.connect('database_new.db')
    result_data = []
    not_found = []
    
    for item in test_data:
        ten_sanpham = item['Tên sản phẩm']
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, [Code cám], [Tên cám], [Kích cỡ ép viên] 
            FROM SanPham 
            WHERE [Tên cám] = ? AND [Đã xóa] = 0
        """, (ten_sanpham,))
        result = cursor.fetchone()
        
        if result:
            id_sanpham, code_cam, ten_cam, kich_co = result
            import_item = {
                'ID sản phẩm': id_sanpham,
                'Tên sản phẩm': ten_cam,
                'Code cám tự động': code_cam,
                'Số lượng': item['Số lượng'],
                'Ghi chú': item['Ghi chú']
            }
            result_data.append(import_item)
            print(f"📦 Import thành công: {ten_sanpham} → {code_cam} (ID: {id_sanpham})")
        else:
            not_found.append(ten_sanpham)
            print(f"⚠️ Không tìm thấy: {ten_sanpham}")
    
    conn.close()
    
    if result_data:
        print(f"\n✅ Kết quả: Import thành công {len(result_data)} sản phẩm")
        print(f"❌ Không tìm thấy: {len(not_found)} sản phẩm: {not_found}")
        
        df_result = pd.DataFrame(result_data)
        print("\nDữ liệu đã xử lý:")
        print(df_result.to_string(index=False))

if __name__ == "__main__":
    simple_test_product_lookup()