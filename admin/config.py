import admin.sys_sqlite as ss
import pandas as pd

TABLE_NAME = 'tbsys_config'

DEFAULT_CONFIGS = {
    "project_name": "Quản lý Máy Đo Hoàng Long",
    "style_container_bg": "#2E3440",
    "style_icon_color": "#88C0D0",
    "style_icon_font_size": "22px",
    "style_nav_link_font_size": "16px",
    "style_nav_link_color": "#ECEFF4",
    "style_nav_link_hover_color": "#4C566A",
    "style_nav_link_selected_bg": "#81A1C1",
    "style_nav_link_selected_color": "#2E3440",
    "style_menu_icon": "clipboard-data",
    "style_font_family": "sans-serif",
}

def create_config_table():
    """
    Kiểm tra xem bảng config có tồn tại không. Nếu không, tạo bảng và chèn các giá trị mặc định.
    """
    try:
        # Kiểm tra sự tồn tại của bảng
        check_table_sql = "SELECT name FROM sqlite_master WHERE type='table' AND name = ?"
        table_exists = ss.query_database_sqlite(check_table_sql, params=(TABLE_NAME,), data_type='value')

        if not table_exists:
            print(f"Bảng '{TABLE_NAME}' không tồn tại. Đang tạo bảng...")
            # Tạo bảng
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                config_key TEXT PRIMARY KEY,
                config_value TEXT
            )
            """
            ss.query_database_sqlite(create_table_sql)
            
            # Chèn các giá trị mặc định
            print("Đang chèn các giá trị cấu hình mặc định...")
            for key, value in DEFAULT_CONFIGS.items():
                set_config(key, value)
            print("Tạo và khởi tạo bảng cấu hình thành công.")
            
        return True
    except Exception as e:
        print(f"Lỗi nghiêm trọng trong quá trình khởi tạo bảng cấu hình: {e}")
        return False

def get_all_configs():
    """
    Lấy tất cả các cặp key-value từ bảng cấu hình và trả về dưới dạng dictionary.
    """
    try:
        df = ss.get_columns_data(
            table_name=TABLE_NAME,
            columns=['config_key', 'config_value']
        )
        if df.empty:
            return {}
        # Chuyển DataFrame thành dictionary
        return pd.Series(df.config_value.values, index=df.config_key).to_dict()
    except Exception as e:
        print(f"Lỗi khi lấy tất cả cấu hình: {e}")
        return {}

def get_config(key, default=None):
    """
    Lấy một giá trị cấu hình cụ thể từ database bằng key.
    """
    try:
        # Đầu tiên thử lấy tất cả config để tận dụng cache nếu có
        all_configs = get_all_configs()
        if key in all_configs:
            return all_configs[key]
        
        # Nếu không có, và có giá trị mặc định, thì set nó
        if default is not None:
            set_config(key, default)
            return default
            
        return None
    except Exception as e:
        print(f"Lỗi khi lấy cấu hình '{key}': {e}")
        return default

def set_config(key, value):
    """
    Thiết lập (thêm mới hoặc cập nhật) một giá trị cấu hình trong database.
    """
    try:
        # Kiểm tra xem key đã tồn tại chưa
        existing_value = ss.query_database_sqlite(
            sql_string=f"SELECT config_value FROM {TABLE_NAME} WHERE config_key = ?",
            params=(key,),
            data_type='value'
        )

        if existing_value is not None:
            # Nếu tồn tại, thực hiện UPDATE
            sql = f"UPDATE {TABLE_NAME} SET config_value = ? WHERE config_key = ?"
            params = (value, key)
        else:
            # Nếu không tồn tại, thực hiện INSERT
            sql = f"INSERT INTO {TABLE_NAME} (config_key, config_value) VALUES (?, ?)"
            params = (key, value)
        
        result = ss.query_database_sqlite(sql_string=sql, params=params)
        return "thành công" in result.lower()
    except Exception as e:
        print(f"Lỗi khi thiết lập cấu hình '{key}': {e}")
        return False