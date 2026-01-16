import streamlit as st
from admin.sys_kde_components import *
import sqlite3

def process_import_dathang(df, loai_dathang, khach_vang_lai=0):
    """Xử lý import Excel cho đặt hàng"""
    # Kiểm tra cột bắt buộc - hỗ trợ cả 2 định dạng
    if 'Tên sản phẩm' in df.columns:
        # Định dạng mới: chỉ cần Tên sản phẩm và Số lượng
        return process_import_by_product_name(df, loai_dathang, khach_vang_lai)
    elif 'Code cám' in df.columns:
        # Định dạng cũ: cần Code cám đầy đủ
        return process_import_by_code_cam(df, loai_dathang, khach_vang_lai)
    else:
        st.error("❌ File Excel phải có cột 'Tên sản phẩm' hoặc 'Code cám' và 'Số lượng'")
        return None

def process_import_by_product_name(df, loai_dathang, khach_vang_lai=0):
    """Xử lý import Excel từ tên sản phẩm - tự động tìm thông tin từ database"""
    if 'Số lượng' not in df.columns:
        st.error("❌ File Excel phải có cột 'Số lượng'")
        return None
    
    conn = sqlite3.connect('database_new.db')
    result_data = []
    not_found = []
    
    for idx, row in df.iterrows():
        ten_sanpham = str(row['Tên sản phẩm']).strip()
        so_luong = row['Số lượng']
        
        # Tìm sản phẩm từ tên
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, [Code cám], [Tên cám], [Kích cỡ ép viên] 
            FROM SanPham 
            WHERE [Tên cám] = ? AND [Đã xóa] = 0
        """, (ten_sanpham,))
        result = cursor.fetchone()
        
        if result:
            id_sanpham, code_cam, ten_cam, kich_co = result
            
            item = {
                'ID sản phẩm': id_sanpham,
                'Số lượng': so_luong,
                'Ngày lấy': row.get('Ngày lấy (tùy chọn)', row.get('Ngày lấy', None)),
                'Ghi chú': row.get('Ghi chú (tùy chọn)', row.get('Ghi chú', None)),
                'Loại đặt hàng': loai_dathang,
                'Khách vãng lai': khach_vang_lai,
                'Code cám được tạo': code_cam,  # Hiển thị cho user biết
                'Tên sản phẩm': ten_cam
            }
            result_data.append(item)
        else:
            not_found.append(ten_sanpham)
    
    conn.close()
    
    # Hiển thị thông báo
    if not_found:
        st.warning(f"⚠️ Không tìm thấy {len(not_found)} sản phẩm: {', '.join(not_found)}")
    
    if result_data:
        df_result = pd.DataFrame(result_data)
        
        # Thêm các trường bắt buộc cho database
        madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH', num_char=5)
        df_result['Mã đặt hàng'] = madathang
        df_result['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_result['Người tạo'] = st.session_state.username
        df_result['Thời gian tạo'] = fn.get_vietnam_time()
        
        # Hiển thị thông tin code cám được tạo
        st.success(f"✅ Đã xử lý thành công {len(result_data)} sản phẩm với mã: **{madathang}**")
        
        # Hiển thị preview
        with st.expander("📋 Xem trước dữ liệu được import"):
            display_cols = ['Tên sản phẩm', 'Code cám được tạo', 'Số lượng', 'Ngày lấy', 'Ghi chú']
            preview_df = df_result[display_cols].copy()
            st.dataframe(preview_df, use_container_width=True)
        
        # Chỉ return các cột cần thiết cho database (loại bỏ cột hiển thị)
        db_cols = ['ID sản phẩm', 'Số lượng', 'Ngày lấy', 'Ghi chú', 
                   'Loại đặt hàng', 'Khách vãng lai', 'Mã đặt hàng', 
                   'Ngày đặt', 'Người tạo', 'Thời gian tạo']
        return df_result[db_cols]
    
    return None

def process_import_by_code_cam(df, loai_dathang, khach_vang_lai=0):
    """Xử lý import Excel từ Code cám đầy đủ - định dạng cũ"""
    if 'Số lượng' not in df.columns:
        st.error("❌ File Excel phải có cột 'Số lượng'")
        return None
        
    # Lấy ID sản phẩm từ Code cám
    conn = sqlite3.connect('database_new.db')
    
    result_data = []
    not_found = []
    
    for idx, row in df.iterrows():
        code_cam = str(row['Code cám']).strip()
        so_luong = row['Số lượng']
        
        # Tìm ID sản phẩm
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM SanPham WHERE [Code cám] = ? AND [Đã xóa] = 0", (code_cam,))
        result = cursor.fetchone()
        
        if result:
            id_sanpham = result[0]
            
            item = {
                'ID sản phẩm': id_sanpham,
                'Số lượng': so_luong,
                'Ngày lấy': row.get('Ngày lấy', None),
                'Ghi chú': row.get('Ghi chú', None),
                'Loại đặt hàng': loai_dathang,
                'Khách vãng lai': khach_vang_lai
            }
            result_data.append(item)
        else:
            not_found.append(code_cam)
    
    conn.close()
    
    # Hiển thị thông báo
    if not_found:
        st.warning(f"⚠️ Không tìm thấy {len(not_found)} sản phẩm: {', '.join(not_found)}")
    
    if result_data:
        df_result = pd.DataFrame(result_data)
        
        # Tạo mã đặt hàng
        madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH', num_char=5)
        df_result['Mã đặt hàng'] = madathang
        df_result['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_result['Người tạo'] = st.session_state.username
        df_result['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.success(f"✅ Đã import {len(result_data)} sản phẩm với mã: **{madathang}**")
        return df_result
    
    return None

def app(selected):
    
    # Tạo 4 tabs cho các loại đặt hàng khác nhau
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Khách vãng lai",
        "🏪 Đại lý Bá Cang", 
        "🚛 Xe bồn Silo", 
        "📅 Forecast hàng tuần"
    ])
    
    # Lấy danh sách sản phẩm
    ds_sanpham = ss.get_columns_data(table_name='SanPham',
                                     columns=['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên', 'ID'],
                                     data_type='list',
                                     col_where={'Đã xóa':('=',0)})
    
    # TAB 1: Khách vãng lai
    with tab1:
        st.header("Đặt hàng Khách vãng lai")
        
        subtab1, subtab2 = st.tabs(["✍️ Nhập tay", "📁 Import Excel"])
        
        # Sub-tab: Nhập tay
        with subtab1:
            data = {
                'ID sản phẩm': [None],
                'Số lượng': [0],
                'Ngày lấy': [None],
                'Ghi chú': [None]
            }
            
            df = pd.DataFrame(data)
            
            column_config={
                'ID sản phẩm': st.column_config.SelectboxColumn('ID sản phẩm',options=ds_sanpham,format_func=lambda x: x,width='large'),
                'Số lượng': st.column_config.NumberColumn('Số lượng',min_value=0,step=1,format="%d",width='small'),
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='khach_vang_lai_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Khách vãng lai'
            df_insert['Khách vãng lai'] = 1
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm đơn hàng Khách vãng lai", disabled=disabled, type="primary", key='btn_khach_vang_lai_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab: Import Excel
        with subtab2:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_khach_vang_lai')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Khách vãng lai', khach_vang_lai=1)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_kvl'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
    
    # TAB 2: Đại lý Bá Cang
    with tab2:
        st.header("Đặt hàng Đại lý Bá Cang")
        st.info("🏪 Dữ liệu được lấy từ Forecast hàng tuần")
        
        # Nút xóa tất cả dữ liệu Bá Cang
        with st.expander("⚠️ Xóa tất cả dữ liệu Đại lý Bá Cang", expanded=False):
            st.warning("⚠️ Hành động này sẽ xóa **TẤT CẢ** dữ liệu Đại lý Bá Cang. Bạn có chắc chắn?")
            col_del1, col_del2 = st.columns([1, 3])
            with col_del1:
                if st.button("🗑️ Xóa tất cả", type="secondary", key="btn_delete_all_bacang"):
                    try:
                        from utils.bacang_importer import BaCangImporter
                        importer = BaCangImporter()
                        result = importer.delete_all_bacang_data()
                        
                        if result['success']:
                            st.success(f"✅ {result['message']}")
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi: {result['message']}")
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")
            with col_del2:
                st.caption("💡 Khi import tuần 3, dữ liệu tuần 3 cũ sẽ tự động bị ghi đè")
        
        subtab1, subtab2, subtab3 = st.tabs(["📁 Import từ Bá Cang", "✍️ Nhập tay", "📂 Import Excel khác"])
        
        # Sub-tab 1: Import từ file Bá Cang
        with subtab1:
            st.subheader("Import từ file KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG")
            st.caption("Đọc dữ liệu từ 2 bảng: Bảng 1 (K/L/M/N) và Bảng 2 (R/S/T)")
            
            try:
                from utils.bacang_importer import BaCangImporter
                
                importer = BaCangImporter()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    use_default = st.checkbox(
                        "Sử dụng file mặc định: EXCEL/KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG 2026.xlsm",
                        value=True,
                        key="bacang_use_default"
                    )
                    
                    if use_default:
                        file_path = "EXCEL/KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG 2026.xlsm"
                        st.info(f"📁 File: {file_path}")
                    else:
                        uploaded = st.file_uploader(
                            "Chọn file Excel Bá Cang",
                            type=['xlsx', 'xlsm'],
                            key="bacang_upload"
                        )
                        if uploaded:
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsm') as f:
                                f.write(uploaded.read())
                                file_path = f.name
                        else:
                            file_path = None
                
                if file_path:
                    try:
                        sheets = importer.get_available_sheets(file_path)
                        
                        with col2:
                            selected_sheet = st.selectbox(
                                "📅 Chọn tuần",
                                options=sheets,
                                index=0,
                                help="Mỗi sheet tương ứng với một tuần",
                                key="bacang_sheet_select"
                            )
                        
                        if selected_sheet:
                            st.subheader(f"📋 Preview dữ liệu {selected_sheet}")
                            
                            with st.spinner("Đang đọc dữ liệu..."):
                                preview_df1, preview_df2 = importer.preview_data(
                                    file_path=file_path,
                                    sheet_name=selected_sheet,
                                    limit=10
                                )
                            
                            col_preview1, col_preview2 = st.columns(2)
                            
                            with col_preview1:
                                st.markdown("**Bảng 1** - 🚛 Xe tải (bao 25kg)")
                                if len(preview_df1) > 0:
                                    st.dataframe(preview_df1, use_container_width=True)
                                else:
                                    st.info("Không có dữ liệu")
                            
                            with col_preview2:
                                st.markdown("**Bảng 2** - 🚛 Xe bồn (Silo)")
                                if len(preview_df2) > 0:
                                    st.dataframe(preview_df2, use_container_width=True)
                                else:
                                    st.info("Không có dữ liệu")
                            
                            if len(preview_df1) > 0 or len(preview_df2) > 0:
                                st.caption(f"Hiển thị tối đa 10 dòng đầu tiên mỗi bảng")
                                
                                col_btn1, col_btn2 = st.columns([1, 3])
                                
                                with col_btn1:
                                    if st.button("🚀 Import vào Database", type="primary", key="btn_import_bacang"):
                                        with st.spinner(f"Đang import dữ liệu {selected_sheet}..."):
                                            result = importer.import_bacang_data(
                                                file_path=file_path,
                                                sheet_name=selected_sheet,
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                        
                                        if result['success'] > 0:
                                            deleted_msg = ""
                                            if result.get('deleted', 0) > 0:
                                                deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                            
                                            st.success(
                                                f"{deleted_msg}"
                                                f"✅ Import thành công **{result['success']}** sản phẩm!\n\n"
                                                f"📦 Mã đặt hàng: **{result['ma_dathang']}**\n\n"
                                                f"📅 Sheet: **{result['sheet_name']}**"
                                            )
                                            st.balloons()
                                            
                                            if result['not_found']:
                                                with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã cám"):
                                                    for code in result['not_found'][:20]:
                                                        st.text(f"- {code}")
                                                    if len(result['not_found']) > 20:
                                                        st.text(f"... và {len(result['not_found']) - 20} mã khác")
                                        else:
                                            st.error("❌ Không import được sản phẩm nào!")
                                            if result['errors']:
                                                for err in result['errors']:
                                                    st.error(err)
                                            if result['not_found']:
                                                st.warning(f"Không tìm thấy {len(result['not_found'])} mã cám trong database")
                            else:
                                st.info("📅 Tuần này không có dữ liệu Bá Cang")
                                
                    except Exception as e:
                        st.error(f"❌ Lỗi đọc file: {e}")
                        import traceback
                        with st.expander("Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                            
            except ImportError as e:
                st.error(f"❌ Không thể import module: {e}")
        
        # Sub-tab 2: Nhập tay
        with subtab2:
            data = {
                'ID sản phẩm': [None],
                'Số lượng': [0],
                'Ngày lấy': [None],
                'Ghi chú': [None]
            }
            
            df = pd.DataFrame(data)
            
            column_config={
                'ID sản phẩm': st.column_config.SelectboxColumn('ID sản phẩm',options=ds_sanpham,format_func=lambda x: x,width='large'),
                'Số lượng': st.column_config.NumberColumn('Số lượng',min_value=0,step=1,format="%d",width='small'),
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='ba_cang_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Đại lý Bá Cang'
            df_insert['Khách vãng lai'] = 0
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm đơn hàng Bá Cang", disabled=disabled, type="primary", key='btn_ba_cang_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab 3: Import Excel khác
        with subtab3:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_ba_cang')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Đại lý Bá Cang', khach_vang_lai=0)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_bc'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
    
    # TAB 3: Xe bồn Silo
    with tab3:
        st.header("Đặt hàng Xe bồn Silo")
        st.info("🚛 Dữ liệu được lấy từ Forecast hàng tuần")
        
        subtab1, subtab2, subtab3 = st.tabs(["📁 Import từ SILO", "✍️ Nhập tay", "📂 Import Excel khác"])
        
        # Sub-tab 1: Import từ file SILO
        with subtab1:
            st.subheader("Import từ file SILO hàng tuần")
            
            try:
                from utils.silo_importer import SiloImporter
                
                importer = SiloImporter()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    use_default = st.checkbox(
                        "Sử dụng file mặc định: EXCEL/SILO W3-12-17-01-2026.xlsm",
                        value=True,
                        key="silo_use_default"
                    )
                    
                    if use_default:
                        file_path = "EXCEL/SILO W3-12-17-01-2026.xlsm"
                        st.info(f"📁 File: {file_path}")
                    else:
                        uploaded = st.file_uploader(
                            "Chọn file Excel SILO",
                            type=['xlsx', 'xlsm'],
                            key="silo_upload"
                        )
                        if uploaded:
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsm') as f:
                                f.write(uploaded.read())
                                file_path = f.name
                        else:
                            file_path = None
                
                if file_path:
                    try:
                        sheets = importer.get_available_sheets(file_path)
                        
                        with col2:
                            selected_sheet = st.selectbox(
                                "📅 Chọn tuần",
                                options=sheets,
                                index=len(sheets)-1 if sheets else 0,
                                help="Mỗi sheet tương ứng với một tuần",
                                key="silo_sheet_select"
                            )
                        
                        if selected_sheet:
                            st.subheader(f"📋 Preview dữ liệu {selected_sheet}")
                            
                            with st.spinner("Đang đọc dữ liệu..."):
                                preview_df = importer.preview_data(
                                    file_path=file_path,
                                    sheet_name=selected_sheet,
                                    limit=15
                                )
                            
                            if len(preview_df) > 0:
                                st.dataframe(
                                    preview_df,
                                    use_container_width=True,
                                    column_config={
                                        'Ngày lấy': st.column_config.TextColumn('Ngày lấy', width='small'),
                                        'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                        'Số lượng (tấn)': st.column_config.NumberColumn('Số lượng (tấn)', format='%.0f')
                                    }
                                )
                                
                                st.caption(f"Hiển thị tối đa 15 dòng đầu tiên")
                                
                                col_btn1, col_btn2 = st.columns([1, 3])
                                
                                with col_btn1:
                                    if st.button("🚀 Import vào Database", type="primary", key="btn_import_silo"):
                                        with st.spinner(f"Đang import dữ liệu {selected_sheet}..."):
                                            result = importer.import_silo_data(
                                                file_path=file_path,
                                                sheet_name=selected_sheet,
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                        
                                        if result['success'] > 0:
                                            deleted_msg = ""
                                            if result.get('deleted', 0) > 0:
                                                deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                            
                                            st.success(
                                                f"{deleted_msg}"
                                                f"✅ Import thành công **{result['success']}** sản phẩm!\n\n"
                                                f"📦 Mã đặt hàng: **{result['ma_dathang']}**\n\n"
                                                f"📅 {result['week_info']}"
                                            )
                                            st.balloons()
                                            
                                            if result['not_found']:
                                                with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã cám"):
                                                    for code in result['not_found'][:20]:
                                                        st.text(f"- {code}")
                                                    if len(result['not_found']) > 20:
                                                        st.text(f"... và {len(result['not_found']) - 20} mã khác")
                                        else:
                                            st.error("❌ Không import được sản phẩm nào!")
                                            if result['errors']:
                                                for err in result['errors']:
                                                    st.error(err)
                                            if result['not_found']:
                                                st.warning(f"Không tìm thấy {len(result['not_found'])} mã cám trong database")
                            else:
                                st.info("📅 Tuần này không có dữ liệu xe bồn silo")
                                
                    except Exception as e:
                        st.error(f"❌ Lỗi đọc file: {e}")
                        import traceback
                        with st.expander("Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                            
            except ImportError as e:
                st.error(f"❌ Không thể import module: {e}")
        
        # Sub-tab 2: Nhập tay
        with subtab2:
            data = {
                'ID sản phẩm': [None],
                'Số lượng': [0],
                'Ngày lấy': [None],
                'Ghi chú': [None]
            }
            
            df = pd.DataFrame(data)
            
            column_config={
                'ID sản phẩm': st.column_config.SelectboxColumn('ID sản phẩm',options=ds_sanpham,format_func=lambda x: x,width='large'),
                'Số lượng': st.column_config.NumberColumn('Số lượng',min_value=0,step=1,format="%d",width='small'),
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='xe_bon_silo_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Xe bồn Silo'
            df_insert['Khách vãng lai'] = 0
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm đơn hàng Xe bồn Silo", disabled=disabled, type="primary", key='btn_xe_bon_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab 3: Import Excel khác
        with subtab3:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_xe_bon')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Xe bồn Silo', khach_vang_lai=0)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_xb'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
    
    # TAB 4: Forecast hàng tuần (gửi vào thứ 6)
    with tab4:
        st.header("Forecast đặt hàng hàng tuần")
        st.info("📅 Forecast gửi vào ngày Thứ 6 hàng tuần")
        
        import datetime
        
        # Tính toán ngày thứ 6 tuần này
        today = fn.get_vietnam_time().date()
        weekday = today.weekday()  # 0 = Thứ 2, 4 = Thứ 6
        days_until_friday = (4 - weekday) % 7
        if days_until_friday == 0 and today.weekday() != 4:
            days_until_friday = 7
        next_friday = today + datetime.timedelta(days=days_until_friday)
        
        st.write(f"**Thứ 6 tuần này:** {next_friday.strftime('%d/%m/%Y')}")
        
        subtab1, subtab2, subtab3 = st.tabs(["📁 Import SALEFORECAST", "✍️ Nhập tay", "📂 Import Excel khác"])
        
        # Sub-tab 1: Import từ file SALEFORECAST
        with subtab1:
            st.subheader("Import từ file SALEFORECAST")
            
            try:
                from utils.forecast_importer import ForecastImporter
                
                importer = ForecastImporter()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    use_default = st.checkbox(
                        "Sử dụng file mặc định: EXCEL/W3.(12-17-01-) SALEFORECAST 2026.xlsm",
                        value=True,
                        key="forecast_use_default"
                    )
                    
                    if use_default:
                        file_path = "EXCEL/W3.(12-17-01-) SALEFORECAST 2026.xlsm"
                        st.info(f"📁 File: {file_path}")
                    else:
                        uploaded = st.file_uploader(
                            "Chọn file Excel SALEFORECAST",
                            type=['xlsx', 'xlsm'],
                            key="forecast_upload"
                        )
                        if uploaded:
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsm') as f:
                                f.write(uploaded.read())
                                file_path = f.name
                        else:
                            file_path = None
                
                if file_path:
                    try:
                        sheets = importer.get_available_sheets(file_path)
                        
                        with col2:
                            selected_sheet = st.selectbox(
                                "📅 Chọn tuần",
                                options=sheets,
                                index=len(sheets)-1 if sheets else 0,
                                help="Mỗi sheet tương ứng với một tuần"
                            )
                        
                        if selected_sheet:
                            st.subheader(f"📋 Preview dữ liệu {selected_sheet}")
                            
                            with st.spinner("Đang đọc dữ liệu..."):
                                preview_df = importer.preview_data(
                                    file_path=file_path,
                                    sheet_name=selected_sheet,
                                    limit=15
                                )
                            
                            if len(preview_df) > 0:
                                st.dataframe(
                                    preview_df,
                                    use_container_width=True,
                                    column_config={
                                        'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                        'Kích cỡ ép viên': st.column_config.TextColumn('Kích cỡ ép viên', width='small'),
                                        'Kích cỡ bao (kg)': st.column_config.TextColumn('Kích cỡ bao (kg)', width='small'),
                                        'Số lượng (tấn)': st.column_config.NumberColumn('Số lượng (tấn)', format='%.1f')
                                    }
                                )
                                
                                st.caption(f"Hiển thị tối đa 15 dòng đầu tiên")
                                
                                col_btn1, col_btn2 = st.columns([1, 3])
                                
                                with col_btn1:
                                    if st.button("🚀 Import vào Database", type="primary", key="btn_import_forecast"):
                                        with st.spinner(f"Đang import dữ liệu {selected_sheet}..."):
                                            result = importer.import_forecast_data(
                                                file_path=file_path,
                                                sheet_name=selected_sheet,
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                        
                                        if result['success'] > 0:
                                            deleted_msg = ""
                                            if result.get('deleted', 0) > 0:
                                                deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                            
                                            st.success(
                                                f"{deleted_msg}"
                                                f"✅ Import thành công **{result['success']}** sản phẩm!\n\n"
                                                f"📦 Mã Forecast: **{result['ma_forecast']}**\n\n"
                                                f"📅 {result['week_info']}"
                                            )
                                            st.balloons()
                                            
                                            if result['not_found']:
                                                with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã cám"):
                                                    for code in result['not_found'][:20]:
                                                        st.text(f"- {code}")
                                                    if len(result['not_found']) > 20:
                                                        st.text(f"... và {len(result['not_found']) - 20} mã khác")
                                        else:
                                            st.error("❌ Không import được sản phẩm nào!")
                                            if result['errors']:
                                                for err in result['errors']:
                                                    st.error(err)
                                            if result['not_found']:
                                                st.warning(f"Không tìm thấy {len(result['not_found'])} mã cám trong database")
                            else:
                                st.info("📅 Tuần này không có dữ liệu forecast")
                                
                    except Exception as e:
                        st.error(f"❌ Lỗi đọc file: {e}")
                        import traceback
                        with st.expander("Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                            
            except ImportError as e:
                st.error(f"❌ Không thể import module: {e}")
        
        # Sub-tab 2: Nhập tay
        with subtab2:
            data = {
                'ID sản phẩm': [None],
                'Số lượng': [0],
                'Ngày lấy': [next_friday],
                'Ghi chú': [None]
            }
            
            df = pd.DataFrame(data)
            
            column_config={
                'ID sản phẩm': st.column_config.SelectboxColumn('ID sản phẩm',options=ds_sanpham,format_func=lambda x: x,width='large'),
                'Số lượng': st.column_config.NumberColumn('Số lượng',min_value=0,step=1,format="%d",width='small'),
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='forecast_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Forecast tuần'
            df_insert['Khách vãng lai'] = 0
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm Forecast tuần", disabled=disabled, type="primary", key='btn_forecast_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab 3: Import Excel khác
        with subtab3:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_forecast')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Forecast tuần', khach_vang_lai=0)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_fc'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
        
        
    st.header("2. Danh sách đơn đặt hàng hiện tại")
    
    column_config = {
        'Ngày đặt': st.column_config.DateColumn('Ngày đặt', format='DD/MM/YYYY'),
        'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY'),
        'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
        'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss')
    }
    
    dataframe_with_selections(
        table_name="DatHang",
        columns=[
            'ID', 'ID sản phẩm', 'Mã đặt hàng', 'Loại đặt hàng', 'Số lượng', 'Ngày đặt', 'Ngày lấy', 
            'Khách vãng lai', 'Ghi chú', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'
        ],
        colums_disable=['ID','Mã đặt hàng','Ngày đặt','Người tạo','Thời gian tạo','Người sửa','Thời gian sửa','Fullname'],
        col_where={'Đã xóa': ('=', 0)},
        col_order={'ID': 'DESC'},
        joins = [
             {
                'table': 'SanPham',
                'on': {'ID sản phẩm': 'ID'},
                'columns': ['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên'],
                'replace_multi':{'ID sản phẩm':['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên']}
            }
        ],
        column_config=column_config,
        key=f'DatHang_{st.session_state.df_key}',
        join_user_info=True,
        allow_select_all=True)