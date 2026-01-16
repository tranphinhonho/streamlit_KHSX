"""
Script kiểm tra các tài khoản Outlook có sẵn
"""
import win32com.client as win32

try:
    outlook = win32.Dispatch("Outlook.Application")
    accounts = outlook.Session.Accounts
    
    print(f"Số lượng tài khoản Outlook: {accounts.Count}")
    print("-" * 60)
    
    for idx in range(1, accounts.Count + 1):
        account = accounts.Item(idx)
        smtp_address = getattr(account, "SmtpAddress", "") or ""
        display_name = getattr(account, "DisplayName", "") or ""
        account_type = getattr(account, "AccountType", "") or ""
        
        print(f"Tài khoản #{idx}:")
        print(f"  Display Name: {display_name}")
        print(f"  SMTP Address: {smtp_address}")
        print(f"  Account Type: {account_type}")
        print()
    
    # Kiểm tra xem có tài khoản mixer2@cp.com.vn không
    found = False
    for idx in range(1, accounts.Count + 1):
        account = accounts.Item(idx)
        smtp_address = getattr(account, "SmtpAddress", "") or ""
        display_name = getattr(account, "DisplayName", "") or ""
        
        if "mixer2@cp.com.vn" in smtp_address.lower() or "mixer2@cp.com.vn" in display_name.lower():
            print("✅ Tìm thấy tài khoản mixer2@cp.com.vn")
            found = True
            break
    
    if not found:
        print("❌ KHÔNG tìm thấy tài khoản mixer2@cp.com.vn")
        print("Bạn cần thêm tài khoản này vào Outlook hoặc dùng tài khoản khác có sẵn.")

except Exception as e:
    print(f"Lỗi: {e}")
    import traceback
    traceback.print_exc()
