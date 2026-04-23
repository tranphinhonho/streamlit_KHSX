import sys
sys.path.insert(0, '.')
from utils.bacang_importer import BaCangImporter

importer = BaCangImporter()

# Test preview
print("Testing with xlsx file:")
df1, df2 = importer.preview_data(file_path="EXCEL/KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG 2026.xlsx", sheet_name="TUẦN 4", limit=5)

print("Table 1 (Xe tải bao 25kg):")
print(df1)
print(f"\nTable 1 rows: {len(df1)}")

print("\nTable 2 (Xe bồn Silo):")
print(df2)
print(f"\nTable 2 rows: {len(df2)}")
