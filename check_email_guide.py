"""
Hướng dẫn kiểm tra email và khắc phục sự cố
"""

print("="*70)
print("HƯỚNG DẪN KIỂM TRA EMAIL")
print("="*70)

print("""
1. MỞ OUTLOOK DESKTOP hoặc OUTLOOK WEB APP:
   - Desktop: Mở Microsoft Outlook trên máy tính
   - Web: Truy cập https://outlook.office.com

2. KIỂM TRA SENT ITEMS (Email đã gửi):
   - Vào thư mục "Sent Items"
   - Tìm email với tiêu đề: "TEST - Báo cáo Test Cân"
   - Từ: mixer2@cp.com.vn
   - Đến: phinho@cp.com.vn
   - Nếu THẤY → Email đã gửi thành công ✅

3. KIỂM TRA INBOX (phinho@cp.com.vn):
   - Đăng nhập với tài khoản phinho@cp.com.vn
   - Kiểm tra Inbox
   - Kiểm tra Junk Email / Spam
   - Kiểm tra Focused / Other (nếu có)

4. NGUYÊN NHÂN EMAIL KHÔNG NHẬN ĐƯỢC:
   
   a) Email bị lọc vào Junk/Spam:
      → Kiểm tra thư mục Junk Email
      → Đánh dấu mixer2@cp.com.vn là "Safe Sender"
   
   b) Email bị chặn bởi Exchange Server:
      → Liên hệ IT để kiểm tra Exchange logs
      → Có thể cần whitelist mixer2@cp.com.vn
   
   c) Email chậm do network:
      → Đợi 5-10 phút
      → Refresh Inbox (F9)
   
   d) Cùng domain nên bị filter:
      → mixer2@cp.com.vn và phinho@cp.com.vn cùng @cp.com.vn
      → Exchange có thể có rule đặc biệt cho internal email

5. GIẢI PHÁP:
   
   ✅ Option 1: Sử dụng chức năng "Lưu nhanh"
      - Không cần gửi email
      - Lưu trực tiếp vào database
      - Xuất Excel theo tuần/tháng
   
   ✅ Option 2: Thay đổi người nhận
      - Thử gửi đến email khác (không cùng domain)
      - Test xem có nhận được không
   
   ✅ Option 3: Display email thay vì Send
      - Email sẽ hiện trong Outlook để review
      - Bạn tự nhấn Send trong Outlook
      - Đảm bảo email được gửi đúng

6. TEST NGAY:
   - Vào http://localhost:8501
   - Tab "Test Cân OCR"
   - Upload ảnh
   - Nhấn "💾 Lưu nhanh" (không cần email)
   - Vào tab "Lịch sử" xem dữ liệu đã lưu
""")

print("="*70)

# Kiểm tra Outlook Sent Items
print("\n\nKIỂM TRA SENT ITEMS TỰ ĐỘNG:")
print("="*70)

try:
    import win32com.client as win32
    from datetime import datetime, timedelta
    
    outlook = win32.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    sent_items = namespace.GetDefaultFolder(5)
    items = sent_items.Items
    items.Sort("[SentOn]", True)
    
    print(f"Tổng email trong Sent Items: {items.Count}")
    
    # Tìm email test vừa gửi
    found = False
    print("\nEmail gửi trong 10 phút qua:")
    cutoff = datetime.now() - timedelta(minutes=10)
    
    for i in range(min(20, items.Count)):
        try:
            item = items.Item(i + 1)
            sent_time = item.SentOn
            
            if hasattr(sent_time, 'year') and sent_time > cutoff:
                if "phinho@cp.com.vn" in item.To.lower():
                    found = True
                    print(f"\n✅ TÌM THẤY EMAIL!")
                    print(f"  To: {item.To}")
                    print(f"  Subject: {item.Subject}")
                    print(f"  SentOn: {sent_time}")
                    if item.Attachments.Count > 0:
                        print(f"  Attachments: {item.Attachments.Count}")
                    break
        except:
            pass
    
    if not found:
        print("⚠️ Không tìm thấy email gửi đến phinho@cp.com.vn trong 10 phút qua")
        print("   → Có thể email vẫn đang trong Outbox")
        print("   → Hoặc đã gửi nhưng không trigger được search")
    
except Exception as e:
    print(f"Lỗi khi kiểm tra: {e}")

print("\n" + "="*70)
