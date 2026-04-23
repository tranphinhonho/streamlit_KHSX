"""Test file để kiểm tra import từ file .xlsx W4"""

from utils.forecast_importer import ForecastImporter

def test_xlsx_import():
    importer = ForecastImporter()
    file_path = "EXCEL/W4.(19-24-01-) SALEFORECAST 2026.xlsx"
    
    print("=== Test file .xlsx W4 ===")
    
    # Kiểm tra file type
    print(f"\n1. Is XLSX file: {importer._is_xlsx_file(file_path)}")
    
    # Lấy sheets
    sheets = importer.get_available_sheets(file_path)
    print(f"\n2. Available sheets: {sheets}")
    
    # Preview data
    print("\n3. Preview data (10 dòng đầu):")
    preview = importer.preview_data(file_path, limit=10)
    if not preview.empty:
        print(preview.to_string())
    else:
        print("   Không có dữ liệu!")
    
    # Test Grand Total
    print("\n4. Grand Total:")
    grand_total = importer.get_grand_total_from_excel(file_path)
    print(f"   Grand Total: {grand_total}")
    
    print("\n=== Test hoàn tất ===")

if __name__ == "__main__":
    test_xlsx_import()
