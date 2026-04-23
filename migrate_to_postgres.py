"""
Script di chuyển dữ liệu từ SQLite sang PostgreSQL (Neontech).
Chạy 1 lần để migrate toàn bộ dữ liệu.

Usage:
    set DATABASE_URL=postgresql://...
    python migrate_to_postgres.py
"""

import sqlite3
import psycopg2
import os
import sys

# Cấu hình
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'database_new.db')
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if not DATABASE_URL:
    print("❌ Thiếu biến môi trường DATABASE_URL!")
    print("   Chạy: set DATABASE_URL=postgresql://...")
    sys.exit(1)

if not os.path.exists(SQLITE_PATH):
    print(f"❌ File SQLite không tồn tại: {SQLITE_PATH}")
    sys.exit(1)


def get_sqlite_tables(sqlite_conn):
    """Lấy danh sách tất cả bảng từ SQLite."""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]


def get_sqlite_table_info(sqlite_conn, table_name):
    """Lấy thông tin cột của bảng SQLite."""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    return cursor.fetchall()


def sqlite_to_pg_type(sqlite_type):
    """Chuyển đổi kiểu dữ liệu SQLite sang PostgreSQL."""
    t = sqlite_type.upper()
    if t in ('TEXT', 'NVARCHAR', 'VARCHAR', 'NCHAR', 'CHAR', 'NTEXT'):
        return 'TEXT'
    elif t in ('INTEGER', 'INT', 'BIGINT', 'SMALLINT', 'BIT'):
        return 'INTEGER'
    elif t in ('REAL', 'FLOAT', 'DOUBLE'):
        return 'DOUBLE PRECISION'
    elif t in ('NUMERIC', 'DECIMAL', 'MONEY'):
        return 'NUMERIC'
    elif t in ('DATETIME', 'DATE', 'TIMESTAMP'):
        return 'TIMESTAMP'
    elif t in ('BLOB', 'IMAGE', 'VARBINARY'):
        return 'BYTEA'
    elif t == 'BOOLEAN':
        return 'INTEGER'  # SQLite stores boolean as 0/1 integer
    else:
        return 'TEXT'


def create_pg_table(pg_conn, table_name, columns_info):
    """Tạo bảng PostgreSQL từ thông tin cột SQLite."""
    cursor = pg_conn.cursor()
    
    col_defs = []
    for col in columns_info:
        cid, name, col_type, notnull, default_val, is_pk = col
        pg_type = sqlite_to_pg_type(col_type)
        
        # Xử lý Primary Key + AUTOINCREMENT
        if is_pk and pg_type == 'INTEGER':
            col_defs.append(f'"{name}" SERIAL PRIMARY KEY')
            continue
        
        parts = [f'"{name}"', pg_type]
        
        if notnull:
            parts.append('NOT NULL')
        
        if default_val is not None:
            default_str = str(default_val)
            if default_str == 'CURRENT_TIMESTAMP':
                parts.append('DEFAULT CURRENT_TIMESTAMP')
            elif default_str.strip("'") == default_str and default_str.isdigit():
                parts.append(f'DEFAULT {default_str}')
            else:
                parts.append(f"DEFAULT {default_str}")
        
        col_defs.append(' '.join(parts))
    
    create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n  ' + ',\n  '.join(col_defs) + '\n)'
    
    try:
        cursor.execute(create_sql)
        pg_conn.commit()
        return True
    except Exception as e:
        pg_conn.rollback()
        print(f"  ⚠ Lỗi tạo bảng {table_name}: {e}")
        return False


def migrate_data(sqlite_conn, pg_conn, table_name, columns_info):
    """Di chuyển dữ liệu từ SQLite sang PostgreSQL."""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    col_names = [col[1] for col in columns_info]
    
    # Lấy dữ liệu từ SQLite
    sqlite_cursor.execute(f'SELECT * FROM [{table_name}]')
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  📭 Bảng {table_name}: không có dữ liệu")
        return 0
    
    # Insert vào PostgreSQL
    quoted_cols = ', '.join([f'"{c}"' for c in col_names])
    placeholders = ', '.join(['%s'] * len(col_names))
    insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})'
    
    count = 0
    for row in rows:
        try:
            # Chuyển đổi giá trị
            values = []
            for i, val in enumerate(row):
                if val is None:
                    values.append(None)
                else:
                    values.append(val)
            pg_cursor.execute(insert_sql, values)
            count += 1
        except Exception as e:
            pg_conn.rollback()
            # Only print first 3 errors per table
            if count < 3:
                print(f"  ⚠ Lỗi insert dòng {count + 1} vào {table_name}: {e}")
            pg_conn.commit()  # Reset transaction
    
    pg_conn.commit()
    
    # Reset sequence cho cột SERIAL
    for col in columns_info:
        if col[5]:  # is_pk
            try:
                pg_cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence('"{table_name}"', '{col[1]}'), 
                           COALESCE((SELECT MAX("{col[1]}") FROM "{table_name}"), 0) + 1, false)
                """)
                pg_conn.commit()
            except:
                pg_conn.rollback()
    
    return count


def main():
    print("=" * 60)
    print("MIGRATE DỮ LIỆU TỪ SQLite SANG PostgreSQL (Neontech)")
    print("=" * 60)
    print(f"\n📂 SQLite: {SQLITE_PATH}")
    print(f"🐘 PostgreSQL: {DATABASE_URL[:50]}...")
    
    # Kết nối SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    print("\n✅ Đã kết nối SQLite")
    
    # Kết nối PostgreSQL
    try:
        pg_conn = psycopg2.connect(DATABASE_URL)
        print("✅ Đã kết nối PostgreSQL")
    except Exception as e:
        print(f"❌ Không thể kết nối PostgreSQL: {e}")
        sys.exit(1)
    
    # Lấy danh sách bảng
    tables = get_sqlite_tables(sqlite_conn)
    print(f"\n📋 Tìm thấy {len(tables)} bảng:")
    for t in tables:
        print(f"   - {t}")
    
    print("\n" + "-" * 60)
    print("BẮT ĐẦU MIGRATION")
    print("-" * 60)
    
    success = 0
    failed = 0
    
    for i, table_name in enumerate(tables, 1):
        print(f"\n[{i}/{len(tables)}] Đang xử lý bảng: {table_name}")
        
        # Lấy thông tin cột
        columns_info = get_sqlite_table_info(sqlite_conn, table_name)
        
        if not columns_info:
            print(f"  ⚠ Không có thông tin cột cho bảng {table_name}")
            failed += 1
            continue
        
        # Xóa bảng cũ nếu có (để tạo lại)
        pg_cursor = pg_conn.cursor()
        try:
            pg_cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            pg_conn.commit()
        except:
            pg_conn.rollback()
        
        # Tạo bảng
        if not create_pg_table(pg_conn, table_name, columns_info):
            failed += 1
            continue
        print(f"  ✅ Đã tạo bảng")
        
        # Migrate dữ liệu
        count = migrate_data(sqlite_conn, pg_conn, table_name, columns_info)
        print(f"  ✅ Đã migrate {count} dòng")
        success += 1
    
    # Đóng kết nối
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print("HOÀN TẤT MIGRATION")
    print("=" * 60)
    print(f"  ✅ Thành công: {success}/{len(tables)} bảng")
    if failed:
        print(f"  ❌ Thất bại: {failed}/{len(tables)} bảng")
    print("=" * 60)


if __name__ == '__main__':
    main()
