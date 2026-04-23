# Script kiểm tra dữ liệu TonBon
import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# Kiểm tra các ngày có dữ liệu
c.execute("SELECT DISTINCT [Ngày kiểm kho] FROM TonBon WHERE [Đã xóa] = 0 ORDER BY [Ngày kiểm kho] DESC")
print("Các ngày có dữ liệu:")
for row in c.fetchall():
    print(f"  - {row[0]}")

# Kiểm tra tổng theo ngày
c.execute("""
    SELECT [Ngày kiểm kho], SUM([Số lượng (kg)]) as tong
    FROM TonBon 
    WHERE [Đã xóa] = 0 
    GROUP BY [Ngày kiểm kho]
    ORDER BY [Ngày kiểm kho] DESC
""")
print("\nTổng theo ngày:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]:,.0f} kg")

conn.close()
