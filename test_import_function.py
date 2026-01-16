import pandas as pd
from PagesKDE.DatHang import process_import_dathang

def test_import_function():
    """Test function import mới với tên sản phẩm"""
    
    # Tạo test data
    test_data = {
        'Tên sản phẩm': ['524P', '502', '510', '511', 'NOTFOUND'],
        'Số lượng': [1000, 2000, 3000, 4000, 5000],
        'Ngày lấy (tùy chọn)': ['2025-12-07', '2025-12-08', '', '', ''],
        'Ghi chú (tùy chọn)': ['Test 1', 'Test 2', '', 'Test 4', '']
    }
    
    df = pd.DataFrame(test_data)
    print("=== TEST DATA ===")
    print(df)
    print()
    
    print("=== TESTING IMPORT FUNCTION ===")
    result = process_import_dathang(df, loai_dathang='Khách vãng lai', khach_vang_lai=1)
    
    if result is not None:
        print("\n=== KẾT QUẢ ===")
        print(result)
    else:
        print("Import thất bại!")

if __name__ == "__main__":
    test_import_function()