import streamlit as st
import admin.sys_sqlite as ss
from admin.sys_kde_components import *
import time
from datetime import datetime
def app(selected):
    table_name="tbsys_DanhSachChucNang"
    name = "chức năng"
    col_code =f'Chức năng chính'
    col_name =f'Chức năng con'
    col_name1 = f'Thứ tự ưu tiên'
    delimiter = ' | '

    c1, c2 = st.columns([1,3])
    with c1:
        st.header(f'Thêm {name}')
        chucnangs = ss.get_columns_data('tbsys_ChucNangChinh',['ID','Chức năng chính'],delimiter,'list',col_order={'Thứ tự ưu tiên':'ASC'}, 
                                        col_where={'Đã xóa':('=',0)})

        chucnangchinh = st.selectbox(col_code,chucnangs)
        id_chucnangchinh = str(chucnangchinh).split(delimiter)[0].strip()
        chucnangcon = st.text_input(col_name)

        max = ss.query_database_sqlite(sql_string=f"SELECT MAX([Thứ tự ưu tiên]) FROM tbsys_DanhSachChucNang Where [ID Chức năng chính]='{id_chucnangchinh}'",data_type='value')
        thutu=st.number_input(col_name1,value=(max +1) if (max and max is not None) else 1)

        disabled = not (len(chucnangchinh) > 0 and len(chucnangcon) > 0)
        them = st.button(f'Thêm {name}', disabled=disabled,type='primary')
        if them:
            # Sử dụng hàm insert_data_to_table để chèn dữ liệu vào bảng Xuong
            columns = ["ID Chức năng chính", "Chức năng con","Thứ tự ưu tiên", 'Người tạo','Thời gian tạo']
            values = [id_chucnangchinh, chucnangcon, thutu ,st.session_state.username,fn.get_vietnam_time()]

            result = ss.insert_data_to_table(table_name,columns_list=columns,values_list=values)
            if "Lỗi:" in result:
                st.error(result)
            else:
                st.success(result)
    with c2:
        st.header(f'Danh sách {name} hiện tại')
        columns = [
            'ID', 'ID Chức năng chính', 'Chức năng con', 'Thứ tự ưu tiên',
            'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa'
        ]
        joins=[
        {
            'from_table': table_name,
            'table': 'tbsys_ChucNangChinh',
            'on': {'ID Chức năng chính': 'ID'},
            'columns': ['Chức năng chính'],
            'replace': {'ID Chức năng chính': 'Chức năng chính'}
        }
        ]
        search_columns = ['tbsys_ChucNangChinh.Chức năng chính', 'Chức năng con']
        chucnangs_options = ss.get_columns_data('tbsys_ChucNangChinh',['ID','Chức năng chính'],delimiter,'list',col_order={'Thứ tự ưu tiên':'ASC'}, col_where={'Đã xóa':('=',0)})
        column_config = {
            "ID Chức năng chính": st.column_config.SelectboxColumn("ID Chức năng chính", options=chucnangs_options, required=True),
            "Thứ tự ưu tiên": st.column_config.NumberColumn("Thứ tự ưu tiên", required=True),
        }
        dataframe_with_selections(
            table_name=table_name,
            columns=columns,
            search_columns=search_columns,
            col_where={'Đã xóa': ('=', 0)},
            col_order={'ID': 'ASC'},
            joins=joins,
            key=f'{table_name}_{st.session_state.df_key}',
            join_user_info=True,
            colums_disable=['ID', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa', 'Fullname'],
            download=True,
            select_all=True,
            column_config=column_config ,
            output_columns=['ID', 'ID Chức năng chính', 'Chức năng con', 'Thứ tự ưu tiên',
            'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Đã xóa', 'Fullname']
        )