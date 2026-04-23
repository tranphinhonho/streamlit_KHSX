import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Get table info
cursor.execute('PRAGMA table_info(StockHomNay)')
columns = [col[1] for col in cursor.fetchall()]
print("Columns count:", len(columns))

# Check if Ghi chu 2 exists
has_ghi_chu_2 = 'Ghi chú 2' in columns
print("Has Ghi chu 2:", has_ghi_chu_2)

if not has_ghi_chu_2:
    print("Adding column...")
    cursor.execute("ALTER TABLE StockHomNay ADD COLUMN [Ghi chú 2] TEXT")
    conn.commit()
    print("Column added!")
else:
    print("Column already exists")

conn.close()
print("Done!")
