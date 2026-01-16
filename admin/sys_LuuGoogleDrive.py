import admin.sys_ggd_api as ggd
import streamlit as st
import os
from admin.sys_kde_components import show_notification
import admin.sys_functions as fn
import time

def app(selected_tab):
    folder_name = fn.get_current_directory(type='folder')
    status, folder_id = ggd.check_existence_in_drive(is_folder=True, name=folder_name)
    if status == False:
        folder_id = ggd.create_folder_in_drive(new_folder_name=folder_name)

    st.header('Lưu trữ database vào google drive',divider='rainbow')
    filename = 'database.db'
    # Lấy giờ Việt Nam
    current_timestamp = fn.get_vietnam_time()
    current_timestamp_str = current_timestamp.strftime('%Y%m%d_%H%M%S')
    # Tạo tên file mới với timestamp
    new_filename = f"{os.path.splitext(filename)[0]} {current_timestamp_str}{os.path.splitext(filename)[1]}"

    st.markdown(f'**Tên thư mục google drive:**: {folder_name}')
    st.markdown(f'**Tên file:** {new_filename}')
    if st.button('Lưu vào Google Drive',type='primary'):
        # st.write(new_filename)
        status, result =  ggd.upload_to_drive(folder_id=folder_id, file_path=filename,file_name=new_filename)
        if status:
            st.success(f'Đã lưu file "{new_filename}" thành công!')
            columns = ['Filename','Người tạo','Thời gian tạo']
            values = [new_filename, st.session_state.username, current_timestamp]
            result = sp.insert_data_to_table(table_name='LichSuLuuGoogleDrive',columns_list=columns,values_list=values)
            show_notification(key='Lỗi:',result=result)
        else:
            st.error(result)
            time.sleep(2)
            st.rerun()

    st.header('Lịch sử lưu trữ database vào google drive', divider='rainbow')
    df = sp.get_columns_data(table_name='LichSuLuuGoogleDrive',columns=['ID','Filename','Người tạo','Thời gian tạo'],col_order={'ID':'DESC'})
    st.dataframe(df,hide_index=True)
