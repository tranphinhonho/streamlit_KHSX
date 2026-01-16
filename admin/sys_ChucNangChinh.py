import streamlit as st
import admin.sys_sqlite as ss
from admin.sys_kde_components import *
import time
from datetime import datetime


def app(selected):
    table_name="tbsys_ChucNangChinh"
    name = "chức năng chính"
    col_code =f'Chức năng chính'
    col_name =f'Thứ tự ưu tiên'

    c1, c2 = st.columns([1,3])
    with c1:
        st.header(f'Thêm {name}')

        ma = st.text_input(col_code)
        ten = st.text_input(col_name)
        icon = st.text_input('Icon')
        st.warning('Link icon: https://icons.getbootstrap.com/')


        disabled = not (len(ma) > 0 and len(ten) > 0)
        them = st.button(f'Thêm {name}', disabled=disabled)
        if them:
            # Sử dụng hàm insert_data_to_table để chèn dữ liệu vào bảng Xuong
            columns_xuong = [col_code, col_name, 'Icon','Người tạo','Thời gian tạo']
            values_xuong = [ma, ten,icon, st.session_state.username,fn.get_vietnam_time()]

            result = ss.insert_data_to_table(table_name,columns_list=columns_xuong,values_list=values_xuong)
            show_notification("Lỗi:",result)
    with c2:
        st.header(f'Danh sách {name} hiện tại')

        columns = ['ID', col_code, col_name, 'Icon', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa']
        search_columns = [col_code, col_name]
        dataframe_with_selections(
            table_name=table_name,
            columns=columns,
            search_columns=search_columns,
            col_where={'Đã xóa': ('=', 0)},
            col_order={'ID': 'ASC'},
            key=f'{table_name}_{st.session_state.df_key}',
            join_user_info=True,
            colums_disable=['ID', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa', 'Fullname'],
            download=True,
            select_all=True
        )