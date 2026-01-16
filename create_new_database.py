"""
Script khởi tạo database SQLite MỚI cho hệ thống B5-SQLite_Database
Tạo database mới với tên database_new.db
"""

import sqlite3
import os
from datetime import datetime
import streamlit_authenticator as stauth

# Đường dẫn database MỚI
database_path = 'database_new.db'

# Xóa nếu tồn tại
if os.path.exists(database_path):
    os.remove(database_path)
    print(f"Đã xóa {database_path} cũ")

# Kết nối database
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

print("=" * 60)
print("BẮT ĐẦU KHỞI TẠO DATABASE MỚI")
print("=" * 60)

# 1. Tạo bảng DonViTinh
print("\n[1/11] Tạo bảng DonViTinh...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS DonViTinh (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    [Mã đơn vị] TEXT NOT NULL,
    [Tên đơn vị] TEXT NOT NULL,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng DonViTinh")

# 2. Tạo bảng tbsys_ChucNangChinh
print("\n[2/11] Tạo bảng tbsys_ChucNangChinh...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_ChucNangChinh (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    [Chức năng chính] TEXT NOT NULL,
    Router TEXT,
    [Thứ tự ưu tiên] INTEGER,
    Icon TEXT,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng tbsys_ChucNangChinh")

# 3. Tạo bảng tbsys_VaiTro
print("\n[3/11] Tạo bảng tbsys_VaiTro...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_VaiTro (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    [Vai trò] TEXT NOT NULL,
    [Thứ tự ưu tiên] INTEGER,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng tbsys_VaiTro")

# 4. Tạo bảng tbsys_Users
print("\n[4/11] Tạo bảng tbsys_Users...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_Users (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL UNIQUE,
    Password TEXT,
    Fullname TEXT,
    Email TEXT,
    [Số điện thoại] TEXT,
    [Ngày sinh] DATE,
    [Giới tính] TEXT,
    ID_VaiTro INTEGER,
    [Địa chỉ] TEXT,
    [Hình ảnh] TEXT,
    [Thường trú] TEXT,
    [Tạm trú] TEXT,
    IsLock INTEGER DEFAULT 0,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng tbsys_Users")

# 5. Tạo bảng tbsys_DanhSachChucNang
print("\n[5/11] Tạo bảng tbsys_DanhSachChucNang...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_DanhSachChucNang (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    [ID Chức năng chính] INTEGER NOT NULL,
    [Chức năng con] TEXT NOT NULL,
    Router TEXT,
    Icon TEXT,
    [Thứ tự ưu tiên] INTEGER NOT NULL,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng tbsys_DanhSachChucNang")

# 6. Tạo bảng tbsys_ChucNangTheoVaiTro
print("\n[6/11] Tạo bảng tbsys_ChucNangTheoVaiTro...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_ChucNangTheoVaiTro (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    [ID Vai trò] INTEGER NOT NULL,
    [ID Danh sách chức năng] INTEGER NOT NULL,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng tbsys_ChucNangTheoVaiTro")

# 7. Tạo bảng tbsys_config
print("\n[7/11] Tạo bảng tbsys_config...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_config (
    config_key TEXT PRIMARY KEY,
    config_value TEXT
)
""")
print("✓ Đã tạo bảng tbsys_config")

# 8. Tạo bảng tbsys_ModuleChucNang
print("\n[8/11] Tạo bảng tbsys_ModuleChucNang...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_ModuleChucNang (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_DanhSachChucNang INTEGER NOT NULL,
    ModulePath TEXT,
    [Ghi chú] TEXT,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng tbsys_ModuleChucNang")

# 9. Tạo bảng tbsys_LichSuBackupDatabase
print("\n[9/11] Tạo bảng tbsys_LichSuBackupDatabase...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_LichSuBackupDatabase (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Database_Name TEXT,
    Backup_Path TEXT,
    Backup_Filename TEXT,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0
)
""")
print("✓ Đã tạo bảng tbsys_LichSuBackupDatabase")

# 10. Tạo bảng tbsys_Logs
print("\n[10/11] Tạo bảng tbsys_Logs...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS tbsys_Logs (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    Username TEXT,
    Action TEXT,
    TableName TEXT,
    Details TEXT,
    Status TEXT
)
""")
print("✓ Đã tạo bảng tbsys_Logs")

# 11. Tạo bảng sysdiagrams
print("\n[11/11] Tạo bảng sysdiagrams...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS sysdiagrams (
    name TEXT NOT NULL,
    principal_id INTEGER NOT NULL,
    diagram_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER,
    definition BLOB
)
""")
print("✓ Đã tạo bảng sysdiagrams")

conn.commit()

print("\n" + "=" * 60)
print("CHÈN DỮ LIỆU MẪU")
print("=" * 60)

# Chèn dữ liệu mẫu
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 1. Vai trò
print("\n[1/7] Chèn vai trò mẫu...")
roles = [
    (1, 'Admin', 1, 'phinho', current_time, 0),
    (2, 'Nhân viên', 2, 'phinho', current_time, 0),
    (3, 'Quản lý', 3, 'phinho', current_time, 0)
]
cursor.executemany("""
    INSERT INTO tbsys_VaiTro (ID, [Vai trò], [Thứ tự ưu tiên], [Người tạo], [Thời gian tạo], [Đã xóa])
    VALUES (?, ?, ?, ?, ?, ?)
""", roles)
print(f"✓ Đã chèn {len(roles)} vai trò")

# 2. User Admin
print("\n[2/7] Tạo tài khoản admin...")
# Mã hóa mật khẩu bằng streamlit_authenticator
hashed_password = stauth.Hasher(['nho123']).generate()[0]

cursor.execute("""
    INSERT INTO tbsys_Users (
        Username, Password, Fullname, ID_VaiTro, IsLock, [Người tạo], [Thời gian tạo], [Đã xóa]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", ('phinho', hashed_password, 'Phi Nho', 1, 0, 'system', current_time, 0))
print(f"✓ Đã tạo user: phinho / nho123")

# 3. Chức năng chính
print("\n[3/7] Chèn chức năng chính...")
main_functions = [
    (1, 'Danh mục', None, 1, 'list', 'phinho', current_time, 0),
    (2, 'Báo cáo', None, 2, 'file-text', 'phinho', current_time, 0)
]
cursor.executemany("""
    INSERT INTO tbsys_ChucNangChinh (
        ID, [Chức năng chính], Router, [Thứ tự ưu tiên], Icon, [Người tạo], [Thời gian tạo], [Đã xóa]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", main_functions)
print(f"✓ Đã chèn {len(main_functions)} chức năng chính")

# 4. Danh sách chức năng con
print("\n[4/7] Chèn chức năng con...")
sub_functions = [
    (1, 1, 'Đơn vị tính', None, None, 1, 'phinho', current_time, 0),
    (2, 1, 'Tỉnh/Thành phố', None, None, 2, 'phinho', current_time, 0)
]
cursor.executemany("""
    INSERT INTO tbsys_DanhSachChucNang (
        ID, [ID Chức năng chính], [Chức năng con], Router, Icon, 
        [Thứ tự ưu tiên], [Người tạo], [Thời gian tạo], [Đã xóa]
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", sub_functions)
print(f"✓ Đã chèn {len(sub_functions)} chức năng con")

# 5. Liên kết module
print("\n[5/7] Liên kết module...")
modules = [
    (1, 1, 'PagesKDE.DonViTinh', 'Module quản lý đơn vị tính', 'phinho', current_time, 0),
    (2, 2, 'PagesKDE.Tinh', 'Module quản lý tỉnh/thành phố', 'phinho', current_time, 0)
]
cursor.executemany("""
    INSERT INTO tbsys_ModuleChucNang (
        ID, ID_DanhSachChucNang, ModulePath, [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa]
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", modules)
print(f"✓ Đã liên kết {len(modules)} module")

# 6. Chức năng theo vai trò (Admin có tất cả quyền)
print("\n[6/7] Gán chức năng cho vai trò Admin...")
admin_permissions = [
    (1, 1, 1, 'phinho', current_time, 0),  # Admin - Đơn vị tính
    (2, 1, 2, 'phinho', current_time, 0)   # Admin - Tỉnh/TP
]
cursor.executemany("""
    INSERT INTO tbsys_ChucNangTheoVaiTro (
        ID, [ID Vai trò], [ID Danh sách chức năng], [Người tạo], [Thời gian tạo], [Đã xóa]
    ) VALUES (?, ?, ?, ?, ?, ?)
""", admin_permissions)
print(f"✓ Đã gán {len(admin_permissions)} quyền cho Admin")

# 7. Cấu hình hệ thống
print("\n[7/7] Chèn cấu hình hệ thống...")
configs = [
    ('project_name', 'Hệ Thống Quản Lý'),
    ('style_container_bg', '#2E3440'),
    ('style_icon_color', '#88C0D0'),
    ('style_icon_font_size', '22px'),
    ('style_nav_link_font_size', '16px'),
    ('style_nav_link_color', '#ECEFF4'),
    ('style_nav_link_hover_color', '#4C566A'),
    ('style_nav_link_selected_bg', '#81A1C1'),
    ('style_nav_link_selected_color', '#2E3440'),
    ('style_menu_icon', 'clipboard-data'),
    ('style_font_family', 'sans-serif')
]
cursor.executemany("""
    INSERT INTO tbsys_config (config_key, config_value)
    VALUES (?, ?)
""", configs)
print(f"✓ Đã chèn {len(configs)} cấu hình")

# 8. Đơn vị tính mẫu
print("\n[Bonus] Chèn một số đơn vị tính mẫu...")
units = [
    (1, 'DVT001', 'Cái', 'phinho', current_time, 0),
    (2, 'DVT002', 'Chiếc', 'phinho', current_time, 0),
    (3, 'DVT003', 'Kg', 'phinho', current_time, 0),
    (4, 'DVT004', 'Lít', 'phinho', current_time, 0),
    (5, 'DVT005', 'Mét', 'phinho', current_time, 0)
]
cursor.executemany("""
    INSERT INTO DonViTinh (ID, [Mã đơn vị], [Tên đơn vị], [Người tạo], [Thời gian tạo], [Đã xóa])
    VALUES (?, ?, ?, ?, ?, ?)
""", units)
print(f"✓ Đã chèn {len(units)} đơn vị tính mẫu")

# Commit tất cả thay đổi
conn.commit()

print("\n" + "=" * 60)
print("HOÀN TẤT KHỞI TẠO DATABASE")
print("=" * 60)
print(f"\n✅ Database đã được tạo tại: {os.path.abspath(database_path)}")
print("\n📝 BƯỚC TIẾP THEO:")
print("  1. Đổi tên file database_new.db thành database.db")
print("  2. Hoặc cập nhật config.json để trỏ đến database_new.db")
print("\n🔐 Thông tin đăng nhập:")
print("  Username: phinho")
print("  Password: nho123")
print("  Vai trò: Admin")
print("\n🚀 Chạy ứng dụng:")
print("  streamlit run main.py")
print("\n" + "=" * 60)

# Đóng kết nối
cursor.close()
conn.close()

print("\n✓ Đã đóng kết nối database")
print("✓ Khởi tạo hoàn tất!")
