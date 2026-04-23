"""
Database Abstraction Layer - Hỗ trợ cả SQLite và PostgreSQL (Neontech).
Khi có biến môi trường DATABASE_URL → dùng PostgreSQL.
Khi không có → dùng SQLite như cũ.
"""

import os
import sqlite3
import json

# Đường dẫn config
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

# Load config nếu có (local dev). Trên Render sẽ không có file này.
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
else:
    data = {}

# Lấy đường dẫn database SQLite (chỉ cần khi chạy local)
database_path = data.get('database_path', 'database_new.db')
if not os.path.isabs(database_path):
    database_path = os.path.join(script_dir, database_path)

# Kiểm tra loại database
DATABASE_URL = os.environ.get('DATABASE_URL', '')
IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras
    import re


def connect_db():
    """
    Kết nối database. Tự động chọn SQLite hoặc PostgreSQL.
    Trả về connection wrapper tự động adapt SQL cho PostgreSQL.
    """
    if IS_POSTGRES:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return AdaptedConnection(conn)
        except Exception as e:
            raise ConnectionError(f"Không thể kết nối PostgreSQL: {e}")
    else:
        try:
            conn = sqlite3.connect(database_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            raise ConnectionError(f"Không thể kết nối SQLite tại {database_path}: {e}")


def adapt_placeholder(sql):
    """Chuyển đổi placeholder từ SQLite (?) sang PostgreSQL (%s)."""
    if not IS_POSTGRES:
        return sql
    return sql.replace('?', '%s')


class AdaptedCursor:
    """Cursor wrapper tự động adapt SQL cho PostgreSQL."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        adapted = adapt_sql(sql)
        if IS_POSTGRES:
            adapted = adapt_placeholder(adapted)
        if params:
            return self._cursor.execute(adapted, params)
        return self._cursor.execute(adapted)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class AdaptedConnection:
    """Connection wrapper trả về AdaptedCursor thay vì cursor gốc."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, **kwargs):
        return AdaptedCursor(self._conn.cursor(**kwargs))

    def execute(self, sql, params=None):
        """For pd.read_sql_query() compatibility."""
        adapted = adapt_sql(sql)
        if IS_POSTGRES:
            adapted = adapt_placeholder(adapted)
        cursor = self._conn.cursor()
        if params:
            return cursor.execute(adapted, params)
        return cursor.execute(adapted)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def get_cursor(conn):
    """Tạo cursor phù hợp cho từng loại database."""
    if IS_POSTGRES:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        return conn.cursor()


def get_cursor_tuple(conn):
    """Tạo cursor trả về tuple (không phải dict) - dùng cho PRAGMA/metadata."""
    if IS_POSTGRES:
        return conn.cursor()
    else:
        return conn.cursor()


def adapt_sql(sql):
    """
    Chuyển đổi SQL từ SQLite syntax sang PostgreSQL syntax.
    """
    if not IS_POSTGRES:
        return sql
    
    # Thay [column] → "column"
    result = re.sub(r'\[([^\]]+)\]', r'"\1"', sql)
    
    # Thay AUTOINCREMENT → (PostgreSQL dùng SERIAL)
    result = result.replace('AUTOINCREMENT', '')
    result = result.replace('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY')
    
    # Thay GLOB → ~ (regex match)
    result = re.sub(r"(\S+)\s+GLOB\s+'([^']+)'", r"\1 ~ '\2'", result)
    
    # Thay IFNULL → COALESCE
    result = result.replace('IFNULL(', 'COALESCE(')
    result = result.replace('ifnull(', 'COALESCE(')
    
    # Thay strftime('%d', col) → EXTRACT(DAY FROM col) cho PostgreSQL
    result = re.sub(
        r"CAST\(strftime\('%d',\s*(.+?)\)\s*AS\s+INTEGER\)",
        r"CAST(EXTRACT(DAY FROM \1) AS INTEGER)",
        result
    )
    result = re.sub(
        r"strftime\('([^']+)',\s*(.+?)\)",
        lambda m: _convert_strftime(m.group(1), m.group(2)),
        result
    )
    
    # Thay || (string concat) - giữ nguyên vì PostgreSQL cũng dùng ||
    
    # Thay DATETIME DEFAULT CURRENT_TIMESTAMP → TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    result = result.replace('DATETIME DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    # Thay kiểu dữ liệu
    result = result.replace(' DATETIME', ' TIMESTAMP')
    result = result.replace(' BOOLEAN', ' INTEGER')
    result = result.replace(' REAL', ' DOUBLE PRECISION')
    result = result.replace(' NUMERIC', ' NUMERIC')
    
    # Auto-quote unquoted table names cho PostgreSQL (case-sensitive)
    # Danh sách tất cả bảng trong app
    known_tables = [
        'DonViTinh', 'SanPham', 'DatHang', 'StockHomNay', 'StockOld',
        'Packing', 'PackingPlan', 'Sale', 'Plan', 'Pellet', 'PelletPlan',
        'PelletCapacity', 'PelletReportStatus', 'BaoBi', 'BagStock',
        'Forecast', 'Mixer', 'TonBon', 'Testcan', 'TestCan_Reports',
        'EmailImportLog', 'MasterdataLoss',
        'tbsys_Users', 'tbsys_VaiTro', 'tbsys_ChucNangChinh',
        'tbsys_DanhSachChucNang', 'tbsys_ChucNangTheoVaiTro',
        'tbsys_config', 'tbsys_ModuleChucNang',
        'tbsys_LichSuBackupDatabase', 'tbsys_Logs', 'sysdiagrams'
    ]
    
    for table in known_tables:
        # Quote unquoted table names after FROM, JOIN, INTO, UPDATE, TABLE keywords
        # Only if not already quoted with " or [
        result = re.sub(
            r'(\bFROM\s+)' + re.escape(table) + r'(\b)',
            r'\1"' + table + r'"\2',
            result
        )
        result = re.sub(
            r'(\bJOIN\s+)' + re.escape(table) + r'(\b)',
            r'\1"' + table + r'"\2',
            result
        )
        result = re.sub(
            r'(\bINTO\s+)' + re.escape(table) + r'(\b)',
            r'\1"' + table + r'"\2',
            result
        )
        result = re.sub(
            r'(\bUPDATE\s+)' + re.escape(table) + r'(\b)',
            r'\1"' + table + r'"\2',
            result
        )
    
    # Thay TRIM([col]) - PostgreSQL cũng hỗ trợ TRIM
    
    # Auto-quote alias.BareColumn patterns (e.g. CNC.ID → CNC."ID")
    # Matches: alias.MixedCaseWord where word has at least one uppercase letter
    result = re.sub(
        r'(\b[a-zA-Z_]\w*\.)([A-Z][a-zA-Z0-9_]*)(?=[^"\w]|$)',
        lambda m: m.group(1) + '"' + m.group(2) + '"' if '"' + m.group(2) + '"' not in m.group(0) else m.group(0),
        result
    )
    
    # Auto-quote single-quoted aliases: as 'Name' → as "Name"
    result = re.sub(r"\bas\s+'([^']+)'", r'as "\1"', result)
    
    return result


def _convert_strftime(fmt, col):
    """Chuyển đổi strftime SQLite sang PostgreSQL EXTRACT/TO_CHAR."""
    if fmt == '%d':
        return f"EXTRACT(DAY FROM {col})"
    elif fmt == '%m':
        return f"EXTRACT(MONTH FROM {col})"
    elif fmt == '%Y':
        return f"EXTRACT(YEAR FROM {col})"
    elif fmt == '%H':
        return f"EXTRACT(HOUR FROM {col})"
    elif fmt == '%M':
        return f"EXTRACT(MINUTE FROM {col})"
    elif fmt == '%Y-%m-%d':
        return f"TO_CHAR({col}, 'YYYY-MM-DD')"
    elif fmt == '%Y-%m-%d %H:%M:%S':
        return f"TO_CHAR({col}, 'YYYY-MM-DD HH24:MI:SS')"
    else:
        return f"TO_CHAR({col}, '{fmt}')"


def adapt_placeholder(sql):
    """
    Chuyển ? thành %s cho PostgreSQL.
    """
    if IS_POSTGRES:
        return sql.replace('?', '%s')
    return sql


def get_table_list_sql(include_system=False):
    """SQL để lấy danh sách bảng."""
    if IS_POSTGRES:
        if include_system:
            return "SELECT table_name AS name FROM information_schema.tables WHERE table_schema = 'public' AND table_name NOT LIKE 'pg_%'"
        else:
            return "SELECT table_name AS name FROM information_schema.tables WHERE table_schema = 'public' AND table_name NOT LIKE 'tbsys_%' AND table_name NOT LIKE 'pg_%'"
    else:
        if include_system:
            return "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        else:
            return "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'tbsys_%' AND name NOT LIKE 'sqlite_%'"


def get_table_info(cursor, table_name):
    """
    Lấy thông tin cột của bảng.
    Trả về list of tuples: (cid, name, type, notnull, default_value, pk)
    """
    if IS_POSTGRES:
        cursor.execute("""
            SELECT 
                ordinal_position AS cid,
                column_name AS name,
                UPPER(data_type) AS type,
                CASE WHEN is_nullable = 'NO' THEN 1 ELSE 0 END AS notnull,
                column_default AS dflt_value,
                CASE WHEN column_name IN (
                    SELECT kcu.column_name 
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
                ) THEN 1 ELSE 0 END AS pk
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name, table_name))
        rows = cursor.fetchall()
        # Normalize PostgreSQL types to SQLite-like types
        result = []
        for row in rows:
            pg_type = row[2] if isinstance(row, tuple) else row['type']
            name = row[1] if isinstance(row, tuple) else row['name']
            notnull = row[3] if isinstance(row, tuple) else row['notnull']
            dflt = row[4] if isinstance(row, tuple) else row['dflt_value']
            pk = row[5] if isinstance(row, tuple) else row['pk']
            cid = row[0] if isinstance(row, tuple) else row['cid']
            
            # Map PostgreSQL types to simple types
            sqlite_type = _pg_type_to_sqlite(pg_type)
            result.append((cid, name, sqlite_type, notnull, dflt, pk))
        return result
    else:
        cursor.execute(f"PRAGMA table_info([{table_name}])")
        return cursor.fetchall()


def _pg_type_to_sqlite(pg_type):
    """Map PostgreSQL type names to SQLite-like type names."""
    pg_type = str(pg_type).upper()
    if 'CHARACTER VARYING' in pg_type or 'VARCHAR' in pg_type or 'TEXT' in pg_type:
        return 'TEXT'
    elif 'INTEGER' in pg_type or 'BIGINT' in pg_type or 'SMALLINT' in pg_type:
        return 'INTEGER'
    elif 'DOUBLE' in pg_type or 'FLOAT' in pg_type or 'REAL' in pg_type:
        return 'REAL'
    elif 'NUMERIC' in pg_type or 'DECIMAL' in pg_type:
        return 'NUMERIC'
    elif 'TIMESTAMP' in pg_type or 'DATE' in pg_type:
        return 'DATETIME'
    elif 'BOOLEAN' in pg_type:
        return 'INTEGER'
    elif 'BYTEA' in pg_type:
        return 'BLOB'
    else:
        return 'TEXT'


def quote_identifier(name):
    """Quote tên cột/bảng cho phù hợp với database."""
    if IS_POSTGRES:
        return f'"{name}"'
    else:
        return f'[{name}]'


def quote_table(name):
    """Quote tên bảng."""
    return quote_identifier(name)


def fetchall_as_dicts(cursor, rows):
    """Chuyển kết quả query thành list of dicts."""
    if IS_POSTGRES:
        # RealDictCursor đã trả về dict
        return [dict(row) for row in rows]
    else:
        # sqlite3.Row
        return [dict(row) for row in rows]


def get_last_insert_id_sql(table_name, id_column='ID'):
    """SQL để lấy ID vừa insert."""
    if IS_POSTGRES:
        return f' RETURNING "{id_column}"'
    else:
        return ''  # SQLite dùng cursor.lastrowid


def get_index_list(cursor, table_name):
    """Lấy danh sách index của bảng."""
    if IS_POSTGRES:
        cursor.execute("""
            SELECT indexname AS name
            FROM pg_indexes
            WHERE tablename = %s AND schemaname = 'public'
        """, (table_name,))
        return cursor.fetchall()
    else:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (table_name,))
        return cursor.fetchall()


def create_table_if_not_exists(sql):
    """Adapt CREATE TABLE syntax."""
    if IS_POSTGRES:
        return adapt_sql(sql)
    return sql
