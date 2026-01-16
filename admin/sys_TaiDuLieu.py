import datetime
import io
import os
import base64
import streamlit as st
import pandas as pd
import admin.sys_sqlite as ss
from admin.sys_kde_components import *
def app(selected):
    st.header(selected)

    ds_table = ss.get_all_tables()
    table_dachon = st.multiselect('Chọn table', ds_table, default=ds_table)
    if len(table_dachon):
        st.subheader('Các table đã chọn')
        df = pd.DataFrame(data={"Table name":table_dachon})
        st.dataframe(df)
        # Tạo tên file dựa trên thời gian hiện tại
        file_name = f"Back_up{datetime.datetime.now().strftime('%Y_%m-%d_%H%M%S')}"

        # Tạo hai danh sách rỗng để chứa các DataFrame và sheet names
        df_list = []
        sheetnames_list = []

        # Lặp qua mỗi bảng đã chọn
        for table_name in table_dachon:
            # Truy vấn dữ liệu từ bảng và đọc vào DataFrame
            df = ss.query_database_sqlite(sql_string=f"SELECT * FROM {table_name}", data_type='dataframe')

            # Thêm DataFrame và tên sheet vào danh sách tương ứng
            df_list.append(df)
            sheetnames_list.append(table_name)

        # Gọi hàm download_multi_sheets với danh sách DataFrame và sheet names
        download_multi_sheets(dataframes=df_list, sheet_names=sheetnames_list, filename='All Data.xlsx',
                              button_text='Download Excel',key=fn.get_timestamp())