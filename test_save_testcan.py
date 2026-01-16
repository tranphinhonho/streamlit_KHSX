"""
Test script để kiểm tra lưu dữ liệu TestCan vào database
"""
import sys
sys.path.insert(0, '.')

from utils.database_utils import save_testcan_report, get_testcan_reports, init_testcan_tables
from PIL import Image
from io import BytesIO

# Khởi tạo database
print("Initializing database...")
init_testcan_tables("database_new.db")

# Tạo một ảnh test đơn giản
print("Creating test image...")
image = Image.new('RGB', (100, 100), color='red')
buffer = BytesIO()
image.save(buffer, format='PNG')
image_bytes = buffer.getvalue()

# Lưu test report
print("Saving test report...")
try:
    saved_id = save_testcan_report(
        datetime_value="2025-12-03 14:30:00",
        value_502="85.5",
        value_505="12.3",
        value_508="1000.0",
        value_574="25.0",
        image_bytes=image_bytes,
        image_filename="test_image.png",
        created_by="phinho",
        notes="Test report from script",
        email_sent=False,
        email_recipients="",
        is_valid=True,
        db_path="database_new.db"
    )
    print(f"✅ Saved successfully with ID: {saved_id}")
except Exception as e:
    print(f"❌ Error saving: {e}")
    import traceback
    traceback.print_exc()

# Kiểm tra lại database
print("\nChecking saved records...")
reports = get_testcan_reports(limit=5, db_path="database_new.db")
print(f"Total reports found: {len(reports)}")
for report in reports:
    print(f"  ID={report['ID']}, Time={report['Datetime']}, User={report['Created_By']}")
