import time

import admin.sys_ggd_api as ggd
import streamlit as st
import admin.sys_functions as fn
import os
from admin.sys_kde_components import *

def app(selected_tab):
    folder_name = 'HoSoDoanhNghiep_2'
    status, folder_id = ggd.check_existence_in_drive(is_folder=True, name=folder_name)
    if status == False:
        folder_id = ggd.create_folder_in_drive(new_folder_name=folder_name)


    st.header('Danh sách file trong thư mục google drive', divider='rainbow')
    # Ví dụ sử dụng hàm list_files_in_folder
    df_files = ggd.list_files_in_folder_to_dataframe(folder_id=folder_id)
    if len(df_files):

        df_files.rename(columns={'File ID': 'ID'}, inplace=True)
        selection = selectable_dataframe(df_files, key='khoiphucdb', multi_select=False)

        if not selection.empty:
            file_id = selection['ID'].iloc[0]
            file_name = selection['File Name'].iloc[0]

            st.markdown("---")
            st.markdown("#### File đã chọn")
            st.dataframe(selection, hide_index=True)

            c1, c2 = st.columns(2)
            
            if c1.button("Khôi phục database", type='primary'):
                save_path = 'database.db'
                try:
                    with st.spinner('Đang tải file và khôi phục...'):
                        ggd.download_file_from_drive(file_id, save_path)
                    st.success('Đã khôi phục thành công!')
                    
                    # Ghi lại lịch sử
                    # ss.insert_data_to_table(
                    #     table_name='LichSuKhoiPhucDatabase',
                    #     columns_list=['Filename', 'Người tạo', 'Thời gian tạo'],
                    #     values_list=[file_name, st.session_state.username, fn.get_vietnam_time()]
                    # )
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f'Lỗi khi khôi phục: {str(e)}')

            if c2.button("Xóa file", type='secondary'):
                try:
                    with st.spinner('Đang xóa file...'):
                        ggd.delete_files_by_ids(file_ids=[file_id])
                    st.success('Đã xóa file thành công!')
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f'Lỗi khi xóa file: {str(e)}')
    else:
        st.warning('Chưa có file nào trong thư mục!')

    st.header('Lịch sử khôi phục database', divider='rainbow')
    df = sp.get_columns_data(table_name='LichSuKhoiPhucDatabase',columns=['ID', 'Filename', 'Người tạo', 'Thời gian tạo'], col_order={'ID': 'DESC'})
    st.dataframe(df, hide_index=True)