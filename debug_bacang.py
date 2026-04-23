# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check Bá Cang orders for 25/01/2026
cursor.execute("""
    SELECT 
        d.[ID sản phẩm],
        p.[Code cám],
        p.[Tên cám],
        d.[Số lượng],
        d.[Ngày lấy]
    FROM DatHang d
    LEFT JOIN SanPham p ON d.[ID sản phẩm] = p.ID
    WHERE d.[Đã xóa] = 0 
    AND d.[Loại đặt hàng] = 'Đại lý Bá Cang'
    AND d.[Ngày lấy] = '2026-01-25'
    ORDER BY p.[Tên cám]
""")

results = cursor.fetchall()
print(f"Bá Cang orders for 25/01/2026: {len(results)} items")
print("=" * 60)
for r in results:
    print(f"{r[1]} | {r[2]} | {r[3]:,.0f} kg | {r[4]}")

# Check specifically for 552, 552S, 553S
print("\n" + "=" * 60)
print("Kiểm tra 552, 552S, 553S:")
cursor.execute("""
    SELECT 
        p.[Tên cám],
        SUM(d.[Số lượng]) as total
    FROM DatHang d
    LEFT JOIN SanPham p ON d.[ID sản phẩm] = p.ID
    WHERE d.[Đã xóa] = 0 
    AND d.[Loại đặt hàng] = 'Đại lý Bá Cang'
    AND d.[Ngày lấy] = '2026-01-25'
    AND p.[Tên cám] IN ('552', '552S', '553S')
    GROUP BY p.[Tên cám]
""")
for r in cursor.fetchall():
    print(f"  {r[0]}: {r[1]:,.0f} kg")

conn.close()
