# Script an Lich thang
import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

c.execute("UPDATE tbsys_DanhSachChucNang SET [Đã xóa] = 1 WHERE [Chức năng con] = 'Lịch tháng'")
print(f'Updated {c.rowcount} row(s)')

conn.commit()
conn.close()
print("Done!")
