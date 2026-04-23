"""Test forecast importer với file W4 (.xlsx)"""
import sys
sys.path.insert(0, '.')

from utils.forecast_importer import ForecastImporter

importer = ForecastImporter()

# Test với file W4 (.xlsx)
file_path = "EXCEL/W4.(19-24-01-) SALEFORECAST 2026.xlsx"

print("="*70)
print("TEST FORECAST IMPORTER - FILE W4 (.xlsx)")
print("="*70)

# 1. Kiểm tra sheets
print("\n1. Lấy danh sách sheets:")
sheets = importer.get_available_sheets(file_path)
print(f"   Sheets: {sheets}")

if not sheets:
    print("❌ Không tìm thấy sheet nào bắt đầu bằng 'W'")
else:
    # 2. Preview dữ liệu
    print(f"\n2. Preview dữ liệu từ sheet: {sheets[-1]}")
    preview_df = importer.preview_data(file_path=file_path, sheet_name=sheets[-1], limit=20)
    
    if preview_df.empty:
        print("❌ Không có dữ liệu preview")
    else:
        print(f"✅ Tìm thấy {len(preview_df)} dòng dữ liệu:")
        print(preview_df.to_string())
    
    # 3. Đọc toàn bộ dữ liệu
    print(f"\n3. Đọc toàn bộ dữ liệu từ sheet: {sheets[-1]}")
    data = importer._read_sheet_data(file_path, sheets[-1])
    print(f"   Tổng số sản phẩm: {len(data)}")
    
    if data:
        print("\n   Top 10 sản phẩm:")
        for i, item in enumerate(data[:10]):
            print(f"   {i+1}. {item['ten_cam']} - {item['so_luong_tan']} tấn")

print("\n" + "="*70)
print("KẾT THÚC TEST")
print("="*70)
