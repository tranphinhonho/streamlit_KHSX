import streamlit as st
import admin.sys_functions as fn
from admin.sys_kde_components import *
import bcrypt
import pandas as pd
import admin.sys_sqlite as ss
import streamlit_authenticator as stauth

def app(selected):
    st.header(selected)
    matkhaucu = st.text_input('Mật khẩu cũ',type='password')
    matkhaumoi = st.text_input('Mật khẩu mới',type='password')
    xacnhanmatkhau = st.text_input('Xác nhận mật khẩu mới', type='password')

    hash_pw_old = st.session_state['credentials']['usernames'][st.session_state.username]['password']

    if st.button('Đổi mật khẩu',type='primary'):
        # Kiểm tra mật khẩu cũ có đúng không
        is_correct_password = fn.check_password(matkhaucu, hash_pw_old)
        
        if is_correct_password:
            if matkhaumoi == xacnhanmatkhau:
                if len(matkhaumoi) >= 6:  # Kiểm tra độ dài mật khẩu mới
                    # Sử dụng streamlit_authenticator's Hasher để mã hóa mật khẩu mới
                    hashed_password = stauth.Hasher([matkhaumoi]).generate()[0]
                    
                    data={
                        'Username': [st.session_state.username],
                        'Password': [hashed_password],
                        'Người sửa': [st.session_state.username],
                        'Thời gian sửa': [fn.get_vietnam_time()]
                    }
                    df = pd.DataFrame(data=data)
                    result = ss.update_database_from_dataframe(table_name='tbsys_Users',dataframe=df,column_key='Username',nguoisua=st.session_state.username)
                    
                    if result is None or "thành công" in result.lower():
                        # Cập nhật session state khi thành công
                        st.session_state['credentials']['usernames'][st.session_state.username]['password'] = hashed_password
                        st.success('Đổi mật khẩu thành công!')
                        st.rerun()
                    else:
                        st.error(f'Lỗi cập nhật cơ sở dữ liệu: {result}')
                else:
                    st.warning('Mật khẩu mới phải có ít nhất 6 ký tự!')
            else:
                st.warning('Xác nhận mật khẩu mới không khớp!')
        else:
            st.warning('Mật khẩu cũ không đúng!')
