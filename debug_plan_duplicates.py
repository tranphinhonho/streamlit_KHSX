# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check for duplicate code cám in Plan
cursor.execute("""
    SELECT 
        p.[Code cám],
        p.[Tên cám],
        COUNT(*) as count,
        SUM(pl.[Số lượng]) as total_qty
    FROM Plan pl
    LEFT JOIN SanPham p ON pl.[ID sản phẩm] = p.ID
    WHERE pl.[Đã xóa] = 0
    GROUP BY p.[Code cám]
    HAVING COUNT(*) > 1
    ORDER BY count DESC
""")

results = cursor.fetchall()
print(f"Duplicate code cám in Plan: {len(results)} items")
print("=" * 60)
for r in results:
    print(f"{r[0]} | {r[1]} | {r[2]} lần | Tổng: {r[3]:,.0f} kg")

# Total unique products
cursor.execute("""
    SELECT COUNT(DISTINCT p.[Code cám])
    FROM Plan pl
    LEFT JOIN SanPham p ON pl.[ID sản phẩm] = p.ID
    WHERE pl.[Đã xóa] = 0
""")
unique_count = cursor.fetchone()[0]
print(f"\nTổng số code cám unique: {unique_count}")

# Total records
cursor.execute("SELECT COUNT(*) FROM Plan WHERE [Đã xóa] = 0")
total_count = cursor.fetchone()[0]
print(f"Tổng số dòng trong Plan: {total_count}")

conn.close()
