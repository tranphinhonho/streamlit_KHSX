import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# Tìm các Code cám có nhiều Tên cám khác nhau
c.execute("""
    SELECT [Code cám], COUNT(*) as cnt, GROUP_CONCAT([Tên cám]) as ten_cam_list
    FROM SanPham 
    WHERE [Đã xóa] = 0
    GROUP BY [Code cám]
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    LIMIT 20
""")

print("Code cám có nhiều Tên cám:")
for row in c.fetchall():
    print(f"  Code: {row[0]}, Count: {row[1]}, Tên cám: {row[2]}")

# Kiểm tra code 203101 (VT12)
print("\n\nSản phẩm có Code cám = 203101:")
c.execute("SELECT ID, [Code cám], [Tên cám] FROM SanPham WHERE [Code cám] = '203101' AND [Đã xóa] = 0")
for row in c.fetchall():
    print(f"  ID: {row[0]}, Code: {row[1]}, Tên: {row[2]}")

# Kiểm tra code 321001 (552)
print("\nSản phẩm có Code cám = 321001:")
c.execute("SELECT ID, [Code cám], [Tên cám] FROM SanPham WHERE [Code cám] = '321001' AND [Đã xóa] = 0")
for row in c.fetchall():
    print(f"  ID: {row[0]}, Code: {row[1]}, Tên: {row[2]}")

conn.close()
