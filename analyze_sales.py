"""
Script phân tích thói quen bán hàng từ ngày 2 đến hiện tại 
và gợi ý kế hoạch sản xuất cho hôm nay (14/01/2026 - Thứ Tư)
"""
import sqlite3
from datetime import datetime

# Kết nối database
conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

print("=" * 70)
print("PHAN TICH THOI QUEN BAN HANG & GOI Y KE HOACH SAN XUAT")
print("=" * 70)

# Lấy dữ liệu Sale từ ngày 2/1/2026 đến nay
print("\n[DU LIEU BAN HANG (tu 02/01/2026 den nay)]")
print("-" * 50)
cursor.execute("""
    SELECT COUNT(*), SUM([Số lượng]) 
    FROM Sale 
    WHERE [Ngày sale] >= '2026-01-02'
""")
stats = cursor.fetchone()
print(f"Tong so don hang: {stats[0]}")
print(f"Tong so luong: {stats[1]:,.0f} kg" if stats[1] else "Tong so luong: 0 kg")

# Top sản phẩm bán chạy nhất
print("\n[TOP 15 SAN PHAM BAN CHAY NHAT]")
print("-" * 50)
cursor.execute("""
    SELECT 
        sp.[Code cám],
        sp.[Tên cám],
        COUNT(*) as so_lan_ban,
        SUM(s.[Số lượng]) as tong_so_luong,
        ROUND(AVG(s.[Số lượng]), 0) as trung_binh,
        sp.[Batch size]
    FROM Sale s
    LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
    WHERE s.[Ngày sale] >= '2026-01-02'
    GROUP BY s.[ID sản phẩm]
    ORDER BY tong_so_luong DESC
    LIMIT 15
""")
top_products = cursor.fetchall()
print(f"{'Code':<8} {'Ten san pham':<25} {'So lan':>8} {'Tong (kg)':>12} {'TB/lan':>10} {'Batch':>8}")
print("-" * 80)
for row in top_products:
    code = row[0] if row[0] else "N/A"
    name = (row[1][:22] + "...") if row[1] and len(row[1]) > 25 else (row[1] or "N/A")
    batch = f"{row[5]:,.0f}" if row[5] else "N/A"
    total = f"{row[3]:,.0f}" if row[3] else "0"
    avg = f"{row[4]:,.0f}" if row[4] else "0"
    print(f"{code:<8} {name:<25} {row[2]:>8} {total:>12} {avg:>10} {batch:>8}")

# Phân tích theo ngày trong tuần
print("\n[PHAN TICH THEO NGAY TRONG TUAN]")
print("-" * 50)
cursor.execute("""
    SELECT 
        strftime('%w', [Ngày sale]) as day_of_week,
        COUNT(*) as so_don,
        ROUND(SUM([Số lượng]), 0) as tong_kg
    FROM Sale 
    WHERE [Ngày sale] >= '2026-01-02'
    GROUP BY day_of_week
    ORDER BY day_of_week
""")
dow_analysis = cursor.fetchall()
days = ['Chu Nhat', 'Thu Hai', 'Thu Ba', 'Thu Tu', 'Thu Nam', 'Thu Sau', 'Thu Bay']
for row in dow_analysis:
    day_idx = int(row[0])
    total_kg = f"{row[2]:,.0f}" if row[2] else "0"
    print(f"  {days[day_idx]:<12}: {row[1]:>5} don  |  {total_kg:>12} kg")

# Hôm nay là Thứ Tư (14/01/2026)  
today = datetime.now()
today_dow = today.weekday()  # 0=Monday, 2=Wednesday
sql_dow = str((today_dow + 1) % 7)  # SQLite dùng 0=Sunday, 3=Wednesday

print("\n" + "=" * 70)
print(f"GOI Y KE HOACH SAN XUAT CHO {days[int(sql_dow)].upper()} - {today.strftime('%d/%m/%Y')}")
print("=" * 70)

# Gợi ý dựa trên thói quen bán hàng cùng thứ
print(f"\nDua tren thoi quen ban hang vao {days[int(sql_dow)]}:")
print("-" * 50)
cursor.execute("""
    SELECT 
        sp.[Code cám],
        sp.[Tên cám],
        COUNT(*) as so_lan_ban,
        SUM(s.[Số lượng]) as tong_so_luong,
        ROUND(AVG(s.[Số lượng]), 0) as trung_binh_ngay,
        sp.[Batch size]
    FROM Sale s
    LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
    WHERE s.[Ngày sale] >= '2026-01-02'
      AND strftime('%w', s.[Ngày sale]) = ?
    GROUP BY s.[ID sản phẩm]
    ORDER BY tong_so_luong DESC
    LIMIT 20
""", (sql_dow,))
today_suggestions = cursor.fetchall()

