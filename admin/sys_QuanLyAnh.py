import time

import streamlit as st
import os
import admin.sys_functions as fn
import pandas as pd
from admin.sys_kde_components import *
# Hàm chính của ứng dụng
def app(selected):
    st.header('Thêm ảnh', divider='rainbow')

    # Tải lên tệp ảnh
    uploaded_file = st.file_uploader('Ảnh sản phẩm', type=['png', 'jpg', 'jpeg'], accept_multiple_files=False)

    if uploaded_file:
        st.image(uploaded_file, caption="Ảnh đã tải lên",width=200)

        # Lấy tên file (basename) mặc định
        default_filename = os.path.splitext(os.path.basename(uploaded_file.name))[0]

        # Đặt tên ảnh với tên mặc định là tên file đã tải lên
        ten_anh = st.text_input('Đặt tên ảnh', value=default_filename)

        # Nút lưu ảnh
        disabled = not (uploaded_file and ten_anh)
        them = st.button('Thêm ảnh', disabled=disabled, type='primary')
        if them:
            try:
                if uploaded_file:
                    fn.save_uploaded_file(uploaded_file, ma_san_pham=ten_anh, output_dir='AnhSanPham')
                    st.success(f'Ảnh đã được lưu với tên: {ten_anh}')
            except Exception as e:
                st.error(str(e))
    else:
        # Nếu chưa tải lên tệp, không hiển thị phần nhập tên ảnh
        st.text_input('Đặt tên ảnh', value='', disabled=True)


    st.markdown('---')
    st.header('2. Danh sách ảnh',divider='rainbow')
    image_paths = fn.get_image_paths('AnhSanPham')
    df = pd.DataFrame(image_paths, columns=['Đường dẫn ảnh'])
    df['STT'] = range(1, len(df) + 1)
    df = df[['STT', 'Đường dẫn ảnh']]
    df.rename(columns={'STT': 'ID'}, inplace=True)
    selection = selectable_dataframe(df, key='quanlyanh', multi_select=True)

    if not selection.empty:
        image_paths = selection['Đường dẫn ảnh'].tolist()
        st.markdown("---")
        st.markdown("#### Ảnh đã chọn")
        
        # Display images in columns
        cols = st.columns(5)
        for i, image_path in enumerate(image_paths):
            with cols[i % 5]:
                st.image(image_path, use_column_width=True)

        if st.button('Xóa ảnh đã chọn', type='primary'):
            try:
                for img in image_paths:
                    fn.delete_image(img)
                st.success('Đã xóa thành công')
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(str(e))
    # if image_paths:

    #     show_images(image_paths=image_paths)

    #     if st.button('Xóa ảnh',type='primary'):
    #         try:
    #             for img in image_paths:
    #                 fn.delete_image(img)
    #             st.success('Đã xóa thành công')
    #             time.sleep(2)
    #             st.rerun()
    #         except Exception as e:
    #             st.error(str(e))