import pandas as pd
import streamlit as st
from admin.sys_kde_components import *
import admin.sys_sqlite as ss

def app(selected):
    # Khởi tạo df_key để quản lý việc làm mới dữ liệu
    if 'df_key' not in st.session_state:
        st.session_state.df_key = 0
    else:
        # Đảm bảo df_key luôn là số nguyên
        if not isinstance(st.session_state.df_key, int):
            st.session_state.df_key = 0
    
    st.header('1. Phân quyền chức năng theo vai trò', divider='rainbow')

    try:
        # --- 1. LẤY DỮ LIỆU GỐC TỪ CSDL ---

        # Lấy tất cả các chức năng (con và cha)
        df_chucnang = ss.get_columns_data(
            table_name='tbsys_DanhSachChucNang',
            columns=['ID', 'ID Chức năng chính', 'Chức năng con', 'Thứ tự ưu tiên'],
            col_where={'Đã xóa': ('=', 0)}
        )
        # Đổi tên cột 'Thứ tự ưu tiên' của chức năng con để tránh xung đột khi join
        df_chucnang = df_chucnang.rename(columns={'Thứ tự ưu tiên': 'TTUT_CNCon'})

        # Lấy tên và TTUT chức năng chính
        df_chucnang = ss.get_info(
            df=df_chucnang,
            table_name='tbsys_ChucNangChinh',
            columns_name=['ID', 'Chức năng chính', 'Thứ tự ưu tiên'],
            columns_map=['ID Chức năng chính'],
            columns_key=['ID']
        )
        

        # Đổi tên các cột một cách an toàn sau khi join
        df_chucnang = df_chucnang.rename(columns={
            'ID': 'ID Danh sách chức năng',
            'Thứ tự ưu tiên': 'TTUT_CNC'      # TTUT từ ChucNangChinh
        })

        # Lấy tất cả các vai trò, sắp xếp theo ID
        df_vaitro = ss.get_columns_data(
            table_name='tbsys_VaiTro',
            columns=['ID', 'Vai trò'],
            col_where={'Đã xóa': ('=', 0)},
            col_order={'ID': 'ASC'}
        ).rename(columns={'ID': 'ID Vai trò'})

        # Lấy bảng phân quyền hiện tại
        df_quyen = ss.get_columns_data(
            table_name='tbsys_ChucNangTheoVaiTro',
            columns=['ID Vai trò', 'ID Danh sách chức năng'],
            col_where={'Đã xóa': ('=', 0)}
        )

        # --- 2. CHUẨN BỊ DỮ LIỆU CHO BẢNG LƯỚI ---

        # Tạo một bảng full-join giữa chức năng và vai trò để có tất cả các cặp có thể
        df_grid = df_chucnang.merge(df_vaitro, how='cross')
        

        # Đánh dấu các quyền đã có
        df_quyen['has_permission'] = True
        df_grid = df_grid.merge(df_quyen, on=['ID Vai trò', 'ID Danh sách chức năng'], how='left')
        df_grid['has_permission'] = df_grid['has_permission'].astype('boolean').fillna(False)
        
        # Sử dụng pivot_table để xoay bảng, đưa vai trò thành các cột
        permission_matrix = df_grid.pivot_table(
            index=['Chức năng chính', 'Chức năng con', 'ID Danh sách chức năng', 'TTUT_CNC', 'TTUT_CNCon'],
            columns='Vai trò',
            values='has_permission'
        ).reset_index()
        
        # Sắp xếp lại theo thứ tự ưu tiên
        permission_matrix = permission_matrix.sort_values(by=['TTUT_CNC', 'TTUT_CNCon'])
        
        # Sắp xếp lại các cột vai trò theo thứ tự ID
        role_columns_sorted = df_vaitro['Vai trò'].tolist()
        fixed_columns = ['Chức năng chính', 'Chức năng con', 'ID Danh sách chức năng']
        permission_matrix = permission_matrix[fixed_columns + role_columns_sorted]


        # --- 3. HIỂN THỊ BẢNG LƯỚI ĐỂ CHỈNH SỬA ---

        # Lấy danh sách các cột vai trò để cấu hình
        role_columns = df_vaitro['Vai trò'].tolist() # Giữ nguyên để dùng cho vòng lặp

        # ĐẢM BẢO CÁC CỘT VAI TRÒ LÀ KIỂU BOOLEAN
        for role in role_columns:
            if role in permission_matrix.columns:
                permission_matrix[role] = permission_matrix[role].astype(bool)

        # --- 3.5 KHỞI TẠO SESSION STATE VÀ KHU VỰC ĐIỀU KHIỂN ---
        if 'permission_matrix' not in st.session_state:
            st.session_state['permission_matrix'] = permission_matrix

        # Nút làm mới dữ liệu
        
        if st.button("🔄 Làm mới", help="Tải lại dữ liệu mới nhất từ database", type="secondary"):
            if 'permission_matrix' in st.session_state:
                del st.session_state['permission_matrix']
            st.success("Đã làm mới dữ liệu!")
            st.rerun()

        st.subheader("Công cụ chọn hàng loạt", divider='blue')
        
        # Hàng 1: Các ô chọn
        col1, col2 = st.columns(2)
        with col1:
            main_funcs = st.session_state.permission_matrix['Chức năng chính'].unique().tolist()
            selected_main_funcs = st.multiselect("Chọn Chức năng chính", options=main_funcs)
        with col2:
            roles = role_columns
            selected_roles = st.multiselect("Chọn Vai trò", options=roles)

        # Hàng 2: Các nút hành động
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        
        # Nút hành động
        with btn_col1:
            if st.button("✔️ Chọn con", help="Chọn các chức năng con tương ứng với lựa chọn ở trên", width='stretch', disabled=not (selected_main_funcs and selected_roles)):
                for role in selected_roles:
                    st.session_state.permission_matrix.loc[st.session_state.permission_matrix['Chức năng chính'].isin(selected_main_funcs), role] = True
                st.rerun()
        with btn_col2:
            if st.button("❌ Bỏ chọn con", help="Bỏ chọn các chức năng con tương ứng với lựa chọn ở trên", width='stretch', disabled=not (selected_main_funcs and selected_roles)):
                for role in selected_roles:
                    st.session_state.permission_matrix.loc[st.session_state.permission_matrix['Chức năng chính'].isin(selected_main_funcs), role] = False
                st.rerun()
        with btn_col3:
            if st.button(f"✔️ Chọn tất cả", help="Chọn tất cả các quyền cho các vai trò đã chọn", width='stretch', disabled=not selected_roles):
                for role in selected_roles:
                    st.session_state.permission_matrix[role] = True
                st.rerun()
        with btn_col4:
            if st.button(f"❌ Bỏ chọn tất cả", help="Bỏ chọn tất cả các quyền cho các vai trò đã chọn", width='stretch', disabled=not selected_roles):
                for role in selected_roles:
                    st.session_state.permission_matrix[role] = False
                st.rerun()

        # Tạo column_config động
        column_config = {
            "Chức năng chính": st.column_config.TextColumn("Chức năng chính", disabled=True),
            "Chức năng con": st.column_config.TextColumn("Chức năng con", disabled=True),
            "ID Danh sách chức năng": None # Ẩn cột ID
        }
        for role in role_columns:
            column_config[role] = st.column_config.CheckboxColumn(role)

        st.info("Tích vào các ô để cấp quyền cho vai trò tương ứng với chức năng, hoặc sử dụng công cụ chọn hàng loạt ở trên.")
        
        # Hiển thị data editor
        edited_matrix = st.data_editor(
            st.session_state['permission_matrix'],
            column_config=column_config,
            hide_index=True,
            width='stretch',
            key="permission_editor"
        )
        # Cập nhật lại state sau khi người dùng có thể đã chỉnh sửa thủ công
        st.session_state['permission_matrix'] = edited_matrix

        # --- 4. LƯU THAY ĐỔI ---

        if st.button("Lưu thay đổi", type="primary"):
            # Chuyển đổi (unpivot) bảng lưới từ dạng rộng về dạng dài
            id_vars = ['ID Danh sách chức năng', 'Chức năng chính', 'Chức năng con']
            updated_permissions_long = st.session_state.permission_matrix.melt(
                id_vars=id_vars,
                var_name='Vai trò',
                value_name='has_permission'
            )

            # Chỉ giữ lại những quyền được cấp (True)
            updated_permissions_long = updated_permissions_long[updated_permissions_long['has_permission']]

            # Map tên vai trò về lại ID Vai trò
            role_map = df_vaitro.set_index('Vai trò')['ID Vai trò']
            updated_permissions_long['ID Vai trò'] = updated_permissions_long['Vai trò'].map(role_map)

            # Chọn các cột cần thiết để insert vào CSDL
            final_df_to_insert = updated_permissions_long[['ID Vai trò', 'ID Danh sách chức năng']]

            # Lấy tên người dùng hiện tại
            username = st.session_state.get("username", "unknown")

            # Sử dụng transaction để đảm bảo toàn vẹn dữ liệu
            try:
                # Bắt đầu transaction (ẩn, vì pyodbc autocommit=True, ta sẽ xóa và chèn)
                
                # 1. Xóa tất cả các quyền hiện có
                delete_query = "UPDATE tbsys_ChucNangTheoVaiTro SET [Đã xóa] = 1, [Người sửa] = ?, [Thời gian sửa] = CURRENT_TIMESTAMP WHERE [Đã xóa] = 0"
                ss.query_database_sqlite(delete_query, params=[username])


                # 2. Chèn lại các quyền mới từ DataFrame
                if not final_df_to_insert.empty:
                    result = ss.insert_data_to_sql_server(
                        table_name='tbsys_ChucNangTheoVaiTro',
                        dataframe=final_df_to_insert,
                        created_by=username
                    )
                    if "thành công" not in result:
                        raise Exception(result)
                
                st.success("Cập nhật phân quyền thành công!")
                # Xóa state để load lại dữ liệu mới từ DB ở lần chạy sau
                if 'permission_matrix' in st.session_state:
                    del st.session_state['permission_matrix']
                st.rerun()

            except Exception as e:
                st.error(f"Có lỗi xảy ra trong quá trình cập nhật: {e}")


    except Exception as e:
        st.error(f"Không thể tải dữ liệu phân quyền: {e}")

    st.header('2. Danh sách chức năng theo vai trò', divider='rainbow')
    
    if st.button("🔄 Làm mới", help="Tải lại dữ liệu mới nhất từ database", type="secondary", key="refresh_section_2"):
        # Tăng df_key để force reload dữ liệu
        if 'df_key' not in st.session_state:
            st.session_state.df_key = 0
        else:
            # Đảm bảo df_key là số nguyên trước khi cộng
            if isinstance(st.session_state.df_key, str):
                st.session_state.df_key = 0
        st.session_state.df_key += 1
        st.success("Đã làm mới dữ liệu!")
        st.rerun()
    
    table_name = 'tbsys_ChucNangTheoVaiTro'
    columns = ['ID',
        'ID Vai trò',
        'ID Danh sách chức năng'
    ]
    search_columns = ['tbsys_VaiTro.Vai trò', 'tbsys_ChucNangChinh.Chức năng chính', 'tbsys_DanhSachChucNang.Chức năng con']
    joins=[
        {
            'from_table': table_name,
            'table': 'tbsys_VaiTro',
            'on': {'ID Vai trò': 'ID'},
            'columns': ['Vai trò'],
            'replace': {'ID Vai trò': 'Vai trò'}
        },
        {
            'from_table': table_name,
            'table': 'tbsys_DanhSachChucNang',
            'on': {'ID Danh sách chức năng': 'ID'},
            'columns': ['ID Chức năng chính','Chức năng con'],
            'replace': {'ID Danh sách chức năng': 'Chức năng con'}
        },
        {
            'from_table': 'tbsys_DanhSachChucNang',
            'table': 'tbsys_ChucNangChinh',
            'on': {'ID Chức năng chính': 'ID'},
            'columns': ['Chức năng chính'],
            'replace': {'ID Chức năng chính': 'Chức năng chính'}
        }
    ]
    
    dataframe_with_selections(
        table_name=table_name,
        columns=columns,
        search_columns=search_columns,
        joins=joins,
        col_where={f'{table_name}.[Đã xóa]': ('=', 0)},
        key=f'{table_name}_{st.session_state.df_key}',
        multi_select=True,
        select_all=False,
        output_columns=['ID','ID Vai trò','ID Chức năng chính','ID Danh sách chức năng'],
        width='stretch'
    )