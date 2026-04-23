import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(PelletCapacity)")
columns = [row[1] for row in cursor.fetchall()]

if 'Thông số khuôn' not in columns:
    cursor.execute('ALTER TABLE PelletCapacity ADD COLUMN [Thông số khuôn] TEXT')
    conn.commit()
    print('✅ Đã thêm cột [Thông số khuôn] vào table PelletCapacity')
else:
    print('ℹ️ Cột [Thông số khuôn] đã tồn tại')

conn.close()
