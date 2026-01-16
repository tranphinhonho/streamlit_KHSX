"""
Script demo: Thêm dữ liệu mẫu vào database Test Cân
Để test tính năng History
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.database_utils import save_testcan_report, get_testcan_stats

def create_sample_image(text: str) -> bytes:
    """Tạo ảnh mẫu với text"""
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Vẽ text
    draw.text((50, 50), f"Test Cân Sample", fill='black')
    draw.text((50, 100), f"Thời gian: {text}", fill='blue')
    draw.text((50, 150), "502: 25.5", fill='green')
    draw.text((50, 180), "505: 45.2", fill='green')
    draw.text((50, 210), "508: 1000.8", fill='green')
    draw.text((50, 240), "574: 30.1", fill='green')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def add_sample_data():
    """Thêm 10 báo cáo mẫu"""
    print("🚀 Bắt đầu thêm dữ liệu mẫu...")
    print("=" * 60)
    
    base_time = datetime.now()
    
    samples = [
        {
            'datetime': (base_time - timedelta(hours=i)).strftime('%Y-%m-%d %H:%M:%S'),
            'value_502': f"{20 + i * 2}.{i}",
            'value_505': f"{40 + i}.{i * 2}",
            'value_508': f"{1000 + i * 5}.{i}",
            'value_574': f"{25 + i}.{i}",
            'created_by': ['phinho', 'system', 'admin'][i % 3],
            'notes': [
                'Báo cáo bình thường',
                'Cần kiểm tra lại',
                'Đã xác nhận',
                '',
                'Test mẫu',
                'Giá trị ổn định',
                '',
                'Cần theo dõi',
                'OK',
                'Hoàn tất'
            ][i],
            'email_sent': i % 2 == 0,
            'email_recipients': 'tranphinho@gmail.com' if i % 2 == 0 else '',
            'is_valid': i != 3  # Record 3 không hợp lệ
        }
        for i in range(10)
    ]
    
    saved_ids = []
    for idx, sample in enumerate(samples, 1):
        print(f"\n[{idx}/10] Tạo báo cáo: {sample['datetime']}")
        
        # Tạo ảnh mẫu
        image_bytes = create_sample_image(sample['datetime'])
        
        # Lưu vào database
        record_id = save_testcan_report(
            datetime_value=sample['datetime'],
            value_502=sample['value_502'],
            value_505=sample['value_505'],
            value_508=sample['value_508'],
            value_574=sample['value_574'],
            image_bytes=image_bytes,
            image_filename=f"sample_{idx}.png",
            created_by=sample['created_by'],
            notes=sample['notes'],
            email_sent=sample['email_sent'],
            email_recipients=sample['email_recipients'],
            is_valid=sample['is_valid']
        )
        
        saved_ids.append(record_id)
        print(f"   ✓ Đã lưu với ID: {record_id}")
        print(f"   - Người tạo: {sample['created_by']}")
        print(f"   - Email: {'Đã gửi' if sample['email_sent'] else 'Chưa gửi'}")
        print(f"   - Hợp lệ: {'Có' if sample['is_valid'] else 'Không'}")
    
    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT!")
    print(f"Đã thêm {len(saved_ids)} báo cáo mẫu")
    print(f"IDs: {saved_ids}")
    
    # Hiển thị thống kê
    print("\n📊 THỐNG KÊ DATABASE:")
    print("=" * 60)
    stats = get_testcan_stats()
    print(f"Tổng báo cáo:     {stats['total_reports']}")
    print(f"Báo cáo hợp lệ:   {stats['valid_reports']}")
    print(f"Đã gửi email:     {stats['email_sent']}")
    print(f"Mới nhất:         {stats['latest_datetime']}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        add_sample_data()
        print("\n💡 Bây giờ hãy mở Streamlit và vào tab 'Lịch sử' để xem!")
        print("   URL: http://localhost:8501")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
