import streamlit as st
from admin.sys_kde_components import *
import time
from datetime import datetime
import admin.sys_sqlite as ss
def app(selected):
    table_name="tbsys_VaiTro"
    name = "vai trò"
    col_name =f'Vai trò'


    c1, c2 = st.columns([1,3])
    with c1:
        st.header(f'Thêm {name}')

        ten = st.text_input(col_name)
        thutu = st.number_input('Thứ tự ưu tiên',min_value=1, max_value=1000000)
        disabled = not (len(ten) > 0)
        them = st.button(f'Thêm {name}', disabled=disabled)
        if them:
            # Sử dụng hàm insert_data_to_table để chèn dữ liệu vào bảng Xuong
            columns = [col_name, 'Thứ tự ưu tiên','Người tạo','Thời gian tạo']
            values = [ten, thutu, st.session_state.username,fn.get_vietnam_time()]

            result = ss.insert_data_to_table(table_name,columns_list=columns,values_list=values)
            if "Lỗi:" in result:
                st.error(result)
            else:
                st.success(result)
    with c2:
        st.header(f'Danh sách {name} hiện tại')
        columns = ['ID', col_name, 'Thứ tự ưu tiên', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa']
        search_columns = [col_name]
        dataframe_with_selections(
            table_name=table_name,
            columns=columns,
            search_columns=search_columns,
            col_where={'Đã xóa': ('=', 0)},
            col_order={'ID': 'DESC'},
            key=f'{table_name}_{st.session_state.df_key}',
            join_user_info=True,
            colums_disable=['ID', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa', 'Fullname'],
            download=True,
            select_all=True
        )

