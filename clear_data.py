# Script xoa du lieu FFSTOCK va BATCHING
import sqlite3

conn = sqlite3.connect('database_new.db')
c = conn.cursor()

# Xoa mem StockOld
c.execute("UPDATE StockOld SET [Đã xóa]=1 WHERE [Đã xóa]=0")
print(f"Deleted StockOld: {c.rowcount}")

# Xoa mem Mixer  
c.execute("UPDATE Mixer SET [Đã xóa]=1 WHERE [Đã xóa]=0")
print(f"Deleted Mixer: {c.rowcount}")

# Xoa log import
c.execute("DELETE FROM EmailImportLog WHERE LoaiFile IN ('FFSTOCK', 'PRODUCTION')")
print(f"Deleted logs: {c.rowcount}")

conn.commit()
conn.close()
print("Done! Ban co the import lai tu trang Nhan email.")
