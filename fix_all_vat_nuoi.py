# Check and fix all Vat nuoi issues
import sqlite3
conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Get all products with null Vat nuoi
cursor.execute("SELECT [Code cám], [Tên cám] FROM SanPham WHERE ([Vật nuôi] IS NULL OR [Vật nuôi] = '') AND [Đã xóa] = 0")
null_products = cursor.fetchall()
print(f"Products with NULL Vat nuoi: {len(null_products)}")

# Read CSV and update
import pandas as pd
df = pd.read_csv('EXCEL/12334.csv')
df_unique = df[['Tên cám', 'Vật nuôi']].drop_duplicates()

# Create mapping
vat_nuoi_map = {row['Tên cám']: row['Vật nuôi'] for _, row in df_unique.iterrows()}

# Update null products
updated = 0
for code_cam, ten_cam in null_products:
    vat_nuoi = vat_nuoi_map.get(ten_cam) or vat_nuoi_map.get(code_cam)
    if vat_nuoi:
        cursor.execute("UPDATE SanPham SET [Vật nuôi] = ? WHERE [Tên cám] = ? OR [Code cám] = ?", 
                       (vat_nuoi, ten_cam, code_cam))
        updated += cursor.rowcount

conn.commit()
print(f"Updated: {updated}")

# Verify 551X26
cursor.execute("SELECT [Tên cám], [Vật nuôi] FROM SanPham WHERE [Tên cám] = '551X26'")
for r in cursor.fetchall():
    print(f"  551X26: {r[1]}")

conn.close()
