"""
Script test gửi email qua Outlook
"""
import win32com.client as win32
from pathlib import Path

def test_send_email():
    try:
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        
        # Tìm tài khoản mixer2@cp.com.vn
        accounts = outlook.Session.Accounts
        target_account = None
        
        for idx in range(1, accounts.Count + 1):
            account = accounts.Item(idx)
            smtp_address = getattr(account, "SmtpAddress", "") or ""
            if "mixer2@cp.com.vn" in smtp_address.lower():
                target_account = account
                break
        
        if target_account:
            mail.SendUsingAccount = target_account
            print(f"✅ Đã chọn tài khoản: {target_account.SmtpAddress}")
        else:
            print("⚠️ Không tìm thấy tài khoản mixer2@cp.com.vn, dùng default account")
        
        # Thiết lập email
        mail.To = "phinho@cp.com.vn"
        mail.Subject = "Test email từ Python - Test Cân"
        mail.Body = """Đây là email test từ hệ thống Test Cân.

Nếu bạn nhận được email này, nghĩa là hệ thống gửi email hoạt động bình thường.

Trân trọng,
Hệ thống Test Cân
"""
        
        # Gửi email
        print("📤 Đang gửi email...")
        mail.Send()
        print("✅ Đã gửi email thành công!")
        print(f"   Từ: mixer2@cp.com.vn")
        print(f"   Đến: phinho@cp.com.vn")
        print(f"   Tiêu đề: {mail.Subject}")
        print()
        print("⚠️ LƯU Ý: Email có thể mất vài giây để được gửi đi.")
        print("   Hãy kiểm tra Outbox và Sent Items trong Outlook.")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_send_email()
