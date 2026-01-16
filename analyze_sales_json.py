"""
Script phan tich du lieu ban hang va xuat ra JSON
"""
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

result = {}

# Stats
cursor.execute("""
    SELECT COUNT(*), COALESCE(SUM([Số lượng]), 0)
    FROM Sale 
    WHERE [Ngày sale] >= '2026-01-02'
""")
stats = cursor.fetchone()
result['tong_don'] = stats[0]
result['tong_kg'] = float(stats[1]) if stats[1] else 0

# Top products
cursor.execute("""
    SELECT 
        sp.[Code cám],
        sp.[Tên cám],
        COUNT(*) as so_lan,
        COALESCE(SUM(s.[Số lượng]), 0) as tong,
        COALESCE(ROUND(AVG(s.[Số lượng]), 0), 0) as tb,
        sp.[Batch size]
    FROM Sale s
    LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
    WHERE s.[Ngày sale] >= '2026-01-02'
    GROUP BY s.[ID sản phẩm]
    ORDER BY tong DESC
    LIMIT 20
""")
result['top_products'] = []
for row in cursor.fetchall():
    result['top_products'].append({
        'code': row[0] or 'N/A',
        'name': row[1] or 'N/A', 
        'count': row[2],
        'total_kg': float(row[3]),
        'avg_kg': float(row[4]),
        'batch': float(row[5]) if row[5] else None
    })

# Day of week analysis
cursor.execute("""
    SELECT 
        strftime('%w', [Ngày sale]) as dow,
        COUNT(*) as cnt,
        COALESCE(SUM([Số lượng]), 0) as total
    FROM Sale 
    WHERE [Ngày sale] >= '2026-01-02'
    GROUP BY dow
    ORDER BY dow
""")
days = ['Chu Nhat', 'Thu Hai', 'Thu Ba', 'Thu Tu', 'Thu Nam', 'Thu Sau', 'Thu Bay']
result['by_day'] = {}
for row in cursor.fetchall():
    result['by_day'][days[int(row[0])]] = {'count': row[1], 'total_kg': float(row[2])}

# Today's suggestion
today_dow = datetime.now().weekday()
sql_dow = str((today_dow + 1) % 7)
result['today'] = days[int(sql_dow)]

cursor.execute("""
    SELECT 
        sp.[Code cám],
        sp.[Tên cám],
        COALESCE(ROUND(AVG(s.[Số lượng]), 0), 0) as tb,
        sp.[Batch size]
    FROM Sale s
    LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
    WHERE s.[Ngày sale] >= '2026-01-02'
      AND strftime('%w', s.[Ngày sale]) = ?
    GROUP BY s.[ID sản phẩm]
    ORDER BY SUM(s.[Số lượng]) DESC
    LIMIT 15
""", (sql_dow,))
result['today_suggestion'] = []
for row in cursor.fetchall():
    avg = float(row[2])
    batch = float(row[3]) if row[3] else avg
    if batch > 0 and avg > 0:
        suggested = int((avg // batch + 1) * batch) if avg % batch != 0 else int(avg)
    else:
        suggested = int(avg)
    result['today_suggestion'].append({
        'code': row[0] or 'N/A',
        'name': row[1] or 'N/A',
        'avg_kg': avg,
        'batch': batch,
        'suggested': suggested
    })

conn.close()
print(json.dumps(result, ensure_ascii=False, indent=2))
