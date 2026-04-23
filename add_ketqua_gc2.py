import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check if column exists
cursor.execute('PRAGMA table_info(StockHomNay)')
columns = [col[1] for col in cursor.fetchall()]
print("Columns count:", len(columns))

# Add numeric column for sorting
if 'Ket qua GC2' not in columns:
    print("Adding column Ket qua GC2...")
    cursor.execute("ALTER TABLE StockHomNay ADD COLUMN [Kết quả GC2] REAL")
    conn.commit()
    print("Column added!")
else:
    print("Column already exists")

conn.close()
print("Done!")
