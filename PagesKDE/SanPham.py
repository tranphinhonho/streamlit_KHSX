import streamlit as st
from admin.sys_kde_components import *

# Danh sách vật nuôi: viết tắt -> tên đầy đủ
VAT_NUOI_OPTIONS = {
    'H': 'Heo',
    'G': 'Gà', 
    'B': 'Bò',
    'V': 'Vịt',
    'C': 'Cút',
    'D': 'Dê'
}

def app(selected):
    
    import_data(
        title="Import danh mục sản phẩm",
        file_path='Template\\SanPham.xlsx',
        output_name='SanPham.xlsx',
        dtype={
            'Code cám': str,
            'Tên cám': str,
            'Kích cỡ ép viên': str,
            'Dạng ép viên': str,
            'Kích cỡ đóng bao': float,
            'Pellet': str,
            'Packing': str,
            'Batch size': float,
            'Vật nuôi': str
            },
        table_name='SanPham',
        delete_by_ids=['Code cám','Tên cám'])
    
    st.header("1. Thêm sản phẩm")
    # Code cám	Tên cám	Kích cỡ ép viên	Dạng ép viên	Kích cỡ đóng bao	Pellet	Packing	Batch size
    
    
    c1, c2, c3, c4 = st.columns(4)
    codecam = c1.text_input("Code cám")
    tencam = c2.text_input("Tên cám")
    kichcoepvien = c3.text_input("Kích cỡ ép viên")
    dangepvien = c4.text_input("Dạng ép viên")
    
    c1, c2, c3, c4 = st.columns(4)
    kichcodongbao = c1.selectbox("Kích cỡ đóng bao", options=[25, 40, 50], index=None)   
    pellet = c2.text_input("Pellet")
    packing = c3.text_input("Packing")
    batchsize = c4.selectbox("Batch size (kg)", options=[8000,8400,6000], index=None)
    
    # Thêm dòng mới cho Vật nuôi
    c1, c2, c3, c4 = st.columns(4)
    vatnuoi = c1.selectbox(
        "Vật nuôi", 
        options=list(VAT_NUOI_OPTIONS.keys()),
        format_func=lambda x: f"{x} - {VAT_NUOI_OPTIONS[x]}",
        index=None,
        help="H=Heo, G=Gà, B=Bò, V=Vịt, C=Cút, D=Dê"
    )
    
    
    disabled = not (len(codecam) > 0 and len(tencam) > 0)
    
    if st.button("Thêm sản phẩm", disabled=disabled, type="primary"):
        # Sử dụng hàm insert_data_to_table để chèn dữ liệu vào bảng Xuong
        columns = [
            "Code cám", "Tên cám", "Kích cỡ ép viên", "Dạng ép viên",
            "Kích cỡ đóng bao", "Pellet", "Packing", "Batch size",
            "Vật nuôi",
            'Người tạo','Thời gian tạo'
        ]
        values = [
            codecam, tencam, kichcoepvien, dangepvien,
            kichcodongbao, pellet, packing, batchsize,
            vatnuoi,
            st.session_state.username, fn.get_vietnam_time()
        ]

        result = ss.insert_data_to_table("SanPham",columns_list=columns,values_list=values)
        show_notification("Lỗi:", result)
        
        
    st.header("2. Danh sách sản phẩm hiện tại")
    
    dataframe_with_selections(
        table_name="SanPham",
        columns=[
            'ID', 'Code cám', 'Tên cám', 'Kích cỡ ép viên', 'Dạng ép viên',
            'Kích cỡ đóng bao', 'Pellet', 'Packing', 'Batch size', 'Vật nuôi',
            'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'
        ],
        search_columns=['Code cám', 'Tên cám', 'Vật nuôi'],
        col_where={'Đã xóa': ('=', 0)},
        col_order={'ID': 'DESC'},
        key=f'SanPham_{st.session_state.df_key}',
        join_user_info=True,
        allow_select_all=True)