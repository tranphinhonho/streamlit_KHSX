import datetime
import base64
import streamlit as st
import admin.sys_functions as fn
from admin.sys_kde_components import *
import bcrypt
import admin.sys_sqlite as ss
def app(selected):
    st.header(selected)
    # ds_table = sp.query_database(sql_string=f"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' And name not in ('DanhSachChucNang','PhanQuyen','IconChucNangChinh','ChucNangTheoVaiTro','VaiTro','ChucNangChinh','Users');",
    #                              data_type='list',delimiter=' | ')

    ds_table = ss.get_all_tables()

    table_dachon =st.multiselect('Chọn table',ds_table,default=None)
    disabled = not (len(table_dachon)>0)
    if st.button('Xóa dữ liệu',type='primary',disabled=disabled):
        for table in table_dachon:
            # Xóa dữ liệu từ bảng
            delete_query = f"DELETE FROM {table}"
            ss.query_database_sqlite(sql_string=delete_query, data_type=None)

            # Reset AutoIncrement
            reset_auto_increment_query = f"DBCC CHECKIDENT ([{table}], RESEED, 0)"
            ss.query_database_sqlite(sql_string=reset_auto_increment_query, data_type=None)

        st.success('Dữ liệu đã được xóa thành công và AutoIncrement đã được reset!')

    st.markdown('---')
    st.header('Các table đã chọn')
    for table in table_dachon:
        query = f"Select * from [{table}]"
        df = ss.query_database_sqlite(sql_string=query,data_type='dataframe')
        st.subheader(f'Dữ liệu bảng {table}')
        st.dataframe(df)


