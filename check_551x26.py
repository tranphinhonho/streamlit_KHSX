# Check 551X26 in SanPham
import sqlite3
conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check SanPham
cursor.execute("SELECT [Code cám], [Tên cám], [Vật nuôi] FROM SanPham WHERE [Code cám] LIKE '%551X26%' OR [Tên cám] LIKE '%551X26%'")
rows = cursor.fetchall()
print(f"Found in SanPham: {len(rows)}")
for r in rows:
    print(f"  Code: {r[0]}, Ten: {r[1]}, Vat nuoi: {r[2]}")

# Check all columns in SanPham for 551X26
cursor.execute("SELECT * FROM SanPham WHERE [Tên cám] = '551X26' OR [Code cám] = '551X26'")
rows = cursor.fetchall()
print(f"\nFull record: {len(rows)}")

cursor.execute("PRAGMA table_info(SanPham)")
cols = [r[1] for r in cursor.fetchall()]
print(f"Columns: {cols}")

conn.close()
