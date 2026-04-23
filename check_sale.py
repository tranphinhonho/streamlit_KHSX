import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check sale data for product 34 (511B)
cursor.execute('''
    SELECT SUM([Số lượng]) as total, COUNT(DISTINCT [Ngày sale]) as days
    FROM Sale 
    WHERE [ID sản phẩm] = 34 AND [Đã xóa] = 0
''')
result = cursor.fetchone()
print(f"San pham 511B (ID=34):")
print(f"  Tong ban: {result[0]}")
print(f"  So ngay ban: {result[1]}")

if result[0] and result[1]:
    aver = result[0] / result[1]
    print(f"  Aver: {aver:.0f} kg/ngay")
    print(f"  Neu ton kho = 72100 kg -> DOH = {72100/aver:.1f}")

# Check all sale data
cursor.execute('''
    SELECT COUNT(*) FROM Sale WHERE [Đã xóa] = 0
''')
print(f"\nTong so ban ghi Sale: {cursor.fetchone()[0]}")

conn.close()
