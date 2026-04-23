# Fix 551X26 Vat nuoi
import sqlite3
conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()
cursor.execute("UPDATE SanPham SET [Vật nuôi] = 'H' WHERE [Tên cám] = '551X26' AND ([Vật nuôi] IS NULL OR [Vật nuôi] = '')")
print('Updated:', cursor.rowcount)
conn.commit()
conn.close()
