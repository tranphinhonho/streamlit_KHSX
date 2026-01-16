import streamlit as st
import pandas as pd
from admin.sys_functions import *
import time
import datetime
import streamlit_authenticator as stauth

from admin.sys_kde_components import *
import admin.sys_sqlite as ss

def app(selected_tab):
    delimiter = ' | '
    table_name = "tbsys_Users"
    
    # Số dòng bạn muốn hiển thị trên mỗi trang
    page_size = 50
    st.header('1. Thêm người dùng')
    c1,c2, c3, c4 = st.columns(4)
    username = c1.text_input("Username (*)")
    password = c1.text_input('Mật khẩu (*)')
    fullname = c2.text_input('Họ và tên (*)')

    ds_vaitro = ss.get_columns_data(table_name='tbsys_VaiTro', columns=['ID','Vai trò'], delimiter=delimiter,
                                    data_type='list',col_order={'ID':'ASC'},col_where={'Đã xóa':('=',0)})

    vaitro = c2.selectbox("Vai trò",ds_vaitro)
    id_vaitro = str(vaitro).split(delimiter)[0].strip()

    ds_gioitinh=['Nam','Nữ']
    gioitinh = c3.selectbox('Giới tính',ds_gioitinh)
    diachi = c3.text_input('Địa chỉ')

    sodienthoai = c4.text_input('Số điện thoại')
    email = c4.text_input('Email')

    status =not (len(username) and len(password) and len(fullname) and len(vaitro))
    them_btn = st.button('Thêm người dùng',disabled=status,type='primary')

    if them_btn:
        try:
            cols = ["Username" ,"Password" ,"Fullname" ,"Email","Số điện thoại","Giới tính","ID_VaiTro","Địa chỉ",'Người tạo']
            vals = [username,ss.hashpw(password),fullname,email,sodienthoai,gioitinh,id_vaitro,diachi,st.session_state.username]
            result = ss.insert_data_to_table(table_name=table_name,columns_list=cols,values_list=vals)
            show_notification('Lỗi:',result)
        except Exception as e:
            st.error(str(e))

    st.header('2. Danh sách người dùng')
    
    columns = ['ID','Username','Fullname','Email','Số điện thoại','Giới tính','ID_VaiTro','Địa chỉ', 'Người tạo','Thời gian tạo']
    col_config = {
        'ID_VaiTro':st.column_config.SelectboxColumn(options=ds_vaitro, required=True),
        'Giới tính':st.column_config.SelectboxColumn(options=ds_gioitinh, required=False)
    }
    dataframe_with_selections(table_name=table_name,columns=columns, search_columns=columns, join_user_info=False,
                              key=str(st.session_state.df_key) + 'qlnd',
                              joins=[
                                {
                                    'from_table':'tbsys_Users',
                                    'table':'tbsys_VaiTro',
                                    'on':{'ID_VaiTro':'ID'},
                                    'columns':['Vai trò'],  
                                    'replace':{'ID_VaiTro':'Vai trò'}
                                }
                              ],
                              col_where={'Đã xóa':('=',0)},
                              title= 'Kết quả tìm kiếm', column_config=col_config, width='content',num_rows='fix',
                              select_all=True, selected=True)
