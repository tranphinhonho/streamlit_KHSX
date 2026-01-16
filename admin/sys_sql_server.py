import json
import pyodbc
import pandas as pd
import bcrypt
import numpy as np
import platform
import admin.sys_functions as fn
import os
# Lấy đường dẫn tuyệt đối đến thư mục chứa script hiện tại
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

with open(config_path, 'r') as file:
    data = json.load(file)

# Lấy password kết nối
server = data['server']
database = data['database']
username = data['username']
pwd = data['password']

def connect_db(server, database, username, pwd):
    """
    Cố gắng kết nối đến SQL Server bằng cách thử qua nhiều driver ODBC phổ biến.
    """
    # Danh sách các driver để thử, theo thứ tự ưu tiên
    drivers_to_try = [
        "{ODBC Driver 18 for SQL Server}",
        "{ODBC Driver 17 for SQL Server}",
        "{SQL Server Native Client 11.0}",
        "{SQL Server}"
    ]

    last_error = None

    for driver in drivers_to_try:
        try:
            # Thêm TrustServerCertificate=yes để tránh lỗi SSL với các driver mới
            cnstr = (
                f"Driver={driver};"
                f"Server={server};"
                f"Database={database};"
                f"UID={username};"
                f"PWD={pwd};"
                f"TrustServerCertificate=yes;"
            )
            cn = pyodbc.connect(cnstr, timeout=5)
            cn.autocommit = True
            return cn
        except pyodbc.InterfaceError as e:
            # Lỗi IM002 là lỗi không tìm thấy driver, tiếp tục thử driver tiếp theo
            if 'IM002' in str(e):
                last_error = e
                continue
            # Các lỗi InterfaceError khác (ví dụ: sai thông tin đăng nhập) thì báo lỗi ngay
            last_error = e
            break
        except pyodbc.Error as e:
            last_error = e
            break # Dừng lại nếu có lỗi khác (ví dụ: login failed)

    # Nếu không có driver nào hoạt động, đưa ra thông báo lỗi cuối cùng
    error_message = (
        f"Không thể kết nối đến SQL Server. Lỗi cuối cùng: {last_error}\n"
        "Vui lòng đảm bảo rằng:\n"
        "1. Thông tin server, database, username, password trong file config.json là chính xác.\n"
        "2. Máy tính đã cài đặt ít nhất một trong các ODBC Driver for SQL Server (ưu tiên phiên bản 17 hoặc 18)."
    )
    raise ConnectionError(error_message)

def generate_next_code(tablename, column_name, prefix='PT', num_char=5):
    sql = f"""
    -- Lấy mã kế tiếp cho bảng {tablename}
    SELECT
        CONCAT('{prefix}', RIGHT(CONCAT(REPLICATE('0', {num_char}),
        CAST(ISNULL(MAX(TRY_CAST(SUBSTRING([{column_name}], {len(prefix) + 1}, LEN([{column_name}]) - {len(prefix)}) AS INT)), 0) + 1 AS NVARCHAR)), {num_char}))
        AS [Mã kế tiếp]
    FROM
        [{tablename}]
    WHERE
        [{column_name}] LIKE '{prefix}%';
    """
    return query_database_sqlite(sql_string=sql, data_type='value')

def generate_create_table_query_sql_server(table_name, df):
    """
    Tạo câu lệnh CREATE TABLE từ DataFrame.
    Hỗ trợ Auto Increment cho bất kỳ cột nào được đánh dấu.
    """
    create_table_query = f"CREATE TABLE [{table_name}] (\n"
    
    system_columns = ['Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa']
    df_filtered = df[~df['Tên trường'].isin(system_columns)]
    
    has_primary_key = False
    
    for index, row in df_filtered.iterrows():
        if row['Tên trường'] and row['Kiểu dữ liệu']:
            field_name = f"[{row['Tên trường']}]"
            data_type = row['Kiểu dữ liệu']
            
            if "(n)" in data_type:
                n_value = row.get("n (Mặc định n=50)")
                if pd.isna(n_value) or not isinstance(n_value, (int, float)) or n_value <= 0:
                    n_value = 50
                data_type = str(data_type).replace('(n)', f'({int(n_value)})')
            
            # Xử lý Auto Increment
            is_auto_increment = row.get('Auto Increment', False)
            if is_auto_increment:
                # Chỉ các kiểu số mới có thể IDENTITY
                if data_type.upper() in ['INT', 'BIGINT', 'SMALLINT', 'TINYINT']:
                    data_type += " IDENTITY(1,1) PRIMARY KEY"
                    has_primary_key = True
                else:
                    # Nếu không phải kiểu số, bỏ qua auto increment
                    is_auto_increment = False
            
            # NOT NULL và DEFAULT chỉ áp dụng nếu không phải auto increment
            if not is_auto_increment:
                not_null = "NOT NULL" if row.get('Not Null') else "NULL"
                
                default_value = row.get('Mặc định')
                if default_value is None or str(default_value).strip() == "" or str(default_value) == "0":
                    default_value = ""
                else:
                    default_value = f"DEFAULT {default_value}" if isinstance(default_value, (int, float)) else f"DEFAULT '{default_value}'"
                
                create_table_query += f"\t{field_name} {data_type} {not_null} {default_value},\n"
            else:
                create_table_query += f"\t{field_name} {data_type},\n"
    
    # Thêm các cột hệ thống
    create_table_query += "\t[Người tạo] NVARCHAR(255),\n"
    create_table_query += "\t[Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,\n"
    create_table_query += "\t[Người sửa] NVARCHAR(255),\n"
    create_table_query += "\t[Thời gian sửa] DATETIME,\n"
    create_table_query += "\t[Đã xóa] BIT DEFAULT 0\n"
    create_table_query += ");"
    
    return create_table_query


def get_id_by_name_from_df(df, table_name='MonHoc', columns_get=['Tên môn học', 'Mã môn học'],
                           columns_rename={'Tên môn học': 'Phụ trách'}, columns_on=['Phụ trách'], how='left'):
    df_monhoc = get_columns_data(table_name=table_name, columns=columns_get)
    df_monhoc = df_monhoc.rename(columns=columns_rename)
    df = pd.merge(df, df_monhoc, how=how, on=columns_on)
    return df

def get_id_by_name(tablename,column_name, value_name,col_id='ID'):
    sql = f"Select Top 1 [{col_id}] from {tablename} Where [Đã xóa]=0 and [{column_name}]=N'{value_name}'"
    return query_database_sqlite(sql_string=sql,data_type='value')

