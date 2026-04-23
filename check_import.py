import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# Check VT12 in StockOld after import
c.execute("""
    SELECT so.ID, sp.[Tên cám], so.[Số lượng], so.[Ngày stock old] 
    FROM StockOld so 
    JOIN SanPham sp ON so.[ID sản phẩm] = sp.ID
    WHERE sp.[Tên cám] LIKE '%VT%'
    ORDER BY so.ID DESC 
    LIMIT 10
""")
results = c.fetchall()
print(f"VT products in StockOld: {len(results)}")
for r in results:
    print(r)

# Check total count
c.execute("SELECT COUNT(*) FROM StockOld WHERE [Đã xóa] = 0")
print(f"\nTotal StockOld records: {c.fetchone()[0]}")

# Check if VT12 is in not_found during import - check log
c.execute("""
    SELECT [ID sản phẩm], [Số lượng], [Ghi chú] 
    FROM StockOld 
    WHERE [Đã xóa] = 0 
    ORDER BY ID DESC 
    LIMIT 5
""")
print("\nLatest 5 StockOld records:")
for r in c.fetchall():
    c2 = conn.cursor()
    c2.execute("SELECT [Tên cám] FROM SanPham WHERE ID = ?", (r[0],))
    sp = c2.fetchone()
    ten_cam = sp[0] if sp else 'Unknown'
    print(f"  ID SP: {r[0]}, Ten: {ten_cam}, SL: {r[1]}")

conn.close()
