import streamlit as st
import admin.sys_sqlite as ss
import pandas as pd
from . import sys_functions as fn
from admin.sys_kde_components import *

def app(selected_tab):
    st.header(f"Cấu hình liên kết Module chức năng")

    # Lấy danh sách chức năng con và các liên kết hiện có
    sql_chucnang = """
        SELECT 
            DSCN.ID as ID_DanhSachChucNang, 
            CNC.[Chức năng chính], 
            DSCN.[Chức năng con],
            LKM.ModulePath,
            LKM.[Ghi chú]
        FROM tbsys_DanhSachChucNang as DSCN
        LEFT JOIN tbsys_ChucNangChinh as CNC ON DSCN.[ID Chức năng chính] = CNC.ID AND CNC.[Đã xóa] = 0
        LEFT JOIN tbsys_ModuleChucNang as LKM ON DSCN.ID = LKM.ID_DanhSachChucNang AND LKM.[Đã xóa] = 0
        WHERE DSCN.[Đã xóa] = 0 
        ORDER BY CNC.[Thứ tự ưu tiên] ASC, DSCN.[Thứ tự ưu tiên] ASC
    """
    try:
        df_chucnang = ss.query_database_sqlite(sql_chucnang, data_type='dataframe')
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        df_chucnang = pd.DataFrame()

    if isinstance(df_chucnang, pd.DataFrame) and not df_chucnang.empty:
        
        # Lấy danh sách module path có sẵn trong project
        available_modules = fn.get_module_paths()
        st.info("Chỉnh sửa trực tiếp đường dẫn module trong cột 'ModulePath' bên dưới và nhấn 'Lưu thay đổi'.")
        
        # Sử dụng data_editor để cho phép chỉnh sửa
        edited_df = st.data_editor(
            df_chucnang,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "Chức năng chính": st.column_config.TextColumn("Chức năng chính", disabled=True),
                "Chức năng con": st.column_config.TextColumn("Chức năng con", disabled=True),
                "ModulePath": st.column_config.SelectboxColumn(
                    "ModulePath",
                    help="Chọn đường dẫn module tương ứng",
                    options=available_modules,
                    required=False, # Cho phép để trống
                ),
                'Ghi chú': st.column_config.TextColumn("Ghi chú", required=False)
            },
            width='content',
            hide_index=True,
            key="module_editor"
        )
        df_luu = edited_df[['ID_DanhSachChucNang', 'ModulePath', 'Ghi chú']].copy()
        df_luu['Người tạo'] = st.session_state.username
        df_luu['Thời gian tạo'] = fn.get_vietnam_time().strftime('%Y-%m-%d %H:%M:%S')
        if st.button("Lưu thay đổi", type='primary'):
            result = ss.insert_data_to_sql_server(table_name='tbsys_ModuleChucNang', dataframe=df_luu, delete_old_data=True)
            show_notification("Lỗi:", result)
    else:
        st.warning("Không tìm thấy danh sách chức năng nào.")

    # Quản lý sửa/xóa liên kết module bằng dataframe_with_selections
    st.subheader('Quản lý liên kết module chức năng (sửa/xóa)')
    columns_module = ['ID',  'ModulePath', 'Ghi chú', 'Người tạo', 'Thời gian tạo']
    joins = [
        {
            'table': 'tbsys_DanhSachChucNang',
            'alias': 'DSCN',
            'on': {'ID_DanhSachChucNang': 'ID'},
            'columns': ['Chức năng con', 'ID Chức năng chính']
        },
        {
            'from_table': 'DSCN',
            'table': 'tbsys_ChucNangChinh',
            'alias': 'CNC',
            'on': {'ID Chức năng chính': 'ID'},
            'columns': ['Chức năng chính']
        }
    ]
    dataframe_with_selections(
        table_name='tbsys_ModuleChucNang',
        columns=columns_module,
        col_where={'Đã xóa': ('=', 0)},
        col_order={'ID': 'DESC'},
        title='Danh sách liên kết module',
        select_all=True,
        download=True,
        key='module_links',
        colums_disable=['ID'],
        joins=joins
    )