def query_database_sqlite(sql_string, data_type=None, delimiter=' | ', params=None):
    # Kết nối tới database
    cn = None
    cursor = None
    try:
        cn = connect_db(server, database, username, pwd)
        cursor = cn.cursor()

        if data_type is not None:
            # Lấy kết quả truy vấn
            if params:
                cursor.execute(sql_string, params)
            else:
                cursor.execute(sql_string)
            
            columns = [column[0] for column in cursor.description]  # Lấy tên cột

            if data_type == 'dataframe':
                rows = cursor.fetchall()
                df = pd.DataFrame.from_records(rows, columns=columns)
                return df
            elif data_type == 'list':
                rows = cursor.fetchall()
                result = [delimiter.join(map(str, row)) for row in rows]
                return result
            elif data_type == 'value':
                result = cursor.fetchone()
                if result is not None:
                    result = result[0]
                return result
        else:
            # Thực thi lệnh truy vấn (thường là INSERT, UPDATE, DELETE)
            if params:
                cursor.execute(sql_string, params)
            else:
                cursor.execute(sql_string)
            cn.commit()
            return "Đã xử lý thành công!"
    except Exception as e:
        # Ném lại lỗi để Streamlit có thể bắt và hiển thị
        raise e
    finally:
        # Đóng kết nối nếu tồn tại
        if cursor:
            cursor.close()
        if cn:
            cn.close()

def get_all_tables():
    cn = connect_db(server,database,username,pwd)
    sql_string = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME NOT LIKE 'tbsys_%';"

    cursor = cn.cursor()
    cursor.execute(sql_string)
    rows = cursor.fetchall()

    # Trả về danh sách các bảng
    tables = [row[0] for row in rows]
    return tables

def get_all_tables_admin():
    cn = connect_db(server,database,username,pwd)
    sql_string = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"

    cursor = cn.cursor()
    cursor.execute(sql_string)
    rows = cursor.fetchall()

    # Trả về danh sách các bảng
    tables = [row[0] for row in rows]
    return tables

def delete_tables(table_list):
    cn = connect_db(server,database,username,pwd)
    cursor = cn.cursor()
    results = []  # Danh sách để lưu kết quả

    # Duyệt qua danh sách các bảng và xóa từng bảng
    for table in table_list:
        try:
            # Tạo câu lệnh xóa bảng
            drop_query = f"DROP TABLE IF EXISTS {table};"
            cursor.execute(drop_query)
            results.append(f"Đã xóa bảng {table}")  # Thêm thông báo thành công
        except Exception as e:
            results.append(f"Lỗi khi xóa bảng {table}: {e}")  # Thêm thông báo lỗi

    # Commit thay đổi nếu có
    cn.commit()
    cursor.close()

    # Trả về danh sách kết quả
    return results