if today_suggestions:
    print(f"{'STT':<4} {'Code':<8} {'Ten san pham':<30} {'TB ban/ngay':>12} {'Goi y SX':>10}")
    print("-" * 70)
    for i, row in enumerate(today_suggestions, 1):
        code = row[0] if row[0] else "N/A"
        name = (row[1][:27] + "...") if row[1] and len(row[1]) > 30 else (row[1] or "N/A")
        avg = row[4] if row[4] else 0
        batch = row[5] if row[5] else avg
        # Gợi ý sản xuất = làm tròn lên batch size
        if batch and avg:
            suggested = int((avg // batch + 1) * batch) if avg % batch != 0 else int(avg)
        else:
            suggested = int(avg) if avg else 0
        print(f"{i:<4} {code:<8} {name:<30} {avg:>12,.0f} {suggested:>10,}")
else:
    print("Khong co du lieu ban hang cho thu nay. Su dung du lieu tong hop.")

# Kiểm tra tồn kho để điều chỉnh (sử dụng đúng tên cột: Ngày stock old)
print("\n[TON KHO HIEN TAI (Top san pham ban chay)]")
print("-" * 50)
try:
    cursor.execute("""
        SELECT 
            sp.[Code cám],
            sp.[Tên cám], 
            SUM(so.[Số lượng]) as ton_kho_kg
        FROM StockOld so
        LEFT JOIN SanPham sp ON so.[ID sản phẩm] = sp.ID
        WHERE so.[Ngày stock old] = (SELECT MAX([Ngày stock old]) FROM StockOld)
        GROUP BY sp.[Code cám]
        ORDER BY ton_kho_kg DESC
        LIMIT 15
    """)
    stock = cursor.fetchall()
    if stock:
        print(f"{'Code':<8} {'Ten san pham':<30} {'Ton kho (kg)':>15}")
        print("-" * 55)
        for row in stock:
            code = row[0] if row[0] else "N/A"
            name = (row[1][:27] + "...") if row[1] and len(row[1]) > 30 else (row[1] or "N/A")
            qty = f"{row[2]:,.0f}" if row[2] else "0"
            print(f"{code:<8} {name:<30} {qty:>15}")
    else:
        print("Chua co du lieu ton kho")
except Exception as e:
    print(f"Loi truy van ton kho: {e}")

# Tính toán kế hoạch cuối cùng
print("\n" + "=" * 70)
print("DE XUAT KE HOACH SAN XUAT CHI TIET")
print("=" * 70)

cursor.execute("""
    SELECT 
        s.[ID sản phẩm],
        sp.[Code cám],
        sp.[Tên cám],
        ROUND(AVG(s.[Số lượng]), 0) as avg_daily,
        sp.[Batch size],
        COALESCE(
            (SELECT SUM(so.[Số lượng]) 
             FROM StockOld so 
             WHERE so.[ID sản phẩm] = s.[ID sản phẩm] 
               AND so.[Ngày stock old] = (SELECT MAX([Ngày stock old]) FROM StockOld)),
            0
        ) as current_stock
    FROM Sale s
    LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
    WHERE s.[Ngày sale] >= '2026-01-02'
    GROUP BY s.[ID sản phẩm]
    ORDER BY avg_daily DESC
    LIMIT 20
""")
final_plan = cursor.fetchall()

print(f"{'STT':<4} {'Code':<8} {'Ten san pham':<25} {'TB/ngay':>10} {'Ton kho':>10} {'Nen SX':>10}")
print("-" * 75)
for i, row in enumerate(final_plan, 1):
    code = row[1] if row[1] else "N/A"
    name = (row[2][:22] + "...") if row[2] and len(row[2]) > 25 else (row[2] or "N/A")
    avg = row[3] if row[3] else 0
    stock = row[5] if row[5] else 0
    batch = row[4] if row[4] else 1
    
    # Nếu tồn kho < trung bình bán thì cần sản xuất
    if stock < avg:
        need = avg - stock
        # Làm tròn lên batch size
        if batch > 0:
            suggested = int((need // batch + 1) * batch) if need > 0 else 0
        else:
            suggested = int(need)
    else:
        suggested = 0
    
    stock_str = f"{stock:,.0f}" if stock else "0"
    print(f"{i:<4} {code:<8} {name:<25} {avg:>10,.0f} {stock_str:>10} {suggested:>10,}")

conn.close()
print("\n" + "=" * 70)
print("KET THUC PHAN TICH")
print("=" * 70)
