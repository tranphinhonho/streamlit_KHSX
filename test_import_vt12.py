import sys
sys.path.insert(0, 'D:/PYTHON/B7KHSX')

from utils.stock_importer import StockImporter
from pathlib import Path

importer = StockImporter()

# Test import
file = Path('downloads/FFSTOCK 14-01-2026.xlsm')
print(f"Testing import for {file}")

result = importer.import_ffstock(
    file_path=file,
    nguoi_import='test',
    ngay_stock='2026-01-14',
    overwrite=True,
    auto_add_missing=False
)

print(f"\nResult:")
print(f"  Success: {result['success']}")
print(f"  Not found: {len(result['not_found'])}")

# Show not_found products containing VT
not_found_vt = [nf for nf in result['not_found'] if 'VT' in str(nf).upper()]
print(f"\nVT products in not_found ({len(not_found_vt)}):")
for nf in not_found_vt:
    print(f"  - {nf}")