def get_columns_data(table_name, columns=None, delimiter=" | ", data_type="dataframe",
                     col_where=None, type="", col_order=None, group_by=None, date_columns=None,
                     joins=None, distinct=False, custom_columns=None, output_columns=None,
                     page_number=None, rows_per_page=None, search_value=None, search_columns=None):
    """
    Lấy dữ liệu từ bảng SQL Server với nhiều tùy chọn lọc và sắp xếp.
    
    Cách sử dụng toán tử Between:
    col_where={'column_name': {'Between': [start_value, end_value]}}
    
    Ví dụ:
    - Lọc ngày: col_where={'Ngày': {'Between': ['2023-01-01', '2023-12-31']}}
    - Lọc số: col_where={'Giá': {'Between': [100, 500]}}
    """
    cn = connect_db(server, database, username, pwd)

    cursor = cn.cursor()

    # Xử lý mặc định cho col_order và col_group
    if col_order is None:
        col_order = {}
    if group_by is None:
        group_by = []
    if custom_columns is None:
        custom_columns = []

    # Lấy danh sách kiểu dữ liệu của các cột
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
    """)

    column_types = {row[0]: row[1] for row in cursor.fetchall()}

    # --- Helper function for quoting values based on SQL type ---
    def _quote_sql_value(value, sql_type):
        if value is None:
            return "NULL"
        # Numeric types should not be quoted
        if sql_type in ['int', 'bigint', 'float', 'decimal', 'money', 'bit', 'tinyint', 'smallint', 'numeric']:
            return str(value)
        # String types need N prefix for Unicode and escaped single quotes
        safe_value = str(value).replace("'", "''")
        if sql_type in ['nvarchar', 'nchar', 'ntext']:
            return f"N'{safe_value}'"
        # Other types (like varchar, date, datetime) are quoted normally
        return f"'{safe_value}'"

    # Tạo một bản sao của danh sách cột để làm việc, giữ nguyên `columns` gốc cho việc sắp xếp cuối cùng
    working_columns = list(columns) if columns is not None else []


    # Xây dựng danh sách các cột cần lấy từ `working_columns`
    selected_columns = []
    if not working_columns:
        # Nếu không có cột nào được chỉ định (kể cả sau khi thêm các cột replace), lấy tất cả các cột
        all_table_columns = get_table_columns(table_name)
        if not all_table_columns:
            # Fallback to '*' if getting column names fails
            selected_columns.append(f"[{table_name}].*")
        else:
            selected_columns += [f"[{table_name}].[{column}]" for column in all_table_columns]
    else:
        selected_columns += [f"[{table_name}].[{column}]" for column in working_columns]

    # Thêm cột custom vào danh sách selected_columns
    for custom_column in custom_columns:
        column_name = custom_column.get("name")  # Tên cột mới
        expression = custom_column.get("expression")  # Biểu thức tính toán
        if not column_name or not expression:
            raise ValueError("Each custom column must have a 'name' and an 'expression'.")

        # Thêm biểu thức vào danh sách cột chọn
        selected_columns.append(f"({expression}) AS [{column_name}]")

    # Xử lý JOIN nếu có
    join_statements = []
    if joins:
        for join in joins:
            from_table = join.get("from_table", table_name)
            join_table = join.get("table")
            join_alias = join.get("alias", join_table)  # Sử dụng alias, nếu không có thì dùng tên bảng
            join_on = join.get("on")
            join_columns = join.get("columns", [])

            # Luôn luôn đặt bí danh cho các cột được join để tránh trùng lặp
            # Ví dụ: SELECT [Size].[Tên size] AS [SizeTP_Tên size]
            selected_columns += [f"[{join_alias}].[{col}] AS [{join_alias}_{col}]" for col in join_columns]

            # Tạo điều kiện JOIN (sử dụng alias)
            on_conditions = " AND ".join(
                f"[{from_table}].[{key}] = [{join_alias}].[{value}]" for key, value in join_on.items()
            )

            # Xử lý điều kiện JOIN bổ sung (join_where)
            join_where = join.get("join_where")
            if join_where and isinstance(join_where, dict):
                for col, cond in join_where.items():
                    if isinstance(cond, tuple) and len(cond) == 2:
                        operator, value = cond
                        column_type = column_types.get(col, "").lower()
                        value_str = _quote_sql_value(value, column_type)
                        on_conditions += f" AND [{from_table}].[{col}] {operator} {value_str}"
            
            # Tạo câu lệnh JOIN (sử dụng alias)
            join_statement = f"LEFT JOIN [{join_table}] AS [{join_alias}] ON {on_conditions}"
            join_statements.append(join_statement)

    # Thêm DISTINCT nếu cần
    distinct_clause = "DISTINCT" if distinct else ""

    # Xây dựng câu lệnh truy vấn cơ bản
    query = f"SELECT {distinct_clause} {', '.join(selected_columns)} FROM [{table_name}]"

    # Thêm các câu lệnh JOIN vào truy vấn
    if join_statements:
        query += " " + " ".join(join_statements)


    # --- WHERE Clause Construction ---
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
            
            # Chuẩn hóa tên cột bằng cách xóa và thêm lại dấu ngoặc vuông
            column_name = column_name.strip('[]')
            column_type = column_types.get(column_name, "").lower()

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

    # --- Search Clause Construction ---
    if search_value and search_columns:
        search_conditions = []
        safe_search_value = str(search_value).replace("'", "''")
        for col in search_columns:
            # Thêm tiền tố tên bảng để tránh lỗi ambiguous khi tìm kiếm
            table_prefix = col.split('.')[0] if '.' in col else table_name
            col_name_only = col.split('.')[-1]
            
            column_type = column_types.get(col_name_only, "").lower()
            
            if column_type in ['datetime', 'date', 'datetime2']:
                search_conditions.append(f"CONVERT(NVARCHAR, [{table_prefix}].[{col_name_only}], 120) LIKE N'%{safe_search_value}%'")
            else:
                search_conditions.append(f"CAST([{table_prefix}].[{col_name_only}] AS NVARCHAR(MAX)) LIKE N'%{safe_search_value}%'")
        
        if search_conditions:
            where_clauses.append(f"({ ' OR '.join(search_conditions) })")

    # --- Final Query Assembly ---
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    # Xử lý phần nhóm (GROUP BY)
    if len(group_by):
        group_statements = [f"[{col}]" for col in group_by]
        query += " GROUP BY " + ", ".join(group_statements)

    # Xử lý phần sắp xếp (ORDER BY)
    if len(col_order):
        order_statements = []
        for col, order in col_order.items():
            order_statements.append(f"[{col}] {order}")
        query += " ORDER BY " + ", ".join(order_statements)
    elif page_number is not None and rows_per_page is not None:
        # Phân trang yêu cầu ORDER BY, thêm mặc định nếu không có
        query += " ORDER BY (SELECT NULL)"

    # Xử lý phân trang
    if page_number is not None and rows_per_page is not None:
        offset = (page_number - 1) * rows_per_page
        query += f" OFFSET {offset} ROWS FETCH NEXT {rows_per_page} ROWS ONLY"

    # print(query)
    # --- Data Fetching and Processing ---
    cursor.execute(query)
    rows = cursor.fetchall()
    columns_from_db = [column[0] for column in cursor.description]
    df = pd.DataFrame.from_records(rows, columns=columns_from_db)

    # --- Apply Join Replace Logic (trên DataFrame) ---
    if joins:
        df_processed = df.copy()
        columns_to_drop = []

        for join in joins:
            join_table = join.get("table")
            join_alias = join.get("alias", join_table)

            # Hàm trợ giúp này giờ đây chỉ cần ghép alias và tên cột
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
                
                # Lấy các cột cần thiết để ghép nối
                cols_to_concat = [target_col] + [c for c in source_cols_aliased if c in df_processed.columns]
                
                # Sử dụng itertuples để lặp qua từng dòng một cách an toàn
                new_values = []
                for row in df_processed[cols_to_concat].itertuples(index=False):
                    parts = [str(val) for val in row if pd.notna(val) and str(val).strip() != '']
                    new_values.append(' | '.join(parts))
                
                df_processed[target_col] = new_values

                # Thêm các cột nguồn vào danh sách cần xóa
                for col in source_cols_aliased:
                    if col in df_processed.columns and col not in columns_to_drop:
                        columns_to_drop.append(col)

        # Sau khi tất cả các join đã được xử lý, xóa các cột không cần thiết
        if columns_to_drop:
            df_processed.drop(columns=columns_to_drop, inplace=True, errors='ignore')
        
        df = df_processed

    # --- Handle Date Columns ---
    if date_columns:
        for column in date_columns:
            if column in df.columns:
                df[column] = pd.to_datetime(df[column], errors='coerce').dt.date

    # --- Reorder columns to match input order if output_columns not specified ---
    if not output_columns and columns:
        # Lấy danh sách cột từ columns ban đầu + custom_columns
        ordered_cols = list(columns) if columns else []
        if custom_columns:
            for custom_col in custom_columns:
                if 'name' in custom_col:
                    ordered_cols.append(custom_col['name'])
        # Reorder dataframe columns
        available_cols = [col for col in ordered_cols if col in df.columns]
        remaining_cols = [col for col in df.columns if col not in available_cols]
        df = df[available_cols + remaining_cols]

    # --- Reorder columns to match input order if output_columns not specified ---
    if not output_columns and columns:
        # Lấy danh sách cột từ columns ban đầu + custom_columns
        ordered_cols = list(columns) if columns else []
        if custom_columns:
            for custom_col in custom_columns:
                if 'name' in custom_col:
                    ordered_cols.append(custom_col['name'])
        # Sắp xếp lại các cột của dataframe
        available_cols = [col for col in ordered_cols if col in df.columns]
        remaining_cols = [col for col in df.columns if col not in available_cols]
        df = df[available_cols + remaining_cols]

    # --- Convert to final data_type ---
    if data_type == "dataframe":
        if output_columns:
            df = df[[col for col in output_columns if col in df.columns]]
        return df

    elif data_type == "list":
        df_processed = df
        if output_columns:
            df_processed = df[[col for col in output_columns if col in df.columns]]
        
        processed_rows = df_processed.values.tolist()
        result = [delimiter.join("None" if item is None else str(item) for item in p_row) for p_row in processed_rows]
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
        return result

    else:
        raise ValueError("Invalid data_type. Must be 'dataframe', 'list', or 'dictionary'.")
def get_total_count(table_name, col_where=None, search_value=None, search_columns=None, joins=None):
    """
    Đếm tổng số bản ghi trong một bảng dựa trên các điều kiện lọc.
    """
    cn = connect_db(server, database, username, pwd)
    cursor = cn.cursor()

    # Lấy danh sách kiểu dữ liệu của các cột để xử lý tìm kiếm
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
    """)
    column_types = {row[0]: row[1] for row in cursor.fetchall()}

    # Xây dựng câu lệnh truy vấn cơ bản
    query = f"SELECT COUNT_BIG(*) FROM [{table_name}]"

    # Xử lý JOIN nếu có
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

    # Xử lý phần điều kiện WHERE
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

            # Chuẩn hóa tên cột bằng cách xóa và thêm lại dấu ngoặc vuông
            column_name = column_name.strip('[]')
            column_type = column_types.get(column_name, "").lower()

            if isinstance(condition, dict) and 'Between' in condition:
                between_values = condition['Between']
                if len(between_values) == 2:
                    start_value, end_value = between_values
                    if column_type == 'nvarchar':
                        start_str, end_str = f"N'{start_value}'", f"N'{end_value}'"
                    elif column_type in ['datetime', 'date', 'datetime2']:
                        start_str, end_str = f"'{start_value}'", f"'{end_value}'"
                    elif column_type in ['int', 'bigint', 'float', 'decimal', 'money']:
                        start_str, end_str = str(start_value), str(end_value)
                    else:
                        start_str, end_str = f"'{start_value}'", f"'{end_value}'"
                    where_clauses.append(f"[{table_prefix}].[{column_name}] BETWEEN {start_str} AND {end_str}")
            elif isinstance(condition, list) or (isinstance(condition, tuple) and condition[0] in ["IN", "NOT IN"]):
                operator, values = ("IN", condition) if isinstance(condition, list) else condition
                if values:
                    condition_str = ", ".join(f"N'{v}'" if column_type == 'nvarchar' else f"'{v}'" for v in values)
                    where_clauses.append(f"[{table_prefix}].[{column_name}] {operator} ({condition_str})")
            elif isinstance(condition, tuple) and len(condition) == 2:
                operator, value = condition
                value_str = f"N'{value}'" if column_type == 'nvarchar' else f"'{value}'"
                where_clauses.append(f"[{table_prefix}].[{column_name}] {operator} {value_str}")
            elif isinstance(condition, str) and condition.strip().upper() in ['IS NULL', 'IS NOT NULL']:
                where_clauses.append(f"[{table_prefix}].[{column_name}] {condition}")
            else:
                value_str = f"N'{condition}'" if column_type == 'nvarchar' else f"'{condition}'"
                where_clauses.append(f"[{table_prefix}].[{column_name}] = {value_str}")

    if search_value and search_columns:
        search_conditions = []
        for col in search_columns:
            # Thêm tiền tố tên bảng để tránh lỗi ambiguous khi tìm kiếm
            table_prefix = col.split('.')[0] if '.' in col else table_name
            col_name_only = col.split('.')[-1]
            
            column_type = column_types.get(col_name_only, "").lower()
            
            if column_type in ['datetime', 'date', 'datetime2']:
                search_conditions.append(f"CONVERT(NVARCHAR, [{table_prefix}].[{col_name_only}], 120) LIKE N'%{search_value}%'")
            else:
                search_conditions.append(f"CAST([{table_prefix}].[{col_name_only}] AS NVARCHAR(MAX)) LIKE N'%{search_value}%'")
        if search_conditions:
            where_clauses.append(f"({ ' OR '.join(search_conditions) })")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    try:
        cursor.execute(query)
        total_count = cursor.fetchone()[0]
        return total_count if total_count is not None else 0
    except Exception as e:
        print(f"Lỗi khi lấy tổng số lượng: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if cn:
            cn.close()
def get_columns_data_pagination(table_name, columns=None, delimiter=";", data_type="dataframe",
                     col_where=None, type="", col_order=None, date_columns=None, all_page=False,
                     page_number=1, rows_per_page=10):
    cn = connect_db(server, database, username, pwd)
    cursor = cn.cursor()

    # Xử lý mặc định cho col_order
    if col_order is None:
        col_order = {}

    # Xây dựng câu lệnh truy vấn cơ bản
    if columns is None:
        # Nếu columns=None thì lấy tất cả các cột
        query = f"SELECT {type} * FROM {table_name}"
    else:
        query = f"SELECT {type} {', '.join(f'[{column}]' for column in columns)} FROM {table_name}"

    # Xử lý phần điều kiện WHERE
    if col_where:
        where_clauses = []
        for column, condition in col_where.items():
            if isinstance(condition, list):
                # Nếu điều kiện là danh sách, sử dụng IN
                condition_str = ", ".join(f"'{value}'" for value in condition)
                where_clauses.append(f"[{column}] IN ({condition_str})")
            elif isinstance(condition, tuple) and len(condition) == 2:
                # Nếu điều kiện là tuple (operator, value), xây dựng phù hợp
                operator, value = condition
                where_clauses.append(f"[{column}] {operator} '{value}'")
            else:
                # Mặc định sử dụng '=' nếu không có operator
                where_clauses.append(f"[{column}] = '{condition}'")
        query += " WHERE " + " AND ".join(where_clauses)

    # Xử lý phần sắp xếp (ORDER BY)
    if len(col_order):
        order_statements = []
        for col, order in col_order.items():
            order_statements.append(f"[{col}] {order}")
        query += " ORDER BY " + ", ".join(order_statements)
    else:
        # Nếu không có ORDER BY, cần thêm mặc định để sử dụng OFFSET-FETCH
        query += " ORDER BY (SELECT NULL)"  # Tránh lỗi khi không có thứ tự sắp xếp

    # Xử lý phân trang nếu all_page=False
    if not all_page:
        offset = (page_number - 1) * rows_per_page
        query += f" OFFSET {offset} ROWS FETCH NEXT {rows_per_page} ROWS ONLY"

    # Thực thi truy vấn và xử lý dữ liệu tùy thuộc vào data_type yêu cầu
    if data_type == "dataframe":
        cursor.execute(query)
        rows = cursor.fetchall()  # Lấy tất cả dữ liệu trả về
        columns_from_db = [column[0] for column in cursor.description]  # Lấy tên các cột từ description

        rows = [tuple(row) for row in rows]

        # Nếu bạn muốn sử dụng columns truyền vào từ bên ngoài
        df = pd.DataFrame(rows, columns=columns_from_db)

        if date_columns:
            # Chuyển đổi các cột ngày tháng từ dạng text sang dạng date
            for column in date_columns:
                df[column] = pd.to_datetime(df[column], errors='coerce').dt.date
        return df

    elif data_type == "list":
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [delimiter.join(map(str, row)) for row in rows]
        return result

    elif data_type == "dictionary":
        if len(columns) != 2:
            raise ValueError("For dictionary data type, columns must contain exactly two columns.")
        cursor.execute(query)
        rows = cursor.fetchall()
        result = {row[0]: row[1] for row in rows}
        return result

    else:
        raise ValueError("Invalid data_type. Must be 'dataframe', 'list', or 'dictionary'.")


# Ví dụ 1: Tìm các bản ghi với cột status là 'active' và age nằm trong danh sách [25, 30, 35].
# python
# Sao chép mã
# col_where = {
#     "status": "active",
#     "age": [25, 30, 35]
# }
# Ví dụ 2: Tìm các bản ghi với salary lớn hơn 5000 và department là 'IT'.
# python
# Sao chép mã
# col_where = {
#     "salary": (">", 5000),
#     "department": "IT"
# }
# Lệnh gọi hàm
# python
# Sao chép mã
# df = get_columns_data(
#     table_name="Employees",
#     columns=["name", "age", "salary"],
#     col_where=col_where,
#     data_type="dataframe"
# )



def insert_data_to_table(table_name, columns_list, values_list):
    try:
        cn = connect_db(server, database, username, pwd)
        cursor = cn.cursor()  # Sử dụng kết nối đã có sẵn

        # Tạo câu lệnh INSERT dựa trên tên bảng và danh sách cột
        columns = "[" + '], ['.join(columns_list) + "]"
        placeholders = ', '.join(['?' for _ in range(len(values_list))])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        # Chèn dữ liệu vào bảng
        cursor.execute(query, values_list)
        cn.commit()  # Xác nhận việc chèn dữ liệu vào bảng
        return "Đã chèn dữ liệu thành công"

    except Exception as e:
        return f"Lỗi: {str(e)}"  # Trả về thông báo lỗi nếu có xảy ra lỗi

# Hàm truy vấn và trả về DataFrame
def query_to_dataframe(query):
    cn = connect_db(server, database, username, pwd)
    # Thực hiện truy vấn
    cursor = cn.cursor()
    cursor.execute(query)
    # Lấy tên cột
    columns = [column[0] for column in cursor.description]
    data = cursor.fetchall()
    # Kiểm tra và chuyển dữ liệu sang tuple nếu cần
    data = [tuple(row) for row in data]

    # Chuyển thành DataFrame
    df = pd.DataFrame(data)

    # Đóng kết nối
    cursor.close()

    return df

def delete_data_from_table_by_ids(table_name, list_ids,nguoisua,thoigiansua, col_where='ID', col_mark='Đã xóa'):
    cn = connect_db(server, database, username, pwd)
    cursor = cn.cursor()

    try:
        # Chuyển danh sách ID thành chuỗi phân cách bằng dấu phẩy
        ids_string ="'" +  "','".join(map(str, list_ids)) + "'"

        # Lệnh SQL để cập nhật cột "Đã xóa" thành 1 cho các dòng có ID trong danh sách
        sql = f"UPDATE {table_name} SET [{col_mark}] = 1, [Người sửa]='{nguoisua}', [Thời gian sửa]='{thoigiansua}' WHERE [{col_where}] IN ({ids_string})"
        cursor.execute(sql)

        cn.commit()
        cn.commit()
        return "Cập nhật dữ liệu thành công!"
    except pyodbc.Error as e:
        cn.rollback()
        return f"Lỗi: {e}"

def convert_date_columns_to_string(dataframe, date_columns):
    df = dataframe.copy()
    for column in date_columns:
        df[column] = df[column].dt.strftime('%Y-%m-%d')
    return df

def update_database_from_dataframe(table_name, dataframe, nguoisua, column_key, date_columns=None):

    try:
        dataframe = dataframe.replace({pd.NA: None, np.nan: None, pd.NaT: None})
        conn = connect_db(server, database, username, pwd)
        cursor = conn.cursor()

        # Kiểm tra xem các cột có tồn tại trong DataFrame hay không trước khi drop
        columns_to_drop = ['Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa','Fullname']

        # Lọc ra các cột tồn tại trong DataFrame
        existing_columns_to_drop = [col for col in columns_to_drop if col in dataframe.columns]
        # Thực hiện drop các cột có trong DataFrame
        if existing_columns_to_drop:
            dataframe = dataframe.drop(columns=existing_columns_to_drop)

        if date_columns is not None:
            dataframe = convert_date_columns_to_string(dataframe, date_columns)

        # Lặp qua từng hàng trong DataFrame để cập nhật thông tin tương ứng trong cơ sở dữ liệu
        for index, row in dataframe.iterrows():
            # Lấy giá trị của cột key từ DataFrame
            key_value = row[column_key]

            # Loại bỏ cột column_key khỏi danh sách cột cần cập nhật
            update_columns = dataframe.drop(columns=[column_key]).columns
            column_names = [f"[{column}]" for column in update_columns]

            sql = f'''
                UPDATE {table_name}
                SET {", ".join([f"{col} = ?" for col in column_names])},
                    [Thời gian sửa] = ?,
                    [Người sửa] = ?
                WHERE [{column_key}] = ?
            '''

            
            # Lấy thông tin từ DataFrame, bỏ cột column_key
            new_info = list(row[update_columns]) + [fn.get_vietnam_time().strftime('%Y-%m-%d %H:%M:%S'), nguoisua, key_value]

            # Thực thi lệnh SQL
            cursor.execute(sql, new_info)

        # Lưu thay đổi và đóng kết nối
        conn.commit()
        conn.close()

        return f"Cập nhật thông tin vào bảng {table_name} thành công"
    except Exception as e:
        # Kiểm tra lỗi vi phạm ràng buộc duy nhất (unique constraint)
        error_str = str(e).lower()
        if '23000' in error_str and ('unique index' in error_str or 'duplicate key' in error_str or 'unique constraint' in error_str):
            return "Lỗi: Dữ liệu bạn vừa nhập bị trùng lặp với một bản ghi đã có. Vui lòng kiểm tra lại."
        return f"Lỗi: {str(e)}"


def get_info(
    df,
    table_name,
    columns_name,
    columns_map,
    columns_key=None,
    columns_output=None,
    columns_position=None,
    where=True
):
    if not all(col in df.columns for col in columns_map):
        missing_cols = [col for col in columns_map if col not in df.columns]
        # st.warning(f"Cột '{', '.join(missing_cols)}' không tồn tại trong DataFrame. Bỏ qua thao tác get_info.")
        return df

    if columns_key is None:
        columns_key = [columns_name[0]]

    col_where_clause = {'Đã xóa': ('=', 0)} if where else None
    
    # Lấy các giá trị duy nhất từ các cột map để tối ưu hóa truy vấn
    unique_values = {}
    for col in columns_map:
        unique_values[col] = df[col].dropna().unique().tolist()

    # Xây dựng điều kiện WHERE phức tạp hơn
    if col_where_clause is None:
        col_where_clause = {}

    for key, map_col in zip(columns_key, columns_map):
        if unique_values[map_col]: # Chỉ thêm điều kiện nếu có giá trị để lọc
            col_where_clause[key] = ('IN', unique_values[map_col])

    df_info = get_columns_data(
        table_name=table_name,
        columns=columns_name,
        col_where=col_where_clause
    )

    if df_info.empty:
        return df

    # Đổi tên cột key trong df_info để khớp với cột map trong df
    rename_dict = {key: map_col for key, map_col in zip(columns_key, columns_map)}
    df_info = df_info.rename(columns=rename_dict)

    # Loại bỏ các dòng trùng lặp trong df_info trước khi merge
    df_info = df_info.drop_duplicates(subset=columns_map)

    # Merge DataFrames
    df_merged = pd.merge(df, df_info, how='left', on=columns_map)

    if columns_output:
        # Tạo dict đổi tên an toàn, chỉ đổi tên các cột tồn tại
        rename_output_dict = {
            old: new
            for old, new in zip(columns_name, columns_output)
            if old in df_merged.columns
        }
        df_merged = df_merged.rename(columns=rename_output_dict)

    if columns_position:
        # Đảm bảo tất cả các cột trong columns_position đều tồn tại
        final_columns = [col for col in columns_position if col in df_merged.columns]
        df_merged = df_merged[final_columns]

    return df_merged
# df = ss.get_info(df=df,table_name='tbsys_ChucNangChinh',columns_name=['ID','Chức năng chính'],
#                          columns_map=['ID Chức năng chính'],columns_key=['ID'], columns_output=['ID','Chức năng chính 1'],columns_position=['Chức năng chính 1', 'ID'])


def insert_data_to_sql_server(table_name, dataframe, created_by=None, delete_old_data=False, delete_by_ids=None, col_where=None):
    try:
        dataframe = dataframe.replace({pd.NA: None, np.nan: None, pd.NaT: None})
        # Kết nối tới SQL Server
        conn = connect_db(server, database, username, pwd)
        cursor = conn.cursor()

        # dataframe=prepare_dataframe_for_sql(df=dataframe,table_name=table_name)
        # Xóa toàn bộ dữ liệu cũ nếu được yêu cầu
        if delete_old_data:
            cursor.execute(f"DELETE FROM {table_name}")
        elif delete_by_ids is not None and col_where:
            ids = ', '.join([str(id_) for id_ in delete_by_ids])

            sql = f"DELETE FROM [{table_name}] WHERE [{col_where}] IN ({ids})"
            cursor.execute(sql)

        # Thêm cột Người tạo vào DataFrame nếu có
        if created_by is not None:
            dataframe['Người tạo'] = created_by

        # Chèn dữ liệu từ DataFrame vào bảng SQL Server
        for _, row in dataframe.iterrows():
            placeholders = ', '.join(['?' for _ in row])
            columns = '], ['.join(dataframe.columns)
            sql = f"INSERT INTO {table_name} ([{columns}]) VALUES ({placeholders})"
            cursor.execute(sql, tuple(row))

        # Lưu các thay đổi
        conn.commit()

        return "Đã cập nhật thành công!"
    except Exception as e:
        return f"Lỗi: {str(e)}"  # Trả về lỗi nếu có


def hashpw(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def get_table_columns(table_name):
    """
    Lấy danh sách tất cả các cột của một bảng hoặc view.
    Sử dụng sp_columns để tăng độ tin cậy.
    """
    cn = connect_db(server, database, username, pwd)
    cursor = cn.cursor()
    try:
        # sp_columns thường đáng tin cậy hơn cho cả bảng và view, và các vấn đề về schema
        cursor.execute(f"EXEC sp_columns @table_name = N'{table_name}'")
        rows = cursor.fetchall()
        if rows:
            # Tên cột nằm ở vị trí thứ 4 (index 3) trong kết quả trả về của sp_columns
            return [row[3] for row in rows]
        return []
    except Exception as e:
        print(f"Lỗi khi lấy danh sách cột cho bảng/view {table_name} bằng sp_columns: {e}")
        # Fallback về INFORMATION_SCHEMA nếu sp_columns thất bại
        try:
            query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'{table_name}' ORDER BY ORDINAL_POSITION"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e2:
            print(f"Lỗi khi lấy danh sách cột cho bảng/view {table_name} bằng INFORMATION_SCHEMA: {e2}")
            return []
    finally:
        if cursor:
            cursor.close()
        if cn:
            cn.close()


def drop_all_filtered_unique_indexes(table_name):
    """Xóa tất cả các filtered unique index (có điều kiện WHERE [Đã xóa] = 0) trên một bảng."""
    sql = f"""
    SELECT name
    FROM sys.indexes
    WHERE object_id = OBJECT_ID('{table_name}')
      AND is_unique = 1
      AND has_filter = 1
      AND filter_definition LIKE N'%[Đã xóa]%=%(0)%';
    """
    indexes_to_drop = query_database_sqlite(sql, data_type='list', delimiter=',')
    if not indexes_to_drop:
        return []
    dropped = []
    for idx_name in indexes_to_drop:
        drop_sql = f"DROP INDEX [{idx_name}] ON [{table_name}];"
        result = query_database_sqlite(drop_sql, data_type=None)
        if result is not None:
            dropped.append(idx_name)
    return dropped


def drop_old_unique_constraints_and_computed_columns(table_name):
    """
    Xóa các UNIQUE constraint cũ và computed columns (_UQ_CHECK_...) từ logic cũ.
    Đây là để tương thích với các bảng đã tạo trước đây sử dụng computed columns.
    """
    try:
        # 1. Lấy danh sách các constraint UNIQUE
        constraint_sql = f"""
        SELECT c.name AS constraint_name
        FROM sys.key_constraints c
        WHERE c.type = 'UQ' 
        AND c.parent_object_id = OBJECT_ID('{table_name}')
        """
        constraints = query_database_sqlite(constraint_sql, data_type='list', delimiter=',')
        
        # Xóa từng constraint
        for constraint_name in constraints:
            drop_constraint_sql = f"ALTER TABLE [{table_name}] DROP CONSTRAINT [{constraint_name}];"
            query_database_sqlite(drop_constraint_sql, data_type=None)
        
        # 2. Lấy danh sách các computed columns bắt đầu với _UQ_CHECK_
        computed_col_sql = f"""
        SELECT name
        FROM sys.columns
        WHERE object_id = OBJECT_ID('{table_name}')
        AND is_computed = 1
        AND name LIKE '_UQ_CHECK_%'
        """
        computed_cols = query_database_sqlite(computed_col_sql, data_type='list', delimiter=',')
        
        # Xóa từng computed column
        for col_name in computed_cols:
            drop_col_sql = f"ALTER TABLE [{table_name}] DROP COLUMN [{col_name}];"
            query_database_sqlite(drop_col_sql, data_type=None)
        
        return {
            'constraints_dropped': constraints,
            'computed_columns_dropped': computed_cols
        }
    except Exception as e:
        print(f"Warning: Error cleaning old unique constraints: {e}")
        return {'constraints_dropped': [], 'computed_columns_dropped': []}


def get_table_columns_info(table_name):
    """
    Lấy thông tin các cột của bảng (name, type, max_length, is_nullable, is_identity)
    Bao gồm cả cột ID, không bao gồm các cột hệ thống khác và cột computed.
    """
    cn = connect_db(server, database, username, pwd)
    system_columns = "('Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa')"
    sql = f"""
        SELECT
            c.COLUMN_NAME AS name,
            CASE
                WHEN c.DATA_TYPE LIKE '%char' AND c.CHARACTER_MAXIMUM_LENGTH = -1 THEN UPPER(c.DATA_TYPE) + '(MAX)'
                WHEN c.DATA_TYPE LIKE '%char' THEN UPPER(c.DATA_TYPE) + '(n)'
                ELSE UPPER(c.DATA_TYPE)
            END AS type,
            c.CHARACTER_MAXIMUM_LENGTH AS max_length,
            CASE
                WHEN c.IS_NULLABLE = 'YES' THEN 1
                ELSE 0
            END AS is_nullable,
            CASE
                WHEN sc.is_identity = 1 THEN 1
                ELSE 0
            END AS is_identity
        FROM
            INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN sys.columns sc ON sc.object_id = OBJECT_ID('{table_name}') AND sc.name = c.COLUMN_NAME
        WHERE
            c.TABLE_NAME = N'{table_name}' 
            AND c.COLUMN_NAME NOT IN {system_columns}
            AND (sc.is_computed IS NULL OR sc.is_computed = 0)
            AND c.COLUMN_NAME NOT LIKE '_UQ_CHECK_%'
        ORDER BY
            c.ORDINAL_POSITION;
    """
    cursor = cn.cursor()
    cursor.execute(sql)
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    results = [dict(zip(columns, row)) for row in rows]
    cursor.close()
    cn.close()
    return results


def get_filtered_unique_index_info(table_name):
    """
    Lấy danh sách các cột tham gia vào filtered unique index (có điều kiện Đã xóa = 0) của một bảng.
    """
    sql = f"""
    SELECT
        c.name AS column_name
    FROM sys.indexes AS i
    INNER JOIN sys.index_columns AS ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    INNER JOIN sys.columns AS c ON ic.object_id = c.object_id AND c.column_id = ic.column_id
    WHERE
        i.object_id = OBJECT_ID('{table_name}')
        AND i.is_unique = 1
        AND i.has_filter = 1
        AND i.filter_definition LIKE N'%[Đã xóa]%=%(0)%';
    """
    df = query_database_sqlite(sql, data_type='dataframe')
    if df is not None and not df.empty:
        return df['column_name'].tolist()
    return []


def generate_filtered_index_query(table_name, columns):
    """
    Tạo câu lệnh CREATE UNIQUE FILTERED INDEX cho danh sách các cột.
    """
    if not table_name or not columns:
        return ""
    column_names_str = '_'.join(columns)
    index_name = f"IX_UQ_{table_name}_{column_names_str}"
    column_list = ', '.join([f"[{col}]" for col in columns])
    query = f"""
CREATE UNIQUE INDEX [{index_name}]
ON [{table_name}] ({column_list})
WHERE [Đã xóa] = 0;
    """
    return query.strip()


def generate_alter_table_queries(table_name, df_new, df_old):
    """
    So sánh cấu trúc bảng cũ (df_old) và mới (df_new), tạo ra danh sách các câu lệnh ALTER TABLE.
    df_new: DataFrame từ data_editor với các cột: Tên trường, Kiểu dữ liệu, n, Not Null, ...
    df_old: DataFrame từ get_table_columns_info với các cột: name, type, max_length, is_nullable
    """
    queries = []
    
    # Kiểm tra df_new có cột 'Tên trường'
    if df_new.empty or 'Tên trường' not in df_new.columns:
        return queries
    
    # Kiểm tra df_old có cột 'name'
    if df_old.empty or 'name' not in df_old.columns:
        # Nếu df_old empty, coi như tất cả các cột trong df_new là cột mới cần thêm
        for index, row in df_new.iterrows():
            if row['Tên trường'] and row['Kiểu dữ liệu']:
                field_name = f"[{row['Tên trường']}]"
                data_type = row['Kiểu dữ liệu']
                
                if "(n)" in data_type:
                    n_value = row.get("n (Mặc định n=50)", 50)
                    if pd.isna(n_value) or not isinstance(n_value, (int, float)) or n_value <= 0:
                        n_value = 50
                    data_type = str(data_type).replace('(n)', f'({int(n_value)})')
                
                is_auto_increment = row.get('Auto Increment', False)
                if is_auto_increment and data_type.upper() in ['INT', 'BIGINT', 'SMALLINT', 'TINYINT']:
                    data_type += " IDENTITY(1,1) PRIMARY KEY"
                    queries.append(f"ALTER TABLE [{table_name}] ADD {field_name} {data_type};")
                else:
                    not_null = "NOT NULL" if row.get('Not Null') else "NULL"
                    queries.append(f"ALTER TABLE [{table_name}] ADD {field_name} {data_type} {not_null};")
        return queries
    
    df_new = df_new.set_index('Tên trường')
    df_old = df_old.set_index('name')

    # --- 1. Cột cần thêm ---
    new_cols = df_new.index.difference(df_old.index)
    for col_name in new_cols:
        row = df_new.loc[col_name]
        data_type = row['Kiểu dữ liệu']
        if "(n)" in data_type:
            n_value = row.get("n (Mặc định n=50)", 50)
            if pd.isna(n_value) or not isinstance(n_value, (int, float)) or n_value <= 0:
                n_value = 50
            data_type = str(data_type).replace('(n)', f'({int(n_value)})')
        
        # Kiểm tra Auto Increment
        is_auto_increment = row.get('Auto Increment', False)
        if is_auto_increment and data_type.upper() in ['INT', 'BIGINT', 'SMALLINT', 'TINYINT']:
            data_type += " IDENTITY(1,1) PRIMARY KEY"
            queries.append(f"ALTER TABLE [{table_name}] ADD [{col_name}] {data_type};")
        else:
            not_null = "NOT NULL" if row.get('Not Null') else "NULL"
            queries.append(f"ALTER TABLE [{table_name}] ADD [{col_name}] {data_type} {not_null};")

    # --- 2. Cột cần xóa ---
    dropped_cols = df_old.index.difference(df_new.index)
    for col_name in dropped_cols:
        queries.append(f"ALTER TABLE [{table_name}] DROP COLUMN [{col_name}];")

    # --- 3. Cột cần sửa ---
    common_cols = df_new.index.intersection(df_old.index)
    for col_name in common_cols:
        new_row = df_new.loc[col_name]
        old_row = df_old.loc[col_name]

        # Kiểm tra thay đổi Auto Increment (IDENTITY)
        old_is_identity = old_row.get('is_identity', 0)
        new_is_identity = new_row.get('Auto Increment', False)
        
        if old_is_identity != new_is_identity:
            # SQL Server không cho phép ALTER COLUMN để thêm/bỏ IDENTITY
            if new_is_identity:
                queries.append(f"-- CẢNH BÁO: Không thể thêm IDENTITY cho cột [{col_name}] đã tồn tại.")
                queries.append(f"-- Bạn cần xóa cột rồi tạo lại (sẽ mất dữ liệu).")
            else:
                queries.append(f"-- CẢNH BÁO: Không thể bỏ IDENTITY khỏi cột [{col_name}].")
                queries.append(f"-- Bạn cần xóa cột rồi tạo lại (sẽ mất dữ liệu).")
            continue  # Bỏ qua thay đổi khác cho cột này

        # Lấy thuộc tính mới từ df_new (giao diện người dùng)
        new_type = new_row['Kiểu dữ liệu']
        if "(n)" in new_type:
            n_value = new_row.get("n (Mặc định n=50)", 50)
            if pd.isna(n_value) or not isinstance(n_value, (int, float)) or n_value <= 0:
                n_value = 50
            new_type = str(new_type).replace('(n)', f'({int(n_value)})')
        new_not_null_str = "NOT NULL" if new_row.get('Not Null') else "NULL"

        # Lấy thuộc tính cũ từ df_old (cơ sở dữ liệu)
        old_type = old_row['type']
        if "(n)" in old_type and 'max_length' in old_row and old_row['max_length'] != -1:
            old_type = str(old_type).replace('(n)', f"({old_row['max_length']})")
        elif "(n)" in old_type: # Xử lý cho nvarchar(max)
            old_type = str(old_type).replace('(n)', '(MAX)')

        # 'is_nullable' từ get_table_columns_info: 1 là CÓ THỂ NULL, 0 là NOT NULL
        old_not_null_str = "NULL" if old_row.get('is_nullable') == 1 else "NOT NULL"

        # So sánh và tạo truy vấn nếu có sự thay đổi
        if new_type.upper() != old_type.upper() or new_not_null_str != old_not_null_str:
            queries.append(f"ALTER TABLE [{table_name}] ALTER COLUMN [{col_name}] {new_type} {new_not_null_str};")

    return queries


def get_table_structure(table_name):
    """
    Lấy đầy đủ thông tin về cấu trúc bảng để có thể tái tạo hoặc chỉnh sửa.
    Trả về DataFrame với các cột: Tên trường, Kiểu dữ liệu, n (Mặc định n=50),
    Unique (Đã xóa = 0), Not Null, Mặc định, DEFAULT_CONSTRAINT_NAME
    """
    import pandas as pd
    
    # Bỏ qua các cột mặc định của hệ thống
    system_columns = ['Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa']
    
    query = f"""
    SELECT
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.IS_NULLABLE,
        c.COLUMN_DEFAULT,
        dc.name AS DEFAULT_CONSTRAINT_NAME
    FROM INFORMATION_SCHEMA.COLUMNS c
    LEFT JOIN sys.columns sc ON sc.object_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME) AND sc.name = c.COLUMN_NAME
    LEFT JOIN sys.default_constraints dc ON dc.parent_object_id = sc.object_id AND dc.parent_column_id = sc.column_id
    WHERE c.TABLE_NAME = N'{table_name}'
    AND c.COLUMN_NAME NOT IN ('Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa')
    ORDER BY c.ORDINAL_POSITION
    """
    
    result = query_database_sqlite(query, data_type='dataframe')
    
    if result is None or result.empty:
        return pd.DataFrame(columns=['Tên trường', 'Kiểu dữ liệu', 'n (Mặc định n=50)',
                                     'Unique (Đã xóa = 0)', 'Not Null', 'Mặc định', 'DEFAULT_CONSTRAINT_NAME'])
    
    # Lấy thông tin về các filtered unique indexes
    unique_query = f"""
    SELECT DISTINCT
        COL_NAME(ic.object_id, ic.column_id) AS COLUMN_NAME
    FROM sys.indexes i
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    WHERE i.is_unique = 1
    AND i.has_filter = 1
    AND OBJECT_NAME(i.object_id) = N'{table_name}'
    """
    
    unique_columns = []
    try:
        unique_result = query_database_sqlite(unique_query, data_type='dataframe')
        if unique_result is not None and not unique_result.empty:
            unique_columns = unique_result['COLUMN_NAME'].tolist()
    except Exception as e:
        pass
    
    # Chuyển đổi thông tin
    data = []
    for _, row in result.iterrows():
        col_name = row['COLUMN_NAME']
        data_type = row['DATA_TYPE'].upper()
        max_length = row['CHARACTER_MAXIMUM_LENGTH']
        is_nullable = row['IS_NULLABLE']
        default_val = row['COLUMN_DEFAULT']
        default_constraint_name = row['DEFAULT_CONSTRAINT_NAME']
        
        # Xử lý kiểu dữ liệu
        if data_type in ['CHAR', 'VARCHAR', 'NVARCHAR']:
            if max_length == -1:
                formatted_type = f"{data_type}(MAX)"
                n_value = 50
            else:
                formatted_type = f"{data_type}(n)"
                n_value = max_length if max_length else 50
        else:
            formatted_type = data_type
            n_value = 50
        
        # Xử lý NOT NULL
        not_null = 0 if is_nullable == 'YES' else 1
        
        # Xử lý giá trị mặc định
        if default_val:
            # Loại bỏ dấu ngoặc đơn và các ký tự đặc biệt
            default_val = str(default_val).strip("()").strip("'")
            if default_val.upper() == 'GETDATE':
                default_val = 'CURRENT_TIMESTAMP'
        else:
            default_val = "0"
        
        # Kiểm tra unique
        is_unique = 1 if col_name in unique_columns else 0
        
        data.append({
            'Tên trường': col_name,
            'Kiểu dữ liệu': formatted_type,
            'n (Mặc định n=50)': int(n_value),
            'Unique (Đã xóa = 0)': int(is_unique),
            'Not Null': int(not_null),
            'Mặc định': default_val,
            'DEFAULT_CONSTRAINT_NAME': default_constraint_name
        })
    
    return pd.DataFrame(data)

