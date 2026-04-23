import streamlit as st
from streamlit_option_menu import option_menu
from admin.sys_functions import *
import streamlit_antd_components as sac
from admin.sys_kde_components import *
import admin.sys_sqlite as ss
from admin import app_config as config

page_icon="images/logo.png"
image_logo = "images/Logo_Sidebar.png"
# Thiết lập trang
st.set_page_config(page_title="KD Educode", page_icon=page_icon, layout="wide")

# Login
# lấy toàn bộ danh sách
df_users = ss.get_columns_data(table_name='tbsys_Users',columns=['Username','Password','Fullname'],col_where={'Đã xóa':('=',0)})
import streamlit_authenticator as stauth
# Tạo
credentials = {
    'usernames': {}
}

for i in range(len(df_users)):
    credentials["usernames"][df_users.loc[i, "Username"]] = {
        "name": df_users.loc[i, "Fullname"],
        "username": df_users.loc[i, "Username"],
        "password": df_users.loc[i, "Password"]
    }

# Xác thưc người dùng
authenticator = stauth.Authenticate(credentials,cookie_name= fn.get_project_folder(), cookie_key= fn.get_project_folder() + 'key', cookie_expiry_days=30)

if not 'authenticator' in st.session_state:
    st.session_state['authenticator'] = authenticator
if not 'credentials' in st.session_state:
    st.session_state['credentials'] = credentials

# name, authentication_status, username = authenticator.login("Login", "main")
name, authentication_status, username = authenticator.login(location='main')

username=str(username).lower()


if "username" not in st.session_state:
    st.session_state["username"] = username
if "fullname" not in st.session_state:
    st.session_state["fullname"] = name

if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = authentication_status

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

# Kêt thúc đăng nhập---------------------------------------------------------------------------------------------------------
if 'index' not in st.session_state:
    st.session_state.index = 0
if "form_key" not in st.session_state:
    st.session_state.form_key = fn.get_timestamp(True)
if "df_key" not in st.session_state:
    st.session_state.df_key = 0

