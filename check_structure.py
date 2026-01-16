import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

print("=" * 60)
print("CẤU TRÚC BẢNG tbsys_ChucNangTheoVaiTro")
print("=" * 60)

cursor.execute('PRAGMA table_info(tbsys_ChucNangTheoVaiTro)')
for row in cursor.fetchall():
    col_id, name, data_type, not_null, default_val, pk = row
    print(f"{name:25} {data_type:15} Default: {default_val if default_val else 'None'}")

print("\n" + "=" * 60)
print("DỮ LIỆU MẪU TRONG tbsys_ChucNangTheoVaiTro")
print("=" * 60)

cursor.execute('SELECT * FROM tbsys_ChucNangTheoVaiTro LIMIT 3')
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print("(Chưa có dữ liệu)")

conn.close()
