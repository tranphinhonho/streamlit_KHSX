"""
Tạo script để test toàn bộ workflow của TestCan
"""
import sys
import os

# Thêm đường dẫn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing TestCan workflow...")
print("="*60)

# Test 1: Import modules
print("\n1. Testing imports...")
try:
    from utils.database_utils import (
        init_testcan_tables,
        save_testcan_report,
        get_testcan_reports
    )
    from utils.email_utils import send_outlook_email
    from PIL import Image
    from io import BytesIO
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Init database
print("\n2. Testing database init...")
try:
    init_testcan_tables("database_new.db")
    print("   ✅ Database initialized")
except Exception as e:
    print(f"   ❌ Database init failed: {e}")
    sys.exit(1)

# Test 3: Create test image
print("\n3. Creating test image...")
try:
    image = Image.new('RGB', (300, 200), color='green')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    print(f"   ✅ Image created ({len(image_bytes)} bytes)")
except Exception as e:
    print(f"   ❌ Image creation failed: {e}")
    sys.exit(1)

# Test 4: Save without email
print("\n4. Testing save to database (no email)...")
try:
    saved_id = save_testcan_report(
        datetime_value="2025-12-03 16:00:00",
        value_502="88.0",
        value_505="14.0",
        value_508="995.0",
        value_574="28.0",
        image_bytes=image_bytes,
        image_filename="test_workflow.png",
        created_by="phinho",
        notes="Test from workflow script",
        email_sent=False,
        email_recipients="",
        is_valid=True,
        db_path="database_new.db"
    )
    print(f"   ✅ Saved successfully with ID: {saved_id}")
except Exception as e:
    print(f"   ❌ Save failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Retrieve records
print("\n5. Testing retrieve records...")
try:
    reports = get_testcan_reports(limit=5, db_path="database_new.db")
    print(f"   ✅ Retrieved {len(reports)} records")
    for r in reports:
        print(f"      - ID={r['ID']}, Time={r['Datetime']}, User={r['Created_By']}")
except Exception as e:
    print(f"   ❌ Retrieve failed: {e}")
    sys.exit(1)

# Test 6: Test email (optional - will likely fail if Outlook not configured)
print("\n6. Testing email send (optional)...")
print("   ⏭️  Skipping email test - manual test required in Streamlit")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("\nNext steps:")
print("1. Streamlit app is running at http://localhost:8501")
print("2. Go to 'Test cân' module")
print("3. Upload an image and click Submit")
print("4. Click '💾 Lưu nhanh' to save without email")
print("5. Or fill email form and click '📧 Gửi email và lưu'")
print("6. Check 'Lịch sử' tab to see saved records")
