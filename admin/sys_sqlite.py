import json
import sqlite3
import pandas as pd
import bcrypt
import numpy as np
import admin.sys_functions as fn
import os
from datetime import datetime

# Lấy đường dẫn tuyệt đối đến thư mục chứa script hiện tại
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

with open(config_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Lấy đường dẫn database
database_path = data.get('database_path', 'database.db')
if not os.path.isabs(database_path):
    # Nếu là đường dẫn tương đối, tính từ thư mục admin
    database_path = os.path.join(script_dir, database_path)

def connect_db():
    """
    Kết nối đến SQLite database.
    """
    try:
        conn = sqlite3.connect(database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
        return conn
    except Exception as e:
        error_message = (
            f"Không thể kết nối đến SQLite database tại {database_path}. Lỗi: {e}\n"
            "Vui lòng đảm bảo rằng:\n"
            "1. Đường dẫn database trong file config.json là chính xác.\n"
            "2. Bạn có quyền đọc/ghi vào thư mục chứa database."
        )
        raise ConnectionError(error_message)

def generate_next_code(tablename, column_name, prefix='PT', num_char=5):
    """
    Tạo mã kế tiếp cho một cột trong bảng SQLite.
    Ví dụ: prefix='DH', num_char=5 → DH00001, DH00002, ...
    """
    try:
        # Lấy số lớn nhất hiện tại
        sql = f"""
        SELECT MAX(
            CAST(
                SUBSTR([{column_name}], {len(prefix) + 1}) AS INTEGER
            )
        ) AS max_num
        FROM [{tablename}]
        WHERE [{column_name}] LIKE '{prefix}%' 
        AND LENGTH([{column_name}]) = {len(prefix) + num_char}
        AND [{column_name}] GLOB '{prefix}[0-9]*'
        """
        
        max_num = query_database_sqlite(sql_string=sql, data_type='value')
        
        # Nếu chưa có bản ghi nào, bắt đầu từ 1
        if max_num is None:
            next_num = 1
        else:
            next_num = int(max_num) + 1
        
        # Format số với số ký tự chỉ định (padding với số 0)
        next_code = f"{prefix}{str(next_num).zfill(num_char)}"
        
        return next_code
        
    except Exception as e:
        # Nếu có lỗi, trả về mã đầu tiên
        return f"{prefix}{'1'.zfill(num_char)}"

def generate_create_table_query_sqlite(table_name, df):
    """
    Tạo câu lệnh CREATE TABLE từ DataFrame cho SQLite.
    Hỗ trợ Auto Increment (AUTOINCREMENT) cho bất kỳ cột nào được đánh dấu.
    """
    create_table_query = f"CREATE TABLE IF NOT EXISTS [{table_name}] (\n"
    
    system_columns = ['Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa']
    df_filtered = df[~df['Tên trường'].isin(system_columns)]
    
    has_primary_key = False
    column_definitions = []
    
    for index, row in df_filtered.iterrows():
        if row['Tên trường'] and row['Kiểu dữ liệu']:
            field_name = f"[{row['Tên trường']}]"
            data_type = row['Kiểu dữ liệu']
            
            # Chuyển đổi kiểu dữ liệu SQL Server sang SQLite
            data_type = convert_sqlserver_to_sqlite_type(data_type, row.get("n (Mặc định n=50)"))
            
            # Xử lý Auto Increment
            is_auto_increment = row.get('Auto Increment', False)
            if is_auto_increment:
                # SQLite: INTEGER PRIMARY KEY AUTOINCREMENT
                if 'INT' in data_type.upper():
                    column_definitions.append(f"\t{field_name} INTEGER PRIMARY KEY AUTOINCREMENT")
                    has_primary_key = True
                    continue
            
            # NOT NULL và DEFAULT
            not_null = "NOT NULL" if row.get('Not Null') else ""
            
            default_value = row.get('Mặc định')
            if default_value is None or str(default_value).strip() == "" or str(default_value) == "0":
                default_value = ""
            else:
                if isinstance(default_value, (int, float)):
                    default_value = f"DEFAULT {default_value}"
                else:
                    default_value = f"DEFAULT '{default_value}'"
            
            column_def = f"\t{field_name} {data_type} {not_null} {default_value}".strip()
            column_definitions.append(column_def)
    
    # Thêm các cột hệ thống
    column_definitions.append("\t[Người tạo] TEXT")
    column_definitions.append("\t[Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP")
    column_definitions.append("\t[Người sửa] TEXT")
    column_definitions.append("\t[Thời gian sửa] DATETIME")
    column_definitions.append("\t[Đã xóa] INTEGER DEFAULT 0")
    
    create_table_query += ",\n".join(column_definitions)
    create_table_query += "\n);"
    
    return create_table_query

def convert_sqlserver_to_sqlite_type(data_type, n_value=None):
    """
    Chuyển đổi kiểu dữ liệu từ SQL Server sang SQLite.
    SQLite có 5 kiểu dữ liệu chính: TEXT, NUMERIC, INTEGER, REAL, BLOB
    """
    data_type = str(data_type).upper().strip()
    
    # Nếu đã là kiểu SQLite thuần túy thì giữ nguyên
    if data_type in ['TEXT', 'INTEGER', 'REAL', 'NUMERIC', 'BLOB', 'DATETIME', 'DATE', 'BOOLEAN']:
        return data_type
    
    if "(n)" in data_type.lower():
        if n_value and not pd.isna(n_value):
            n_value = int(n_value)
        else:
            n_value = 50
        data_type = data_type.replace('(N)', f'({n_value})').replace('(n)', f'({n_value})')
    
    # Chuyển đổi các kiểu dữ liệu SQL Server sang SQLite
    if 'NVARCHAR' in data_type or 'VARCHAR' in data_type or 'NCHAR' in data_type or 'CHAR' in data_type or 'NTEXT' in data_type:
        return 'TEXT'
    elif 'INT' in data_type or 'BIT' in data_type:
        return 'INTEGER'
    elif 'FLOAT' in data_type or 'REAL' in data_type or 'DOUBLE' in data_type:
        return 'REAL'
    elif 'DECIMAL' in data_type or 'NUMERIC' in data_type or 'MONEY' in data_type:
        return 'NUMERIC'
    elif 'DATETIME' in data_type or 'DATE' in data_type:
        return 'DATETIME'
    elif 'BLOB' in data_type or 'IMAGE' in data_type or 'VARBINARY' in data_type:
        return 'BLOB'
    elif 'BOOL' in data_type:
        return 'BOOLEAN'
    else:
        return 'TEXT'  # Mặc định

def get_id_by_name_from_df(df, table_name='MonHoc', columns_get=['Tên môn học', 'Mã môn học'],
                           columns_rename={'Tên môn học': 'Phụ trách'}, columns_on=['Phụ trách'], how='left'):
    df_monhoc = get_columns_data(table_name=table_name, columns=columns_get)
    df_monhoc = df_monhoc.rename(columns=columns_rename)
    df = pd.merge(df, df_monhoc, how=how, on=columns_on)
    return df

def get_id_by_name(tablename, column_name, value_name, col_id='ID'):
    """Lấy ID từ tên"""
    sql = f"SELECT [{col_id}] FROM [{tablename}] WHERE [Đã xóa]=0 AND [{column_name}]=? LIMIT 1"
    return query_database_sqlite(sql_string=sql, data_type='value', params=(value_name,))

def query_database_sqlite(sql_string, data_type=None, delimiter=' | ', params=None):
    """
    Thực thi truy vấn SQLite.
    data_type: 'dataframe', 'list', 'value', hoặc None (cho INSERT/UPDATE/DELETE)
    """
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        if params:
            cursor.execute(sql_string, params)
        else:
            cursor.execute(sql_string)
        
        if data_type is not None:
            # Lấy kết quả truy vấn
            columns = [description[0] for description in cursor.description] if cursor.description else []

            if data_type == 'dataframe':
                rows = cursor.fetchall()
                df = pd.DataFrame([dict(row) for row in rows])
                return df
            elif data_type == 'list':
                rows = cursor.fetchall()
                result = [delimiter.join(str(row[col]) for col in columns) for row in rows]
                return result
            elif data_type == 'value':
                result = cursor.fetchone()
                if result is not None:
                    result = result[0]
                return result
        else:
            # Thực thi lệnh truy vấn (INSERT, UPDATE, DELETE)
            conn.commit()
            return "Đã xử lý thành công!"
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_tables():
    """Lấy danh sách tất cả các bảng (không bao gồm bảng hệ thống)"""
    sql_string = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'tbsys_%' AND name NOT LIKE 'sqlite_%'"
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(sql_string)
    rows = cursor.fetchall()
    conn.close()
    
    tables = [row[0] for row in rows]
    return tables

def get_all_tables_admin():
    """Lấy danh sách tất cả các bảng (bao gồm cả bảng hệ thống)"""
    sql_string = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(sql_string)
    rows = cursor.fetchall()
    conn.close()
    
    tables = [row[0] for row in rows]
    return tables

def delete_tables(table_list):
    """Xóa danh sách các bảng"""
    conn = connect_db()
    cursor = conn.cursor()
    results = []
    
    for table in table_list:
        try:
            drop_query = f"DROP TABLE IF EXISTS [{table}];"
            cursor.execute(drop_query)
            results.append(f"Đã xóa bảng {table}")
        except Exception as e:
            results.append(f"Lỗi khi xóa bảng {table}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return results

def get_columns_data(table_name, columns=None, delimiter=" | ", data_type="dataframe",
                     col_where=None, type="", col_order=None, group_by=None, date_columns=None,
                     joins=None, distinct=False, custom_columns=None, output_columns=None,
                     page_number=None, rows_per_page=None, search_value=None, search_columns=None):
    """
    Lấy dữ liệu từ bảng SQLite với nhiều tùy chọn lọc và sắp xếp.
    """
    conn = connect_db()
    cursor = conn.cursor()

    # Xử lý mặc định
    if col_order is None:
        col_order = {}
    if group_by is None:
        group_by = []
    if custom_columns is None:
        custom_columns = []

    # Lấy danh sách kiểu dữ liệu của các cột
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    column_info = cursor.fetchall()
    column_types = {row[1]: row[2].lower() for row in column_info}

    # Helper function for quoting values
    def _quote_sql_value(value, sql_type):
        if value is None:
            return "NULL"
        # Numeric types
        if sql_type in ['integer', 'real', 'numeric']:
            return str(value)
        # Text types need escaped quotes
        safe_value = str(value).replace("'", "''")
        return f"'{safe_value}'"

    # Xây dựng danh sách cột
    working_columns = list(columns) if columns is not None else []
    selected_columns = []
    
    if not working_columns:
        all_table_columns = get_table_columns(table_name)
        if not all_table_columns:
            selected_columns.append(f"[{table_name}].*")
        else:
            # Thêm alias cho từng cột để tránh ambiguous khi JOIN
            selected_columns += [f"[{table_name}].[{column}] AS [{column}]" for column in all_table_columns]
    else:
        # Thêm alias cho từng cột để tránh ambiguous khi JOIN
        selected_columns += [f"[{table_name}].[{column}] AS [{column}]" for column in working_columns]

    # Thêm cột custom
    for custom_column in custom_columns:
        column_name = custom_column.get("name")
        expression = custom_column.get("expression")
        if not column_name or not expression:
            raise ValueError("Each custom column must have a 'name' and an 'expression'.")
        selected_columns.append(f"({expression}) AS [{column_name}]")

    # Xử lý JOIN
    join_statements = []
    if joins:
        for join in joins:
            from_table = join.get("from_table", table_name)
            join_table = join.get("table")
            join_alias = join.get("alias", join_table)
            join_on = join.get("on")
            join_columns = join.get("columns", [])

            selected_columns += [f"[{join_alias}].[{col}] AS [{join_alias}_{col}]" for col in join_columns]

            on_conditions = " AND ".join(
                f"[{from_table}].[{key}] = [{join_alias}].[{value}]" for key, value in join_on.items()
            )

            join_where = join.get("join_where")
            if join_where and isinstance(join_where, dict):
                for col, cond in join_where.items():
                    if isinstance(cond, tuple) and len(cond) == 2:
                        operator, value = cond
                        column_type = column_types.get(col, "text")
                        value_str = _quote_sql_value(value, column_type)
                        on_conditions += f" AND [{from_table}].[{col}] {operator} {value_str}"
            
            join_statement = f"LEFT JOIN [{join_table}] AS [{join_alias}] ON {on_conditions}"
            join_statements.append(join_statement)

    # Thêm DISTINCT
    distinct_clause = "DISTINCT" if distinct else ""

    # Xây dựng câu truy vấn
    query = f"SELECT {distinct_clause} {', '.join(selected_columns)} FROM [{table_name}]"

    if join_statements:
        query += " " + " ".join(join_statements)

    # WHERE Clause
    where_clauses = []
    if col_where:
        for column, condition in col_where.items():
            if '.' in column:
                parts = column.rsplit('.', 1)
                table_prefix = parts[0]
                column_name = parts[1]
            else:
                table_prefix = table_name
                column_name = column
            
            column_name = column_name.strip('[]')
            column_type = column_types.get(column_name, "text")

            if isinstance(condition, dict) and 'Between' in condition:
                between_values = condition['Between']
                if len(between_values) == 2:
                    start_val, end_val = between_values
                    start_str = _quote_sql_value(start_val, column_type)
                    end_str = _quote_sql_value(end_val, column_type)
                    where_clauses.append(f"[{table_prefix}].[{column_name}] BETWEEN {start_str} AND {end_str}")

            elif isinstance(condition, list) or (isinstance(condition, tuple) and condition[0] in ["IN", "NOT IN"]):
                operator, values = ("IN", condition) if isinstance(condition, list) else condition
                if values:
                    condition_str = ", ".join(_quote_sql_value(v, column_type) for v in values)
                    where_clauses.append(f"[{table_prefix}].[{column_name}] {operator} ({condition_str})")

            elif isinstance(condition, tuple) and len(condition) == 2:
                operator, value = condition
                value_str = _quote_sql_value(value, column_type)
                where_clauses.append(f"[{table_prefix}].[{column_name}] {operator} {value_str}")
            elif isinstance(condition, str) and condition.strip().upper() in ['IS NULL', 'IS NOT NULL']:
                where_clauses.append(f"[{table_prefix}].[{column_name}] {condition}")
            else:
                value_str = _quote_sql_value(condition, column_type)
                where_clauses.append(f"[{table_prefix}].[{column_name}] = {value_str}")

    # Search Clause
    if search_value and search_columns:
        search_conditions = []
        safe_search_value = str(search_value).replace("'", "''")
        for col in search_columns:
            table_prefix = col.split('.')[0] if '.' in col else table_name
            col_name_only = col.split('.')[-1]
            
            search_conditions.append(f"CAST([{table_prefix}].[{col_name_only}] AS TEXT) LIKE '%{safe_search_value}%'")
        
        if search_conditions:
            where_clauses.append(f"({ ' OR '.join(search_conditions) })")

    # Final Query Assembly
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    # GROUP BY
    if len(group_by):
        group_statements = [f"[{col}]" for col in group_by]
        query += " GROUP BY " + ", ".join(group_statements)

    # ORDER BY
    if len(col_order):
        order_statements = []
        for col, order in col_order.items():
            order_statements.append(f"[{col}] {order}")
        query += " ORDER BY " + ", ".join(order_statements)

    # Phân trang
    if page_number is not None and rows_per_page is not None:
        offset = (page_number - 1) * rows_per_page
        query += f" LIMIT {rows_per_page} OFFSET {offset}"

    # Fetch data
    cursor.execute(query)
    rows = cursor.fetchall()
    columns_from_db = [description[0] for description in cursor.description]
    df = pd.DataFrame([dict(row) for row in rows], columns=columns_from_db)

    # Apply Join Replace Logic
    if joins:
        df_processed = df.copy()
        columns_to_drop = []

        for join in joins:
            join_table = join.get("table")
            join_alias = join.get("alias", join_table)

            def get_aliased_col_name(original_name):
                return f"{join_alias}_{original_name}"

            replace_actions = []
            if 'replace' in join and isinstance(join['replace'], dict):
                for original_col, new_col_base in join['replace'].items():
                    replace_actions.append((original_col, [new_col_base]))

            if 'replace_multi' in join and isinstance(join['replace_multi'], dict):
                for target_col, source_cols_base in join['replace_multi'].items():
                    replace_actions.append((target_col, source_cols_base))

            for target_col, source_cols_base in replace_actions:
                if target_col not in df_processed.columns:
                    continue

                source_cols_aliased = [get_aliased_col_name(c) for c in source_cols_base]
                cols_to_concat = [target_col] + [c for c in source_cols_aliased if c in df_processed.columns]
                
                new_values = []
                for row in df_processed[cols_to_concat].itertuples(index=False):
                    parts = [str(val) for val in row if pd.notna(val) and str(val).strip() != '']
                    new_values.append(' | '.join(parts))
                
                df_processed[target_col] = new_values

                for col in source_cols_aliased:
                    if col in df_processed.columns and col not in columns_to_drop:
                        columns_to_drop.append(col)

        if columns_to_drop:
            df_processed.drop(columns=columns_to_drop, inplace=True, errors='ignore')
        
        df = df_processed

    # Handle Date Columns
    if date_columns:
        for column in date_columns:
            if column in df.columns:
                df[column] = pd.to_datetime(df[column], errors='coerce').dt.date

    # Reorder columns
    if not output_columns and columns:
        ordered_cols = list(columns) if columns else []
        if custom_columns:
            for custom_col in custom_columns:
                if 'name' in custom_col:
                    ordered_cols.append(custom_col['name'])
        available_cols = [col for col in ordered_cols if col in df.columns]
        remaining_cols = [col for col in df.columns if col not in available_cols]
        df = df[available_cols + remaining_cols]

    # Convert to final data_type
    if data_type == "dataframe":
        if output_columns:
            df = df[[col for col in output_columns if col in df.columns]]
        conn.close()
        return df

    elif data_type == "list":
        df_processed = df
        if output_columns:
            df_processed = df[[col for col in output_columns if col in df.columns]]
        
        processed_rows = df_processed.values.tolist()
        result = [delimiter.join("None" if item is None else str(item) for item in p_row) for p_row in processed_rows]
        conn.close()
        return result

    elif data_type == "dictionary":
        df_processed = df
        key_col, val_col = None, None

        dict_cols = output_columns if output_columns else columns
        
        if dict_cols:
            if len(dict_cols) != 2:
                raise ValueError("For dictionary data type, 'output_columns' or 'columns' must contain exactly two columns (key, value).")
            key_col, val_col = dict_cols[0], dict_cols[1]
        else:
            available_cols = df_processed.columns.tolist()
            if len(available_cols) < 2:
                raise ValueError("For dictionary data type, the result must have at least two columns.")
            key_col, val_col = available_cols[0], available_cols[1]
        
        if key_col not in df_processed.columns or val_col not in df_processed.columns:
             raise ValueError(f"Specified key ('{key_col}') or value ('{val_col}') column not found in processed DataFrame columns: {df_processed.columns.tolist()}")

        result = pd.Series(df_processed[val_col].values, index=df_processed[key_col]).to_dict()
        conn.close()
        return result

    else:
        conn.close()
        raise ValueError("Invalid data_type. Must be 'dataframe', 'list', or 'dictionary'.")

def get_total_count(table_name, col_where=None, search_value=None, search_columns=None, joins=None):
    """
    Đếm tổng số bản ghi trong một bảng dựa trên các điều kiện lọc.
    """
    conn = connect_db()
    cursor = conn.cursor()

    # Lấy kiểu dữ liệu các cột
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    column_info = cursor.fetchall()
    column_types = {row[1]: row[2].lower() for row in column_info}

    # Xây dựng câu lệnh
    query = f"SELECT COUNT(*) FROM [{table_name}]"

    # JOIN
    join_statements = []
    if joins:
        for join in joins:
            from_table = join.get("from_table", table_name)
            join_table = join.get("table")
            join_alias = join.get("alias", join_table)
            join_on = join.get("on")
            on_conditions = " AND ".join(
                f"[{from_table}].[{key}] = [{join_alias}].[{value}]" for key, value in join_on.items()
            )
            join_statement = f"LEFT JOIN [{join_table}] AS [{join_alias}] ON {on_conditions}"
            join_statements.append(join_statement)
    if join_statements:
        query += " " + " ".join(join_statements)

    # WHERE
    where_clauses = []
    if col_where:
        for column, condition in col_where.items():
            if '.' in column:
                parts = column.rsplit('.', 1)
                table_prefix = parts[0]
                column_name = parts[1]
            else:
                table_prefix = table_name
                column_name = column

            column_name = column_name.strip('[]')
            column_type = column_types.get(column_name, "text")

            def _quote_value(value):
                if value is None:
                    return "NULL"
                if column_type in ['integer', 'real', 'numeric']:
                    return str(value)
                safe_value = str(value).replace("'", "''")
                return f"'{safe_value}'"

            if isinstance(condition, dict) and 'Between' in condition:
                between_values = condition['Between']
                if len(between_values) == 2:
                    start_value, end_value = between_values
                    start_str = _quote_value(start_value)
                    end_str = _quote_value(end_value)
                    where_clauses.append(f"[{table_prefix}].[{column_name}] BETWEEN {start_str} AND {end_str}")
            elif isinstance(condition, list) or (isinstance(condition, tuple) and condition[0] in ["IN", "NOT IN"]):
                operator, values = ("IN", condition) if isinstance(condition, list) else condition
                if values:
                    condition_str = ", ".join(_quote_value(v) for v in values)
                    where_clauses.append(f"[{table_prefix}].[{column_name}] {operator} ({condition_str})")
            elif isinstance(condition, tuple) and len(condition) == 2:
                operator, value = condition
                value_str = _quote_value(value)
                where_clauses.append(f"[{table_prefix}].[{column_name}] {operator} {value_str}")
            elif isinstance(condition, str) and condition.strip().upper() in ['IS NULL', 'IS NOT NULL']:
                where_clauses.append(f"[{table_prefix}].[{column_name}] {condition}")
            else:
                value_str = _quote_value(condition)
                where_clauses.append(f"[{table_prefix}].[{column_name}] = {value_str}")

    if search_value and search_columns:
        search_conditions = []
        safe_search_value = str(search_value).replace("'", "''")
        for col in search_columns:
            table_prefix = col.split('.')[0] if '.' in col else table_name
            col_name_only = col.split('.')[-1]
            search_conditions.append(f"CAST([{table_prefix}].[{col_name_only}] AS TEXT) LIKE '%{safe_search_value}%'")
        if search_conditions:
            where_clauses.append(f"({ ' OR '.join(search_conditions) })")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    try:
        cursor.execute(query)
        total_count = cursor.fetchone()[0]
        conn.close()
        return total_count if total_count is not None else 0
    except Exception as e:
        print(f"Lỗi khi lấy tổng số lượng: {e}")
        conn.close()
        return 0

def insert_data_to_table(table_name, columns_list, values_list):
    """Chèn dữ liệu vào bảng"""
    try:
        conn = connect_db()
        cursor = conn.cursor()

        columns = "[" + '], ['.join(columns_list) + "]"
        placeholders = ', '.join(['?' for _ in range(len(values_list))])
        query = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
        
        cursor.execute(query, values_list)
        conn.commit()
        conn.close()
        return "Đã chèn dữ liệu thành công"

    except Exception as e:
        return f"Lỗi: {str(e)}"

def query_to_dataframe(query):
    """Thực hiện truy vấn và trả về DataFrame"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query)
    
    columns = [description[0] for description in cursor.description]
    data = cursor.fetchall()
    
    df = pd.DataFrame([dict(row) for row in data])
    
    cursor.close()
    conn.close()

    return df

def delete_data_from_table_by_ids(table_name, list_ids, nguoisua, thoigiansua, col_where='ID', col_mark='Đã xóa'):
    """Đánh dấu xóa các bản ghi theo ID"""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        ids_string = "'" + "','".join(map(str, list_ids)) + "'"
        sql = f"UPDATE [{table_name}] SET [{col_mark}] = 1, [Người sửa]=?, [Thời gian sửa]=? WHERE [{col_where}] IN ({ids_string})"
        cursor.execute(sql, (nguoisua, thoigiansua))
        
        conn.commit()
        conn.close()
        return "Cập nhật dữ liệu thành công!"
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"Lỗi: {e}"

def convert_date_columns_to_string(dataframe, date_columns):
    """Chuyển đổi cột ngày thành chuỗi"""
    df = dataframe.copy()
    for column in date_columns:
        if column in df.columns:
            df[column] = df[column].dt.strftime('%Y-%m-%d')
    return df

def update_database_from_dataframe(table_name, dataframe, nguoisua, column_key, date_columns=None):
    """Cập nhật database từ DataFrame"""
    try:
        dataframe = dataframe.replace({pd.NA: None, np.nan: None, pd.NaT: None})
        
        # Chuyển đổi tất cả cột datetime/Timestamp thành string
        for col in dataframe.columns:
            if pd.api.types.is_datetime64_any_dtype(dataframe[col]):
                dataframe[col] = dataframe[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)
        
        conn = connect_db()
        cursor = conn.cursor()

        columns_to_drop = ['Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa', 'Fullname']
        existing_columns_to_drop = [col for col in columns_to_drop if col in dataframe.columns]
        
        if existing_columns_to_drop:
            dataframe = dataframe.drop(columns=existing_columns_to_drop)

        if date_columns is not None:
            dataframe = convert_date_columns_to_string(dataframe, date_columns)

        for index, row in dataframe.iterrows():
            key_value = row[column_key]
            update_columns = dataframe.drop(columns=[column_key]).columns
            column_names = [f"[{column}]" for column in update_columns]

            sql = f'''
                UPDATE [{table_name}]
                SET {", ".join([f"{col} = ?" for col in column_names])},
                    [Thời gian sửa] = ?,
                    [Người sửa] = ?
                WHERE [{column_key}] = ?
            '''
            
            new_info = list(row[update_columns]) + [fn.get_vietnam_time().strftime('%Y-%m-%d %H:%M:%S'), nguoisua, key_value]
            cursor.execute(sql, new_info)

        conn.commit()
        conn.close()

        return f"Cập nhật thông tin vào bảng {table_name} thành công"
    except Exception as e:
        error_str = str(e).lower()
        if 'unique' in error_str or 'duplicate' in error_str:
            return "Lỗi: Dữ liệu bạn vừa nhập bị trùng lặp với một bản ghi đã có. Vui lòng kiểm tra lại."
        return f"Lỗi: {str(e)}"

def get_info(df, table_name, columns_name, columns_map, columns_key=None,
             columns_output=None, columns_position=None, where=True):
    """Lấy thông tin từ bảng và merge vào DataFrame"""
    if not all(col in df.columns for col in columns_map):
        return df

    if columns_key is None:
        columns_key = [columns_name[0]]

    col_where_clause = {'Đã xóa': ('=', 0)} if where else None
    
    # Lấy các giá trị duy nhất
    unique_values = {}
    for col in columns_map:
        unique_values[col] = df[col].dropna().unique().tolist()

    if col_where_clause is None:
        col_where_clause = {}

    for key, map_col in zip(columns_key, columns_map):
        if unique_values[map_col]:
            col_where_clause[key] = ('IN', unique_values[map_col])

    df_info = get_columns_data(
        table_name=table_name,
        columns=columns_name,
        col_where=col_where_clause
    )

    if df_info.empty:
        return df

    rename_dict = {key: map_col for key, map_col in zip(columns_key, columns_map)}
    df_info = df_info.rename(columns=rename_dict)

    df_info = df_info.drop_duplicates(subset=columns_map)

    df_merged = pd.merge(df, df_info, how='left', on=columns_map)

    if columns_output:
        rename_output_dict = {
            old: new
            for old, new in zip(columns_name, columns_output)
            if old in df_merged.columns
        }
        df_merged = df_merged.rename(columns=rename_output_dict)

    if columns_position:
        final_columns = [col for col in columns_position if col in df_merged.columns]
        df_merged = df_merged[final_columns]

    return df_merged

def insert_data_to_sql_server(table_name, dataframe, created_by=None, delete_old_data=False, delete_by_ids=None, col_where=None):
    """Chèn dữ liệu từ DataFrame vào bảng (đổi tên để tương thích)"""
    try:
        dataframe = dataframe.replace({pd.NA: None, np.nan: None, pd.NaT: None})
        
        # Chuyển đổi tất cả cột datetime/Timestamp thành string
        for col in dataframe.columns:
            if pd.api.types.is_datetime64_any_dtype(dataframe[col]):
                dataframe[col] = dataframe[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)
        
        conn = connect_db()
        cursor = conn.cursor()

        if delete_old_data:
            cursor.execute(f"DELETE FROM [{table_name}]")
        
        if created_by is not None:
            dataframe['Người tạo'] = created_by

        # Xử lý từng dòng: Xóa trước rồi Insert
        for _, row in dataframe.iterrows():
            # Nếu có delete_by_ids, xóa bản ghi cũ theo các cột khóa
            if delete_by_ids is not None and not delete_old_data:
                conditions = []
                params = []
                for col in delete_by_ids:
                    if col in row.index and pd.notna(row[col]):
                        conditions.append(f"[{col}] = ?")
                        params.append(row[col])
                
                if conditions:
                    # Thêm điều kiện Đã xóa = 0 nếu cột tồn tại
                    cursor.execute(f"PRAGMA table_info([{table_name}])")
                    columns_in_table = [col[1] for col in cursor.fetchall()]
                    if 'Đã xóa' in columns_in_table:
                        conditions.append("[Đã xóa] = 0")
                    
                    where_clause = " AND ".join(conditions)
                    sql = f"DELETE FROM [{table_name}] WHERE {where_clause}"
                    cursor.execute(sql, tuple(params))
            
            # Insert dòng mới
            placeholders = ', '.join(['?' for _ in row])
            columns = '], ['.join(dataframe.columns)
            sql = f"INSERT INTO [{table_name}] ([{columns}]) VALUES ({placeholders})"
            cursor.execute(sql, tuple(row))

        conn.commit()
        conn.close()

        return "Đã cập nhật thành công!"
    except Exception as e:
        return f"Lỗi: {str(e)}"

def hashpw(password):
    """Hash password"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed_password):
    """Kiểm tra password"""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def get_table_columns(table_name):
    """Lấy danh sách tất cả các cột của một bảng"""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info([{table_name}])")
        rows = cursor.fetchall()
        columns = [row[1] for row in rows]
        conn.close()
        return columns
    except Exception as e:
        print(f"Lỗi khi lấy danh sách cột cho bảng {table_name}: {e}")
        conn.close()
        return []

def drop_all_filtered_unique_indexes(table_name):
    """Xóa tất cả các unique index (SQLite không hỗ trợ filtered index như SQL Server)"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Lấy danh sách index
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (table_name,))
        indexes = cursor.fetchall()
        
        dropped = []
        for idx in indexes:
            idx_name = idx[0]
            # Không xóa index tự động tạo bởi SQLite
            if not idx_name.startswith('sqlite_'):
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS [{idx_name}]")
                    dropped.append(idx_name)
                except:
                    pass
        
        conn.commit()
        conn.close()
        return dropped
    except Exception as e:
        conn.close()
        return []

def drop_old_unique_constraints_and_computed_columns(table_name):
    """
    SQLite không hỗ trợ ALTER TABLE để xóa constraints như SQL Server.
    Hàm này chỉ để tương thích, không thực hiện gì.
    """
    return {
        'constraints_dropped': [],
        'computed_columns_dropped': []
    }

def get_table_columns_info(table_name):
    """
    Lấy thông tin các cột của bảng.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    system_columns = ['Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa']
    
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        col_name = row[1]
        col_type = row[2]
        not_null = row[3]
        default_val = row[4]
        is_pk = row[5]
        
        if col_name in system_columns:
            continue
            
        # Chuyển đổi kiểu dữ liệu SQLite về dạng SQL Server-like để tương thích
        if col_type.upper() == 'TEXT':
            type_str = 'NVARCHAR(n)'
            max_length = 50
        elif col_type.upper() == 'INTEGER':
            type_str = 'INT'
            max_length = None
        elif col_type.upper() == 'REAL':
            type_str = 'FLOAT'
            max_length = None
        elif col_type.upper() == 'NUMERIC':
            type_str = 'DECIMAL'
            max_length = None
        elif col_type.upper() == 'DATETIME':
            type_str = 'DATETIME'
            max_length = None
        else:
            type_str = col_type.upper()
            max_length = None
        
        results.append({
            'name': col_name,
            'type': type_str,
            'max_length': max_length,
            'is_nullable': 0 if not_null else 1,
            'is_identity': 1 if is_pk else 0
        })
    
    conn.close()
    return results

def get_filtered_unique_index_info(table_name):
    """
    SQLite không hỗ trợ filtered index.
    Hàm này trả về danh sách rỗng để tương thích.
    """
    return []

def generate_filtered_index_query(table_name, columns):
    """
    Tạo câu lệnh CREATE UNIQUE INDEX cho SQLite.
    SQLite không hỗ trợ filtered index, nên tạo unique index thông thường.
    """
    if not table_name or not columns:
        return ""
    column_names_str = '_'.join(columns)
    index_name = f"IX_UQ_{table_name}_{column_names_str}"
    column_list = ', '.join([f"[{col}]" for col in columns])
    query = f"CREATE UNIQUE INDEX IF NOT EXISTS [{index_name}] ON [{table_name}] ({column_list});"
    return query.strip()

def generate_alter_table_queries(table_name, df_new, df_old):
    """
    So sánh cấu trúc bảng cũ và mới, tạo các câu lệnh ALTER TABLE.
    Lưu ý: SQLite có giới hạn với ALTER TABLE, chỉ hỗ trợ ADD COLUMN và RENAME COLUMN.
    Để xóa hoặc sửa cột, cần tạo bảng mới và copy dữ liệu.
    """
    queries = []
    
    if df_new.empty or 'Tên trường' not in df_new.columns:
        return queries
    
    if df_old.empty or 'name' not in df_old.columns:
        # Tất cả các cột trong df_new là cột mới
        for index, row in df_new.iterrows():
            if row['Tên trường'] and row['Kiểu dữ liệu']:
                field_name = f"[{row['Tên trường']}]"
                data_type = row['Kiểu dữ liệu']
                
                data_type = convert_sqlserver_to_sqlite_type(data_type, row.get("n (Mặc định n=50)"))
                
                is_auto_increment = row.get('Auto Increment', False)
                if is_auto_increment and 'INT' in data_type.upper():
                    queries.append(f"-- CẢNH BÁO: SQLite không cho phép thêm cột AUTOINCREMENT vào bảng đã tồn tại.")
                    continue
                
                not_null = "NOT NULL" if row.get('Not Null') else ""
                default_value = row.get('Mặc định', '')
                if default_value and str(default_value).strip() and str(default_value) != "0":
                    if isinstance(default_value, (int, float)):
                        default_clause = f"DEFAULT {default_value}"
                    else:
                        default_clause = f"DEFAULT '{default_value}'"
                else:
                    default_clause = ""
                
                queries.append(f"ALTER TABLE [{table_name}] ADD COLUMN {field_name} {data_type} {not_null} {default_clause};")
        return queries
    
    df_new = df_new.set_index('Tên trường')
    df_old = df_old.set_index('name')

    # Cột cần thêm
    new_cols = df_new.index.difference(df_old.index)
    for col_name in new_cols:
        row = df_new.loc[col_name]
        data_type = row['Kiểu dữ liệu']
        data_type = convert_sqlserver_to_sqlite_type(data_type, row.get("n (Mặc định n=50)"))
        
        is_auto_increment = row.get('Auto Increment', False)
        if is_auto_increment:
            queries.append(f"-- CẢNH BÁO: SQLite không cho phép thêm cột AUTOINCREMENT vào bảng đã tồn tại.")
            continue
        
        not_null = "NOT NULL" if row.get('Not Null') else ""
        default_value = row.get('Mặc định', '')
        if default_value and str(default_value).strip() and str(default_value) != "0":
            if isinstance(default_value, (int, float)):
                default_clause = f"DEFAULT {default_value}"
            else:
                default_clause = f"DEFAULT '{default_value}'"
        else:
            default_clause = ""
        
        queries.append(f"ALTER TABLE [{table_name}] ADD COLUMN [{col_name}] {data_type} {not_null} {default_clause};")

    # Cột cần xóa
    dropped_cols = df_old.index.difference(df_new.index)
    if len(dropped_cols) > 0:
        queries.append(f"-- CẢNH BÁO: SQLite không hỗ trợ DROP COLUMN trực tiếp.")
        queries.append(f"-- Bạn cần tạo bảng mới và copy dữ liệu để xóa các cột: {', '.join(dropped_cols)}")

    # Cột cần sửa
    common_cols = df_new.index.intersection(df_old.index)
    for col_name in common_cols:
        new_row = df_new.loc[col_name]
        old_row = df_old.loc[col_name]

        # SQLite không hỗ trợ ALTER COLUMN
        new_type = convert_sqlserver_to_sqlite_type(new_row['Kiểu dữ liệu'], new_row.get("n (Mặc định n=50)"))
        old_type = old_row['type']
        
        if new_type.upper() != old_type.upper():
            queries.append(f"-- CẢNH BÁO: SQLite không hỗ trợ ALTER COLUMN để thay đổi kiểu dữ liệu của cột [{col_name}].")
            queries.append(f"-- Bạn cần tạo bảng mới và copy dữ liệu để thay đổi kiểu dữ liệu.")

    return queries

def get_table_structure(table_name):
    """
    Lấy đầy đủ thông tin về cấu trúc bảng.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    system_columns = ['Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa']
    
    cursor.execute(f"PRAGMA table_info([{table_name}])")
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        col_name = row[1]
        col_type = row[2]
        not_null = row[3]
        default_val = row[4]
        is_pk = row[5]
        
        if col_name in system_columns:
            continue
        
        # Xử lý kiểu dữ liệu
        if col_type.upper() == 'TEXT':
            formatted_type = 'NVARCHAR(n)'
            n_value = 50
        elif col_type.upper() == 'INTEGER':
            formatted_type = 'INT'
            n_value = 50
        elif col_type.upper() == 'REAL':
            formatted_type = 'FLOAT'
            n_value = 50
        elif col_type.upper() == 'NUMERIC':
            formatted_type = 'DECIMAL'
            n_value = 50
        elif col_type.upper() == 'DATETIME':
            formatted_type = 'DATETIME'
            n_value = 50
        else:
            formatted_type = col_type.upper()
            n_value = 50
        
        # Xử lý NOT NULL
        is_not_null = 1 if not_null else 0
        
        # Xử lý giá trị mặc định
        if default_val:
            default_val = str(default_val).strip("'")
        else:
            default_val = "0"
        
        data.append({
            'Tên trường': col_name,
            'Kiểu dữ liệu': formatted_type,
            'n (Mặc định n=50)': int(n_value),
            'Unique (Đã xóa = 0)': 0,  # SQLite không có filtered index
            'Not Null': int(is_not_null),
            'Mặc định': default_val,
            'DEFAULT_CONSTRAINT_NAME': None
        })
    
    conn.close()
    return pd.DataFrame(data)
