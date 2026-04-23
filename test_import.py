"""Test import ffstock"""
from utils.stock_importer import StockImporter
import traceback

s = StockImporter()
try:
    result = s.import_ffstock(
        file_path='downloads/FFSTOCK 14-01-2026.xlsm',
        nguoi_import='phinho',
        ngay_stock='2026-01-14',
        overwrite=True
    )
    print(f"Success: {result['success']}")
    print(f"Not found: {len(result.get('not_found', []))}")
    print(f"Auto added: {len(result.get('auto_added', []))}")
    print(f"Errors: {result.get('errors', [])[:5]}")
except Exception as e:
    traceback.print_exc()