# nếu login thành công thì load chức năng tương ứng theo Username
if authentication_status:
    hide_header_streamlit()
    
    # Custom CSS for larger, bolder, colorful tables + narrow sidebar
    st.markdown("""
    <style>
    /* Thu nhỏ sidebar để bảng dữ liệu rộng hơn */
    [data-testid="stSidebar"] {
        min-width: 220px !important;
        max-width: 220px !important;
        width: 220px !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        width: 220px !important;
        padding: 10px !important;
    }
    
    /* Thu nhỏ font trong sidebar menu */
    [data-testid="stSidebar"] .nav-link {
        font-size: 13px !important;
        padding: 8px 10px !important;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-size: 14px !important;
    }
    
    /* Tăng kích thước chữ trong bảng dữ liệu - 200% */
    div[data-testid="stDataFrame"] table {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stDataFrame"] th {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        background-color: #1f4e79 !important;
        color: white !important;
        padding: 12px 8px !important;
    }
    
    div[data-testid="stDataFrame"] td {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        padding: 10px 8px !important;
    }
    
    /* Alternating row colors */
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) {
        background-color: #f0f7ff !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:nth-child(odd) {
        background-color: #ffffff !important;
    }
    
    /* Hover effect */
    div[data-testid="stDataFrame"] tbody tr:hover {
        background-color: #e3f2fd !important;
    }
    
    /* Data editor styling */
    div[data-testid="stDataFrame"] [data-testid="glideDataEditor"] {
        font-size: 1.1rem !important;
    }
    
    /* Header text styling */
    .stDataFrame [data-testid="column-header"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if 'save_database' not in st.session_state:
        st.session_state.save_database = False
    id_chucnangs = []
    try:
        # st.session_state.mavaitro = sp.execute_sql()[0][0]
        sql =  f"SELECT [ID_VaiTro] from [tbsys_Users] where [Username] = '{st.session_state.username}'"
        mavaitro = ss.query_database_sqlite(sql_string=sql,data_type='value')
        st.session_state.mavaitro=mavaitro

        if mavaitro not in ['1', '2']:  # thuoc cap quan ly
            st.session_state.vaitro = 'quanly'
        else:
            st.session_state.vaitro = 'nhanvien'

        # st.write(f'Mã vai trò: {mavaitro}. Loại vai trò: {st.session_state.loaivaitro }')
        vaitro = ss.get_columns_data(table_name='tbsys_Users', columns=['ID_VaiTro'], delimiter='', data_type='list',
                                      col_where={'Username':('=',st.session_state.username)})[0]
        
        id_chucnangs = ss.get_columns_data('tbsys_ChucNangTheoVaiTro', columns=['ID Danh sách chức năng'],
                                           col_where={'ID Vai trò':('=',vaitro)})

        df_chucnangvaitro = ss.get_columns_data(table_name='tbsys_ChucNangTheoVaiTro', columns=['ID Vai trò', 'ID Danh sách chức năng'],
                                                data_type='dataframe', col_where={'Đã xóa': ('=', 0),'ID Vai trò':('=',vaitro)})
        if len(df_chucnangvaitro):
            df = ss.get_info(df_chucnangvaitro, table_name='tbsys_VaiTro', columns_name=['ID', 'Vai trò'],
                             columns_map=['ID Vai trò'], columns_key=['ID'])
            df = ss.get_info(df, table_name='tbsys_DanhSachChucNang', columns_name=['ID', 'ID Chức năng chính', 'Chức năng con','Thứ tự ưu tiên'],
                             columns_map=['ID Danh sách chức năng'], columns_key=['ID'],
                             columns_output=['ID','ID Chức năng chính','Chức năng con','Thứ tự ưu tiên con'],
                             columns_position=['ID Chức năng chính','Chức năng con','Thứ tự ưu tiên con'])

            df_chucnangs = ss.get_info(df, table_name='tbsys_ChucNangChinh', columns_name=['ID', 'Chức năng chính','Thứ tự ưu tiên','Icon'],
                             columns_map=['ID Chức năng chính'], columns_key=['ID'],
                             columns_position=['ID Chức năng chính', 'Chức năng chính','Thứ tự ưu tiên', 'Chức năng con','Thứ tự ưu tiên con','Icon'])
            df_chucnangs = df_chucnangs.sort_values(by=['Thứ tự ưu tiên', 'Thứ tự ưu tiên con'], ascending=[True, True])
    except Exception as e:
        # Ném lại lỗi để Streamlit có thể bắt và hiển thị đầy đủ
        raise e
    if len(df_chucnangs):
        df_chucnangchinhs = df_chucnangs[['Chức năng chính', 'Thứ tự ưu tiên','Icon']].drop_duplicates(subset='Chức năng chính').sort_values('Thứ tự ưu tiên')
        chucnangs = df_chucnangchinhs['Chức năng chính'].tolist()
        icon_list=df_chucnangchinhs['Icon'].tolist()
        
        # Khởi tạo bảng config và lấy các giá trị cấu hình
        config.create_config_table()
        project_name = config.get_config('project_name', 'Quản lý Máy Đo')
        style_config = {
            "container_bg": config.get_config("style_container_bg", "#2E3440"),
            "icon_color": config.get_config("style_icon_color", "#88C0D0"),
            "icon_font_size": config.get_config("style_icon_font_size", "22px"),
            "nav_link_font_size": config.get_config("style_nav_link_font_size", "16px"),
            "nav_link_color": config.get_config("style_nav_link_color", "#ECEFF4"),
            "nav_link_hover_color": config.get_config("style_nav_link_hover_color", "#4C566A"),
            "nav_link_selected_bg": config.get_config("style_nav_link_selected_bg", "#81A1C1"),
            "nav_link_selected_color": config.get_config("style_nav_link_selected_color", "#2E3440"),
            "menu_icon": config.get_config("style_menu_icon", "clipboard-data"),
            "font_family": config.get_config("style_font_family", "sans-serif"),
        }

        with st.sidebar:
            if username=='phinho' or username=='kde':
                chucnangs.append('Admin KDE')
                icon_list.append('person-gear')
            import math
            chucnangs = [x for x in chucnangs if x is not None and not (isinstance(x, float) and math.isnan(x))]
            icon_list = [x for x in icon_list if x is not None and not (isinstance(x, float) and math.isnan(x))]

            choose = option_menu(
                project_name, chucnangs,
                menu_icon=style_config["menu_icon"],
                styles={
                    "container": {"padding": "5!important", "background-color": style_config["container_bg"]},
                    "icon": {"color": style_config["icon_color"], "font-size": style_config["icon_font_size"]},
                    "nav-link": {
                        "font-size": style_config["nav_link_font_size"],
                        "text-align": "left",
                        "color": style_config["nav_link_color"],
                        "margin": "0px",
                        "--hover-color": style_config["nav_link_hover_color"],
                        "font-family": style_config["font_family"],
                    },
                    "nav-link-selected": {
                        "background-color": style_config["nav_link_selected_bg"],
                        "color": style_config["nav_link_selected_color"],
                    }
                }, key='choose_', icons=icon_list
            )
        
            st.markdown(f'# Xin chào: {name} ({username})')
            authenticator.logout('Đăng xuất')

        tabs = df_chucnangs[df_chucnangs['Chức năng chính']==choose]['Chức năng con'].tolist()

        admin_tabs = ['Tạo bảng','Thêm users','Vai trò','Chức năng chính','Danh sách chức năng','Chức năng theo vai trò','Liên kết Module','Cài đặt','Clear Data Table','Cấu trúc SQL',"Download Database",'Backup Database']
        if (username == 'phinho' or username == 'kde') and choose == 'Admin KDE':
            for tab in admin_tabs:
                tabs.append(tab)
        
        # Tạo danh sách các SegmentedItem từ danh sách tabs
        segmented_items = [sac.SegmentedItem(label=tab) for tab in tabs]
        # Tạo Segmented control từ các mục SegmentedItem đã tạo
        selected_tab = sac.segmented(items=segmented_items, align='center', index=0)

        import importlib
        from admin import sys_QuanLyNguoiDung, sys_VaiTro,sys_ChucNangTheoVaiTro,sys_TaoBang, sys_ChucNangChinh, sys_DanhSachChucNang, sys_LienKetModule, sys_Settings
        try:
            from admin import sys_LuuGoogleDrive, sys_KhoiPhucDatabase, sys_ClearDataTable, sys_SQLStructure, sys_DownloadDatabase, sys_BackupDatabase
        except ImportError:
            sys_LuuGoogleDrive = sys_KhoiPhucDatabase = sys_ClearDataTable = sys_SQLStructure = sys_DownloadDatabase = sys_BackupDatabase = None

        if choose == 'Admin KDE':
            if selected_tab =="Tạo bảng":
                sys_TaoBang.app(selected_tab)
            elif selected_tab=='Thêm users':
                sys_QuanLyNguoiDung.app(selected_tab)
            elif selected_tab=='Vai trò':
                sys_VaiTro.app(selected_tab)
            elif selected_tab == 'Chức năng chính':
                sys_ChucNangChinh.app(selected_tab)
            elif selected_tab == 'Danh sách chức năng':
                sys_DanhSachChucNang.app(selected_tab)
            elif selected_tab=='Chức năng theo vai trò':
                sys_ChucNangTheoVaiTro.app(selected_tab)
            elif selected_tab == 'Liên kết Module':
                sys_LienKetModule.app(selected_tab)
            elif selected_tab == 'Cài đặt':
                sys_Settings.app(selected_tab)
            elif selected_tab == 'Clear Data Table':
                if sys_ClearDataTable: sys_ClearDataTable.app(selected_tab)
                else: st.warning('Chức năng này không khả dụng trên Cloud.')
            elif selected_tab == "Cấu trúc SQL":
                if sys_SQLStructure: sys_SQLStructure.app(selected_tab)
                else: st.warning('Chức năng này không khả dụng trên Cloud.')
            elif selected_tab == "Download Database":
                if sys_DownloadDatabase: sys_DownloadDatabase.app(selected_tab)
                else: st.warning('Chức năng này không khả dụng trên Cloud.')
            elif selected_tab == 'Backup Database':
                if sys_BackupDatabase: sys_BackupDatabase.app(selected_tab)
                else: st.warning('Chức năng này không khả dụng trên Cloud.')
            elif selected_tab == 'Lưu vào Google Drive':
                if sys_LuuGoogleDrive: sys_LuuGoogleDrive.app(selected_tab)
                else: st.warning('Chức năng này không khả dụng trên Cloud.')
            elif selected_tab == 'Khôi phục Database':
                if sys_KhoiPhucDatabase: sys_KhoiPhucDatabase.app(selected_tab)
                else: st.warning('Chức năng này không khả dụng trên Cloud.')
        else:
            # Cơ chế động cho các chức năng khác
            sql_get_module = f"""
                SELECT T2.[ModulePath]
                FROM [tbsys_DanhSachChucNang] AS T1
                LEFT JOIN [tbsys_ModuleChucNang] AS T2 ON T1.[ID] = T2.[ID_DanhSachChucNang] AND T2.[Đã xóa] = 0
                WHERE TRIM(T1.[Chức năng con]) = '{selected_tab.strip()}' AND T1.[Đã xóa] = 0
                ORDER BY T2.[ModulePath] DESC
                LIMIT 1
            """
            module_path = ss.query_database_sqlite(sql_string=sql_get_module, data_type='value')
            
            if module_path and isinstance(module_path, str) and module_path.strip():
                page_module = importlib.import_module(module_path)
                page_module.app(selected_tab)
            else:
                st.warning(f"Chức năng '{selected_tab}' chưa được liên kết với module nào. Vui lòng vào 'Admin KDE' -> 'Liên kết Module' để cấu hình.")

    else:
        st.header("Bạn chưa có quyền truy cập tính năng của ứng dụng. Vui lòng liên hệ người quản lý!")

    
else:
    st.session_state.index = 0