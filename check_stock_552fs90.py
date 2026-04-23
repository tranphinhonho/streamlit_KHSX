import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Tìm ID sản phẩm của 552FS90
cursor.execute('''
    SELECT ID, [Code cám], [Tên cám] FROM SanPham 
    WHERE [Tên cám] = '552FS90' AND [Đã xóa] = 0
''')
products = cursor.fetchall()
print('=== Sản phẩm 552FS90 ===')
for p in products:
    print(f'ID: {p[0]}, Code: {p[1]}, Tên: {p[2]}')

if products:
    product_id = products[0][0]
    
    # Kiểm tra stock ngày 24/01/2026 và 25/01/2026
    print('\n=== Stock các ngày 24-31/01/2026 ===')
    cursor.execute('''
        SELECT [Ngày stock], [Số lượng], [Ghi chú 2]
        FROM StockHomNay
        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
        AND [Ngày stock] >= '2026-01-24' AND [Ngày stock] <= '2026-01-31'
        ORDER BY [Ngày stock]
    ''', (product_id,))
    stocks = cursor.fetchall()
    
    if not stocks:
        print('Không có dữ liệu stock cho khoảng thời gian này!')
    else:
        for s in stocks:
            print(f'Ngày: {s[0]}, Số lượng: {s[1]:,} kg')
            print(f'  GC2: {s[2]}')
            print()

conn.close()
