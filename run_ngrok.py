"""
Script chạy Streamlit app với ngrok tunnel
Cho phép truy cập app từ internet

Bước 1: Đăng ký tài khoản miễn phí tại https://ngrok.com/signup
Bước 2: Lấy authtoken từ https://dashboard.ngrok.com/get-started/your-authtoken
Bước 3: Chạy script này và nhập authtoken khi được yêu cầu
"""

import subprocess
import sys
import time
import webbrowser

def main():
    # Kiểm tra ngrok đã config chưa
    try:
        from pyngrok import ngrok, conf
    except ImportError:
        print("❌ Chưa cài pyngrok. Đang cài...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyngrok"])
        from pyngrok import ngrok, conf
    
    # Kiểm tra authtoken
    print("=" * 60)
    print("🌐 SETUP NGROK - Truy cập app từ internet")
    print("=" * 60)
    
    print("""
📋 Hướng dẫn:
1. Đăng ký miễn phí: https://ngrok.com/signup
2. Lấy authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
3. Nhập authtoken bên dưới
""")
    
    # Mở trang đăng ký
    open_browser = input("Mở trang đăng ký ngrok? (y/n): ").lower()
    if open_browser == 'y':
        webbrowser.open("https://ngrok.com/signup")
        print("\n⏳ Đợi bạn đăng ký và lấy authtoken...")
        time.sleep(3)
    
    # Nhập authtoken
    authtoken = input("\n🔑 Nhập ngrok authtoken: ").strip()
    
    if authtoken:
        ngrok.set_auth_token(authtoken)
        print("✅ Đã lưu authtoken!")
    
    # Tạo tunnel
    print("\n🚀 Đang tạo tunnel...")
    
    try:
        # Mở tunnel tới port 8503
        public_url = ngrok.connect(8503)
        
        print("\n" + "=" * 60)
        print("🎉 THÀNH CÔNG!")
        print("=" * 60)
        print(f"\n🌐 URL công khai: {public_url}")
        print(f"\n📤 Gửi link này cho mọi người để demo:")
        print(f"   {public_url}")
        print("\n⚠️  Giữ cửa sổ này mở để duy trì kết nối")
        print("   Nhấn Ctrl+C để dừng")
        print("=" * 60)
        
        # Mở browser
        webbrowser.open(str(public_url))
        
        # Giữ script chạy
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Đang dừng ngrok...")
            ngrok.kill()
            print("✅ Đã dừng!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print("\n💡 Kiểm tra:")
        print("   1. App Streamlit đang chạy ở port 8503?")
        print("   2. Authtoken có đúng không?")


if __name__ == "__main__":
    main()
