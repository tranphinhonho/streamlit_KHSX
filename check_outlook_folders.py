"""
Kiểm tra Outbox và Sent Items trong Outlook
"""
import win32com.client as win32
from datetime import datetime, timedelta

def check_outlook_folders():
    outlook = win32.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    
    print("="*80)
    print("KIỂM TRA OUTBOX (Email đang chờ gửi)")
    print("="*80)
    
    try:
        outbox = namespace.GetDefaultFolder(4)  # 4 = olFolderOutbox
        items = outbox.Items
        items.Sort("[ReceivedTime]", True)
        
        print(f"Tổng số email trong Outbox: {items.Count}\n")
        
        if items.Count > 0:
            print("⚠️ CÓ EMAIL ĐANG CHỜ GỬI:")
            for i in range(min(10, items.Count)):
                item = items.Item(i + 1)
                try:
                    print(f"  {i+1}. To: {item.To}")
                    print(f"     Subject: {item.Subject}")
                    print(f"     CreationTime: {item.CreationTime}")
                    print()
                except:
                    pass
        else:
            print("✅ Outbox trống - tất cả email đã được gửi\n")
            
    except Exception as e:
        print(f"Lỗi khi kiểm tra Outbox: {e}\n")
    
    print("="*80)
    print("KIỂM TRA SENT ITEMS (Email đã gửi)")
    print("="*80)
    
    try:
        sent_items = namespace.GetDefaultFolder(5)  # 5 = olFolderSentMail
        items = sent_items.Items
        items.Sort("[ReceivedTime]", True)
        
        print(f"Tổng số email trong Sent Items: {items.Count}\n")
        
        # Lọc email gửi trong 1 giờ qua
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_emails = []
        
        print("📧 Email gửi trong 1 giờ qua:")
        for i in range(min(50, items.Count)):
            try:
                item = items.Item(i + 1)
                sent_time = item.SentOn
                
                # Convert COM date to Python datetime
                if hasattr(sent_time, 'year'):
                    if sent_time > cutoff_time:
                        recent_emails.append(item)
            except:
                pass
        
        if recent_emails:
            for idx, email in enumerate(recent_emails, 1):
                try:
                    print(f"\n  {idx}. To: {email.To}")
                    print(f"     Subject: {email.Subject}")
                    print(f"     SentOn: {email.SentOn}")
                    print(f"     Size: {email.Size} bytes")
                    
                    # Kiểm tra attachment
                    if email.Attachments.Count > 0:
                        print(f"     Attachments: {email.Attachments.Count}")
                        for j in range(1, email.Attachments.Count + 1):
                            att = email.Attachments.Item(j)
                            print(f"       - {att.FileName} ({att.Size} bytes)")
                except Exception as e:
                    print(f"     Lỗi: {e}")
        else:
            print("  Không có email nào gửi trong 1 giờ qua\n")
            
    except Exception as e:
        print(f"Lỗi khi kiểm tra Sent Items: {e}\n")
    
    print("="*80)
    print("KIỂM TRA INBOX (phinho@cp.com.vn)")
    print("="*80)
    
    try:
        inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        
        print(f"Tổng số email trong Inbox: {items.Count}\n")
        
        # Tìm email từ mixer2
        print("📬 Email từ mixer2@cp.com.vn trong Inbox:")
        found = False
        for i in range(min(100, items.Count)):
            try:
                item = items.Item(i + 1)
                sender = item.SenderEmailAddress
                
                if "mixer2" in sender.lower():
                    found = True
                    print(f"\n  From: {sender}")
                    print(f"  Subject: {item.Subject}")
                    print(f"  ReceivedTime: {item.ReceivedTime}")
            except:
                pass
        
        if not found:
            print("  ⚠️ Không tìm thấy email từ mixer2@cp.com.vn")
            
    except Exception as e:
        print(f"Lỗi khi kiểm tra Inbox: {e}\n")

if __name__ == "__main__":
    check_outlook_folders()
