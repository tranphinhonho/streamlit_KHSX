import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# From screenshots, the menu is in tbsys_DanhSachChucNang with ID 16
# Column "Chức năng con" = "Stock hôm nay"

# Update Danh sách chức năng (ID 16, "Chức năng con")
print("=== Updating tbsys_DanhSachChucNang ===")
c.execute("UPDATE tbsys_DanhSachChucNang SET [Chức năng con] = 'Stock đầu ngày' WHERE [Chức năng con] = 'Stock hôm nay'")
print(f'Updated {c.rowcount} rows in tbsys_DanhSachChucNang')

# Update Chức năng theo vai trò if needed
print("\n=== Check tbsys_ChucNangTheoVaiTro ===")
try:
    c.execute("UPDATE tbsys_ChucNangTheoVaiTro SET [Chức năng con] = 'Stock đầu ngày' WHERE [Chức năng con] = 'Stock hôm nay'")
    print(f'Updated {c.rowcount} rows in tbsys_ChucNangTheoVaiTro')
except Exception as e:
    print(f'Error: {e}')

# Update Module liên kết if needed  
print("\n=== Check tbsys_ModuleChucNang ===")
try:
    c.execute("UPDATE tbsys_ModuleChucNang SET [Chức năng con] = 'Stock đầu ngày' WHERE [Chức năng con] = 'Stock hôm nay'")
    print(f'Updated {c.rowcount} rows in tbsys_ModuleChucNang')
except Exception as e:
    print(f'Error: {e}')

conn.commit()

# Verify
print("\n=== Verification ===")
c.execute("SELECT * FROM tbsys_DanhSachChucNang WHERE [Chức năng con] LIKE '%Stock%'")
for row in c.fetchall():
    print(f'  {row}')

conn.close()
print('\nDone!')
