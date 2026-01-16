import time
import streamlit as st
import pandas as pd
import admin.sys_sqlite as ss
from admin.sys_kde_components import *

@st.dialog("Xóa table đã chọn")
def xoa_table(table_list):
    st.write(f"Bạn có thật sự muốn xóa các table đã chọn?")
    if st.button("Submit"):
        result = ss.delete_tables(table_list=table_list)
        show_notification('Lỗi:', result)

def app(seleted_tab):
    st.header('Tạo bảng', divider='rainbow')
    
    all_user_tables = ss.get_all_tables()
    options = ["--Tạo bảng mới--"] + all_user_tables

    selected_option = st.selectbox("Chọn bảng để sửa hoặc tạo mới:", options)
    
    if selected_option == "--Tạo bảng mới--":
        table_name = st.text_input("Nhập tên bảng mới:")
    else:
        table_name = selected_option
    
    # Tạo dictionary ban đầu với cột ID mặc định
    data = {
        "Tên trường": ["ID"],
        "Kiểu dữ liệu": ["INT"],
        "n (Mặc định n=50)": [50],
        "Auto Increment": [True],
        "Unique (Đã xóa=0)": [False],
        'Not Null': [True],
        'Mặc định': [""]
    }
    # Tạo dataframe từ dictionary
    df = pd.DataFrame(data)

    # Thiết lập column_config chính xác
    column_config = {
        "Tên trường": st.column_config.TextColumn(label="Tên trường"),
        "Kiểu dữ liệu": st.column_config.SelectboxColumn(
            label="Kiểu dữ liệu",
            options=[
                '', 'TEXT', 'INTEGER', 'REAL', 'NUMERIC', 'BLOB',
                'VARCHAR(n)', 'CHAR(n)', 'DATETIME', 'DATE', 'BOOLEAN'
            ],
            help="SQLite types: TEXT (string), INTEGER (int), REAL (float), NUMERIC (decimal), BLOB (binary)"
        ),
        "Auto Increment": st.column_config.CheckboxColumn(
            label="Auto Increment",
            help="Tự động tăng (AUTOINCREMENT). Chỉ áp dụng cho INTEGER PRIMARY KEY."
        ),
        "Unique (Đã xóa=0)": st.column_config.CheckboxColumn(
            label="Unique (Đã xóa=0)", 
            help="Tạo ràng buộc UNIQUE kết hợp các cột được chọn với điều kiện [Đã xóa]=0."
        ),
        'Not Null': st.column_config.CheckboxColumn(label='Not Null'),
        "Mặc định": st.column_config.TextColumn(label="Mặc định")
    }

    # --- TẢI CẤU TRÚC BẢNG HIỆN TẠI (NẾU CÓ) ---
    all_tables = ss.get_all_tables()
    if table_name and table_name in all_tables:
        # Nếu bảng đã tồn tại, xóa hàng mẫu và load cấu trúc từ DB
        df = df.drop(index=df.index)
        try:
            # Lấy thông tin chi tiết các cột của bảng đã có
            cols_info = ss.get_table_columns_info(table_name)
            # Chuyển thành DataFrame để điền vào data_editor
            df = pd.DataFrame(cols_info)
            
            # Lọc bỏ các cột computed từ logic cũ (_UQ_CHECK_...)
            if not df.empty and 'name' in df.columns:
                df = df[~df['name'].str.startswith('_UQ_CHECK_', na=False)]
            
            # Đổi tên cột để khớp với data_editor
            df = df.rename(columns={
                'name': 'Tên trường',
                'type': 'Kiểu dữ liệu',
                'max_length': 'n (Mặc định n=50)',
                'is_identity': 'Auto Increment'
            })
            
            # Ánh xạ is_nullable: is_nullable=1 nghĩa là CÓ THỂ NULL, nên Not Null = NOT is_nullable
            if 'is_nullable' in df.columns:
                df['Not Null'] = ~df['is_nullable'].astype(bool)
                df = df.drop(columns=['is_nullable'])
            
            # Lấy thông tin về filtered unique index và cập nhật df
            df['Unique (Đã xóa=0)'] = False  # Đặt giá trị mặc định
            indexed_cols = ss.get_filtered_unique_index_info(table_name)
            if indexed_cols:
                df.loc[df['Tên trường'].isin(indexed_cols), 'Unique (Đã xóa=0)'] = True

            # Thêm các cột còn thiếu với giá trị mặc định
            for col in column_config.keys():
                if col not in df.columns:
                    df[col] = None  # Hoặc giá trị mặc định phù hợp
            
            # Sắp xếp lại để cột ID luôn đứng đầu
            if not df.empty and 'Tên trường' in df.columns:
                id_rows = df[df['Tên trường'] == 'ID']
                other_rows = df[df['Tên trường'] != 'ID']
                df = pd.concat([id_rows, other_rows], ignore_index=True)
                
        except Exception as e:
            st.error(f"Không thể tải cấu trúc của bảng '{table_name}': {e}")

    # Hiển thị data editor
    edited_df = st.data_editor(df, num_rows='dynamic', column_config=column_config, width='stretch')

    if len(edited_df):
        disabled = (len(table_name) == 0)

        # --- KIỂM TRA BẢNG TỒN TẠI VÀ TÙY CHỌN GHI ĐÈ ---
        overwrite_table = False
        if table_name:
            all_tables = ss.get_all_tables()
            if table_name in all_tables:
                overwrite_table = st.checkbox(f"Xóa bảng '{table_name}' cũ và tạo lại (Ghi đè)")
        
        # Hiển thị SQL preview
        st.subheader('Chuỗi SQL')
        
        if overwrite_table or (table_name and table_name not in all_tables):
            # Chế độ tạo bảng mới
            create_table_query = ss.generate_create_table_query_sqlite(table_name, edited_df)
            
            # Kiểm tra xem có cột Auto Increment không
            if 'Auto Increment' in edited_df.columns:
                has_auto_increment = edited_df['Auto Increment'].any()
                if not has_auto_increment:
                    st.warning("⚠️ Lưu ý: Bảng không có cột Auto Increment (khóa chính tự tăng). Bạn có thể thêm cột ID với kiểu INT và tick Auto Increment.")
            
            st.code(create_table_query, language='sql')
            
            button_label = 'Tạo lại bảng' if overwrite_table else 'Tạo bảng'
            if st.button(button_label, type='primary', disabled=disabled):
                if overwrite_table:
                    # Xóa bảng cũ trước
                    drop_result = ss.delete_tables([table_name])
                    if "Error" in str(drop_result):
                        st.error(f"Không thể xóa bảng cũ: {drop_result}")
                        st.stop()
                
                # Tạo bảng mới
                result = ss.query_database_sqlite(create_table_query, data_type=None)
                if result is not None:
                    st.success(f"Đã tạo bảng '{table_name}' thành công!")
                    
                    # Tạo filtered unique index nếu có cột được đánh dấu unique
                    if 'Unique (Đã xóa=0)' in edited_df.columns:
                        unique_cols = edited_df[edited_df['Unique (Đã xóa=0)'] == True]['Tên trường'].tolist()
                        if unique_cols:
                            index_query = ss.generate_filtered_index_query(table_name, unique_cols)
                            index_result = ss.query_database_sqlite(index_query, data_type=None)
                            if index_result is not None:
                                st.success(f"Đã tạo unique index cho các cột: {', '.join(unique_cols)}")
                            else:
                                st.warning(f"Bảng đã tạo nhưng không thể tạo unique index")
                    
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
        else:
            # Chế độ cập nhật bảng
            st.info(f"Bảng '{table_name}' đã tồn tại. Tiến hành cập nhật cấu trúc...")
            
            try:
                # Dọn dẹp các constraint và computed column cũ (từ logic cũ)
                cleanup_result = ss.drop_old_unique_constraints_and_computed_columns(table_name)
                if cleanup_result['constraints_dropped'] or cleanup_result['computed_columns_dropped']:
                    st.info(f"Đã dọn dẹp logic cũ: {len(cleanup_result['constraints_dropped'])} constraints, {len(cleanup_result['computed_columns_dropped'])} computed columns")
                
                # Lấy cấu trúc cũ
                df_old_structure = pd.DataFrame(ss.get_table_columns_info(table_name))
                
                # So sánh và tạo các câu ALTER TABLE
                alter_queries = ss.generate_alter_table_queries(table_name, edited_df, df_old_structure)
                
                # Chuẩn bị SQL preview
                sql_preview = ""
                
                # Bước 1: Xóa index cũ
                sql_preview += "-- Bước 1: Xóa các filtered unique index cũ\n"
                sql_preview += f"-- DROP ALL FILTERED UNIQUE INDEXES ON [{table_name}]\n\n"
                
                # Bước 2: Cập nhật cấu trúc
                if alter_queries:
                    sql_preview += "-- Bước 2: Cập nhật cấu trúc bảng\n"
                    sql_preview += "\n".join(alter_queries) + "\n\n"
                else:
                    sql_preview += "-- Bước 2: Không có thay đổi về cấu trúc cột\n\n"
                
                # Bước 3: Tạo lại index
                # SQLite không giới hạn kiểu dữ liệu cho index như SQL Server, nhưng BLOB không nên dùng
                invalid_index_types = ['BLOB']
                valid_index_df = edited_df[~edited_df['Kiểu dữ liệu'].isin(invalid_index_types)]
                filtered_index_cols = []
                if 'Unique (Đã xóa=0)' in valid_index_df.columns:
                    filtered_index_cols = valid_index_df[valid_index_df['Unique (Đã xóa=0)'] == True]['Tên trường'].tolist()
                
                if filtered_index_cols:
                    sql_preview += "-- Bước 3: Tạo lại filtered unique index\n"
                    index_query = ss.generate_filtered_index_query(table_name, filtered_index_cols)
                    sql_preview += index_query
                else:
                    sql_preview += "-- Bước 3: Không có filtered unique index nào để tạo"
                
                # Hiển thị SQL preview
                st.code(sql_preview, language='sql')
                
                # Nút cập nhật
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button('Cập nhật bảng', type='primary'):
                        try:
                            # Bước 1: Xóa index cũ
                            st.info("Bước 1/3: Xóa các filtered unique index cũ...")
                            ss.drop_all_filtered_unique_indexes(table_name)
                            st.success("Đã dọn dẹp index cũ.")
                            
                            # Bước 2: Cập nhật cấu trúc
                            if alter_queries:
                                st.info("Bước 2/3: Cập nhật cấu trúc bảng...")
                                for query in alter_queries:
                                    result = ss.query_database_sqlite(query, data_type=None)
                                    if result is None or "thành công" not in str(result).lower():
                                        raise Exception(f"Lỗi khi thực thi: {query}\nKết quả: {result}")
                                st.success(f"Đã cập nhật cấu trúc bảng '{table_name}' thành công.")
                            else:
                                st.info("Bước 2/3: Không có thay đổi về cấu trúc cột.")
                            
                            # Bước 3: Tạo lại index
                            if filtered_index_cols:
                                st.info("Bước 3/3: Tạo lại filtered unique index...")
                                index_query = ss.generate_filtered_index_query(table_name, filtered_index_cols)
                                result_index = ss.query_database_sqlite(index_query, data_type=None)
                                if result_index is None or "thành công" not in str(result_index).lower():
                                    raise Exception(f"Lỗi khi tạo index: {result_index}")
                                st.success("Đã tạo lại filtered unique index thành công.")
                            else:
                                st.info("Bước 3/3: Không có filtered unique index nào để tạo.")
                            
                            st.success(f"✅ Hoàn thành cập nhật bảng '{table_name}'!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi khi cập nhật bảng: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                
                with col2:
                    if st.button('Hủy thay đổi'):
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Lỗi khi chuẩn bị cập nhật bảng: {e}")
                import traceback
                st.code(traceback.format_exc())
    else:
        st.warning("Vui lòng thêm trường dữ liệu!")

    st.markdown('---')
    st.header("Xóa bảng", divider='rainbow')

    ds_table = ss.get_all_tables()
    chon_table = st.multiselect('Chọn table cần xóa', ds_table)
    if st.button("Xóa table đã chọn"):
        xoa_table(chon_table)
