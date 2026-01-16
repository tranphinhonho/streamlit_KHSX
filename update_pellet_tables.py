"""
Script để thêm cột 'ID sản phẩm' vào bảng Pellet và PackingPlan
Chạy script này nếu database đã tồn tại
"""

import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

print("=" * 60)
print("CẬP NHẬT CẤU TRÚC DATABASE")
print("=" * 60)

# Kiểm tra và thêm cột ID sản phẩm vào Pellet
print("\n[1/2] Cập nhật bảng Pellet...")
try:
    cursor.execute("ALTER TABLE Pellet ADD COLUMN [ID sản phẩm] INTEGER")
    print("✓ Đã thêm cột 'ID sản phẩm' vào bảng Pellet")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ Cột 'ID sản phẩm' đã tồn tại trong bảng Pellet")
    else:
        print(f"✗ Lỗi: {e}")

# Kiểm tra và thêm cột ID sản phẩm vào PackingPlan
print("\n[2/2] Cập nhật bảng PackingPlan...")
try:
    cursor.execute("ALTER TABLE PackingPlan ADD COLUMN [ID sản phẩm] INTEGER")
    print("✓ Đã thêm cột 'ID sản phẩm' vào bảng PackingPlan")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ Cột 'ID sản phẩm' đã tồn tại trong bảng PackingPlan")
    else:
        print(f"✗ Lỗi: {e}")

# Commit
conn.commit()
cursor.close()
conn.close()

print("\n" + "=" * 60)
print("HOÀN TẤT CẬP NHẬT!")
print("=" * 60)
print("\nĐã thêm cột 'ID sản phẩm' vào:")
print("  ✓ Bảng Pellet")
print("  ✓ Bảng PackingPlan")
print("\nKhởi động lại Streamlit để áp dụng thay đổi!")
