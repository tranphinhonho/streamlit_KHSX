import streamlit as st
from admin.sys_kde_components import *

def app(selected):
    
    import_data(
        title="Import danh mục sản phẩm",
        file_path='Template\MasterdataLoss.xlsx',
        output_name='MasterdataLoss.xlsx',
        dtype={
            'Code cám': str,
            'Tên cám': str,
            'Kích cỡ ép viên': str,
            'Dạng ép viên': str,
            'Kích cỡ đóng bao': float,
            'Pellet': str,
            'Packing': str,
            'Batch size': float
            },
        table_name='MasterdataLoss',
        delete_by_ids=['Code NL','Tên NL', 'Loại'])
    
    st.header("1. Thêm nguyên liệu")
    # Code cám	Tên cám	Kích cỡ ép viên	Dạng ép viên	Kích cỡ đóng bao	Pellet	Packing	Batch size
    
    
    c1, c2, c3 = st.columns(3)
    codenl = c1.text_input("Code NL")
    tennl = c2.text_input("Tên NL")
    loai = c3.selectbox("Loại", options=["Hammer", "Mixer", "Pellet", "Packing"])
    
    
    
    disabled = not (len(codenl) > 0 and len(tennl) > 0)
    
    if st.button("Thêm nguyên liệu", disabled=disabled, type="primary"):
        # Sử dụng hàm insert_data_to_table để chèn dữ liệu vào bảng Xuong
        columns = [
            "Code NL", "Tên NL", "Loại",
            'Người tạo','Thời gian tạo'
        ]
        values = [
            codenl, tennl, loai,
            st.session_state.username, fn.get_vietnam_time()
        ]

        result = ss.insert_data_to_table("MasterdataLoss",columns_list=columns,values_list=values)
        show_notification("Lỗi:", result)
        
        
    st.header("2. Danh sách nguyên liệu hiện tại")
    
    dataframe_with_selections(
        table_name="MasterdataLoss",
        columns=[
            'ID', 'Code NL', 'Tên NL', 'Loại',
            'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'
        ],
        search_columns=['Code NL', 'Tên NL'],
        col_where={'Đã xóa': ('=', 0)},
        col_order={'ID': 'DESC'},
        key=f'MasterdataLoss_{st.session_state.df_key}',
        join_user_info=True)