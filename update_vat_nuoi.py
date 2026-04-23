# -*- coding: utf-8 -*-
"""Script cap nhat Vat nuoi vao SanPham"""
import sqlite3
import pandas as pd

csv_path = 'EXCEL/12334.csv'
df = pd.read_csv(csv_path)
print(f"Read {len(df)} rows")

df_unique = df[['Tên cám', 'Vật nuôi']].drop_duplicates()
print(f"Unique pairs: {len(df_unique)}")

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

updated = 0
not_found = []

for _, row in df_unique.iterrows():
    ten_cam = row['Tên cám']
    vat_nuoi = row['Vật nuôi']
    
    cursor.execute("""
        UPDATE SanPham
        SET [Vật nuôi] = ?
        WHERE ([Code cám] = ? OR [Tên cám] = ?) AND [Đã xóa] = 0
    """, (vat_nuoi, ten_cam, ten_cam))
    
    if cursor.rowcount > 0:
        updated += cursor.rowcount
    else:
        not_found.append(ten_cam)

conn.commit()
conn.close()

print(f"Updated: {updated}")
print(f"Not found: {len(not_found)}")
