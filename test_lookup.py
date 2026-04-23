import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# Test exact match for VT12
test_values = ['VT12', 'vt12', 'VT11', '203101', '552']

for val in test_values:
    # Test Code cám
    c.execute("SELECT ID, [Code cám], [Tên cám] FROM SanPham WHERE TRIM([Code cám]) = ? AND [Đã xóa] = 0", (val.strip(),))
    result1 = c.fetchall()
    
    # Test Tên cám 
    c.execute("SELECT ID, [Code cám], [Tên cám] FROM SanPham WHERE UPPER(TRIM([Tên cám])) = UPPER(?) AND [Đã xóa] = 0", (val.strip(),))
    result2 = c.fetchall()
    
    print(f"Search '{val}':")
    print(f"  By Code cam: {result1}")
    print(f"  By Ten cam:  {result2}")
    print()

conn.close()
