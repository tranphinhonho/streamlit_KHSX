"""
Test gửi email từ mixer2@cp.com.vn đến phinho@cp.com.vn
"""
import win32com.client as win32
from pathlib import Path
from PIL import Image
import tempfile

print("="*60)
print("TEST GỬI EMAIL")
print("="*60)

try:
    # Tạo ảnh test
    image = Image.new('RGB', (200, 100), color='green')
    image_path = Path(tempfile.gettempdir()) / "testcan_final.png"
    image.save(image_path, format='PNG')
    print(f"✅ Đã tạo ảnh: {image_path}")
    
    # Outlook
    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    
    # Tìm tài khoản mixer2
    accounts = outlook.Session.Accounts
    mixer2_account = None
    
    print(f"\nTài khoản Outlook có sẵn: {accounts.Count}")
    for idx in range(1, accounts.Count + 1):
        account = accounts.Item(idx)
        smtp = getattr(account, "SmtpAddress", "")
        print(f"  {idx}. {smtp}")
        if "mixer2@cp.com.vn" in smtp.lower():
            mixer2_account = account
    
    if mixer2_account:
        mail.SendUsingAccount = mixer2_account
        print(f"\n✅ Đã chọn tài khoản: {mixer2_account.SmtpAddress}")
    else:
        print("\n⚠️ Không tìm thấy mixer2@cp.com.vn, dùng default")
    
    # Thiết lập email
    mail.To = "phinho@cp.com.vn"
    mail.Subject = "TEST - Báo cáo Test Cân (với attachment)"
    mail.Body = """Đây là email test từ hệ thống Test Cân.

Kết quả Test cân:
- Thời gian: 2025-12-03 15:30:00
- 502: 85.5
- 505: 15.2
- 508: 1000.0
- 574: 20.0

(Email này có đính kèm hình ảnh)

Trân trọng,
Hệ thống Test Cân
"""
    
    # Đính kèm ảnh
    mail.Attachments.Add(str(image_path))
    print(f"✅ Đã thêm attachment: {image_path.name}")
    
    # Gửi
    print("\n📤 Đang gửi email...")
    mail.Send()
    
    print("✅ Email đã được gửi!")
    print("\n" + "="*60)
    print("THÔNG TIN:")
    print(f"  Từ: mixer2@cp.com.vn")
    print(f"  Đến: phinho@cp.com.vn")
    print(f"  Tiêu đề: TEST - Báo cáo Test Cân (với attachment)")
    print(f"  Attachment: testcan_final.png")
    print("="*60)
    
    print("\n⚠️ LƯU Ý:")
    print("  1. Kiểm tra Outlook → Sent Items")
    print("  2. Kiểm tra Inbox của phinho@cp.com.vn")
    print("  3. Kiểm tra Junk Email nếu không thấy trong Inbox")
    print("  4. Email có thể mất vài phút để được gửi/nhận")
    
    # Trigger SendAndReceive
    try:
        namespace = outlook.GetNamespace("MAPI")
        namespace.SendAndReceive(False)
        print("\n✅ Đã trigger Send/Receive")
    except:
        print("\n⚠️ Không thể trigger Send/Receive (không sao)")
    
except Exception as e:
    print(f"\n❌ LỖI: {e}")
    import traceback
    traceback.print_exc()
