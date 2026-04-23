import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Tìm sản phẩm 6951 trong bảng SanPham
print("=== Tìm 6951 trong SanPham ===")
cursor.execute("SELECT [Tên cám], [Code cám], [Kích cỡ ép viên], [Vật nuôi] FROM SanPham WHERE [Tên cám] LIKE '%6951%' OR [Code cám] LIKE '%6951%'")
rows = cursor.fetchall()
for r in rows:
    print(f"Tên cám: {r[0]}, Code cám: {r[1]}, Kích cỡ: {r[2]}, Vật nuôi: {r[3]}")

print("\n=== Tìm 6951XS87 trong PelletCapacity ===")
cursor.execute("SELECT [Code cám], [Ngày] FROM PelletCapacity WHERE [Code cám] LIKE '%6951XS%' LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(f"Code cám: {r[0]}, Ngày: {r[1]}")

conn.close()
