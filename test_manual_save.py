"""
Test manual save to database
"""
import sys
sys.path.insert(0, '.')

from utils.database_utils import save_testcan_report, init_testcan_tables
from PIL import Image
from io import BytesIO

print("Step 1: Init database tables...")
init_testcan_tables("database_new.db")
print("OK")

print("\nStep 2: Create test image...")
image = Image.new('RGB', (200, 100), color='blue')
buffer = BytesIO()
image.save(buffer, format='PNG')
image_bytes = buffer.getvalue()
print(f"Image size: {len(image_bytes)} bytes")

print("\nStep 3: Save to database...")
try:
    saved_id = save_testcan_report(
        datetime_value="2025-12-03 15:30:00",
        value_502="90.0",
        value_505="15.5",
        value_508="1000.0",
        value_574="30.0",
        image_bytes=image_bytes,
        image_filename="test_manual.png",
        created_by="phinho",
        notes="Test manual save",
        email_sent=False,
        email_recipients="",
        is_valid=True,
        db_path="database_new.db"
    )
    print(f"SUCCESS! Saved with ID: {saved_id}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 4: Verify saved data...")
import sqlite3
conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM TestCan_Reports")
count = cursor.fetchone()[0]
print(f"Total records in database: {count}")

cursor.execute("SELECT ID, Datetime, Created_By, Image_Filename FROM TestCan_Reports ORDER BY ID DESC LIMIT 1")
last = cursor.fetchone()
if last:
    print(f"Last record: ID={last[0]}, Time={last[1]}, User={last[2]}, File={last[3]}")
conn.close()
