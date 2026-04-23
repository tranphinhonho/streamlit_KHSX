# -*- coding: utf-8 -*-
"""Script to add new columns for dual week comparison"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Add new columns for dual week comparison
new_columns = [
    ('[Ghi chú 2 A]', 'TEXT'),
    ('[Kết quả GC2 A]', 'REAL'),
    ('[Ghi chú 2 B]', 'TEXT'),
    ('[Kết quả GC2 B]', 'REAL')
]

for col_name, col_type in new_columns:
    try:
        cursor.execute(f"ALTER TABLE StockHomNay ADD COLUMN {col_name} {col_type}")
        print(f"✅ Added column: {col_name}")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print(f"⚠️ Column already exists: {col_name}")
        else:
            print(f"❌ Error adding {col_name}: {e}")

conn.commit()
conn.close()

print("\n✅ Done!")
