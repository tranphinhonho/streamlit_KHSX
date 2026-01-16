"""
Script kiểm tra chi tiết việc gửi email
"""
import win32com.client as win32
from pathlib import Path
import tempfile
from PIL import Image

def check_outlook_accounts():
    """Kiểm tra các tài khoản Outlook"""
    print("="*60)
    print("KIỂM TRA TÀI KHOẢN OUTLOOK")
    print("="*60)
    
    outlook = win32.Dispatch("Outlook.Application")
    accounts = outlook.Session.Accounts
    
    print(f"Tổng số tài khoản: {accounts.Count}\n")
    
    for idx in range(1, accounts.Count + 1):
        account = accounts.Item(idx)
        print(f"Tài khoản #{idx}:")
        print(f"  DisplayName: {getattr(account, 'DisplayName', 'N/A')}")
        print(f"  SmtpAddress: {getattr(account, 'SmtpAddress', 'N/A')}")
        print(f"  AccountType: {getattr(account, 'AccountType', 'N/A')}")
        print()

def test_send_with_attachment():
    """Test gửi email với attachment"""
    print("="*60)
    print("TEST GỬI EMAIL VỚI ATTACHMENT")
    print("="*60)
    
    try:
        # Tạo ảnh test
        image = Image.new('RGB', (200, 100), color='blue')
        image_path = Path(tempfile.gettempdir()) / "test_attachment.png"
        image.save(image_path, format='PNG')
        print(f"✅ Đã tạo ảnh test: {image_path}")
        
        # Tạo email
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        
        # Tìm và set tài khoản mixer2
        accounts = outlook.Session.Accounts
        target_account = None
        for idx in range(1, accounts.Count + 1):
            account = accounts.Item(idx)
            if "mixer2@cp.com.vn" in getattr(account, "SmtpAddress", "").lower():
                target_account = account
                break
        
        if target_account:
            mail.SendUsingAccount = target_account
            print(f"✅ Đã chọn tài khoản: {target_account.SmtpAddress}")
        else:
            print("⚠️ Không tìm thấy tài khoản mixer2@cp.com.vn")
        
        # Setup email
        mail.To = "phinho@cp.com.vn"
        mail.Subject = f"Test Email với Attachment - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
        mail.Body = """Email test từ Python script.

Đây là email có đính kèm hình ảnh để kiểm tra:
1. Tài khoản gửi: mixer2@cp.com.vn
2. Người nhận: phinho@cp.com.vn
3. Có attachment: test_attachment.png

Nếu nhận được email này với attachment, nghĩa là hệ thống hoạt động bình thường.
"""
        
        # Thêm attachment
        mail.Attachments.Add(str(image_path))
        print(f"✅ Đã thêm attachment: {image_path.name}")
        
        # Gửi email
        print("\n📤 Đang gửi email...")
        mail.Send()
        print("✅ Email đã được gửi!")
        
        print("\n" + "="*60)
        print("THÔNG TIN EMAIL:")
        print(f"  Từ: mixer2@cp.com.vn (hoặc default account)")
        print(f"  Đến: phinho@cp.com.vn")
        print(f"  Tiêu đề: {mail.Subject}")
        print(f"  Attachment: test_attachment.png")
        print("="*60)
        
        print("\n⚠️ LƯU Ý:")
        print("  - Email có thể mất vài giây/phút để được gửi")
        print("  - Kiểm tra Outbox trong Outlook (email đang chờ gửi)")
        print("  - Kiểm tra Sent Items (email đã gửi)")
        print("  - Kiểm tra Inbox của phinho@cp.com.vn")
        print("  - Có thể kiểm tra Junk Email nếu không thấy trong Inbox")
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import pandas as pd
    check_outlook_accounts()
    print("\n")
    test_send_with_attachment()
