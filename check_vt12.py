import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# Check VT12 in SanPham
c.execute("SELECT ID, [Code cám], [Tên cám] FROM SanPham WHERE [Tên cám] LIKE '%VT12%'")
print("SanPham VT12:", c.fetchall())

# Check VT12 in StockOld
c.execute("""
    SELECT so.ID, so.[ID sản phẩm], so.[Số lượng], so.[Ngày stock old], sp.[Tên cám]
    FROM StockOld so 
    JOIN SanPham sp ON so.[ID sản phẩm] = sp.ID
    WHERE sp.[Tên cám] LIKE '%VT12%'
    ORDER BY so.ID DESC 
    LIMIT 5
""")
print("StockOld VT12:", c.fetchall())

conn.close()
