import streamlit as st
from admin.sys_kde_components import *

# Mapping vật nuôi
VAT_NUOI_LABELS = {
    'H': 'HEO', 'G': 'GÀ', 'B': 'BÒ', 
    'V': 'VỊT', 'C': 'CÚT', 'D': 'DÊ'
}
def app(selected):
    
    # Hiển thị thông báo nếu đến từ Lịch tháng
    if 'filter_date' in st.session_state and st.session_state.filter_date:
        filter_date = st.session_state.filter_date
        # Parse date
        parts = filter_date.split('-')
        if len(parts) == 3:
            day = int(parts[2])
            month = int(parts[1])
            year = int(parts[0])
            
            st.info(f"""
            📅 **Bạn đến từ Lịch tháng - Ngày đã chọn: {day:02d}/{month:02d}/{year}**
            
            Dữ liệu bên dưới đang lọc theo ngày **{filter_date}**. 
            Nhấn nút bên dưới để xóa bộ lọc.
            """)
            
            if st.button("🔄 Xóa bộ lọc ngày", key="clear_filter_packing"):
                st.session_state.filter_date = None
                st.session_state.navigate_to = None
                st.rerun()
    
    # Tabs: Import Excel đưa lên đầu
    tab1, tab2 = st.tabs(["📁 Import Excel", "📝 Nhập thủ công"])
    
    with tab1:
        st.header("Import Packing từ file DAILY PACKING")
        
        st.markdown("""
        **Import sản lượng đóng bao từ file Excel DAILY PACKING**
        - Chọn file Excel chứa dữ liệu packing theo ngày
        - Chọn ngày (sheet) cần import
        - Preview và xác nhận trước khi import
        """)
        
        try:
            from utils.packing_importer import PackingImporter
            
            importer = PackingImporter()
            
            # File selector
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Sử dụng file mặc định hoặc upload
                use_default = st.checkbox(
                    "Sử dụng file mặc định: EXCEL/DAILY PACKING THANG 1.2026.xlsm",
                    value=True
                )
                
                if use_default:
                    file_path = "EXCEL/DAILY PACKING THANG 1.2026.xlsm"
                    st.info(f"📁 File: {file_path}")
                else:
                    uploaded = st.file_uploader(
                        "Chọn file Excel DAILY PACKING",
                        type=['xlsx', 'xlsm']
                    )
                    if uploaded:
                        # Save to temp
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsm') as f:
                            f.write(uploaded.read())
                            file_path = f.name
                    else:
                        file_path = None
            
            if file_path:
                # Lấy danh sách sheets
                try:
                    sheets = importer.get_available_sheets(file_path)
                    
                    with col2:
                        selected_sheet = st.selectbox(
                            "📅 Chọn ngày",
                            options=sheets,
                            format_func=lambda x: f"Ngày {x}",
                            help="Mỗi sheet tương ứng với một ngày trong tháng"
                        )
                    
                    if selected_sheet:
                        # Preview data
                        st.subheader(f"📋 Preview dữ liệu ngày {selected_sheet}")
                        
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
                                    'Kích cỡ bao (kg)': st.column_config.TextColumn('Kích cỡ bao (kg)', width='small'),
                                    'Số lượng bao': st.column_config.NumberColumn('Số lượng bao', format='%d'),
                                    'Số lượng (kg)': st.column_config.NumberColumn('Số lượng (kg)', format='%.0f')
                                }
                            )
                            
                            st.caption(f"Hiển thị tối đa 15 dòng đầu tiên")
                            
                            # Import button
                            col_btn1, col_btn2 = st.columns([1, 3])
                            
                            with col_btn1:
                                if st.button("🚀 Import vào Database", type="primary"):
                                    with st.spinner(f"Đang import dữ liệu ngày {selected_sheet}..."):
                                        result = importer.import_packing_data(
                                            file_path=file_path,
                                            sheet_name=selected_sheet,
                                            nguoi_import=st.session_state.get('username', 'system'),
                                            year=2026,
                                            month=1
                                        )
                                    
                                    if result['success'] > 0:
                                        deleted_msg = ""
                                        if result.get('deleted', 0) > 0:
                                            deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                        
                                        st.success(
                                            f"{deleted_msg}"
                                            f"✅ Import thành công **{result['success']}** sản phẩm!\n\n"
                                            f"📦 Mã Packing: **{result['ma_packing']}**\n\n"
                                            f"📅 Ngày: **{result['ngay_packing']}**"
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
                            st.info("📅 Ngày này không có dữ liệu đóng bao")
                            
                except Exception as e:
                    st.error(f"❌ Lỗi đọc file: {e}")
                    import traceback
                    with st.expander("Chi tiết lỗi"):
                        st.code(traceback.format_exc())
                        
        except ImportError as e:
            st.error(f"❌ Không thể import module: {e}")
    
    
    with tab2:
        st.header("1. Packing")
        # Code cám	Tên cám	Kích cỡ ép viên	Dạng ép viên	Kích cỡ đóng bao	Pellet	Packing	Batch size
        
        ds_sanpham = ss.get_columns_data(table_name='SanPham',
                                         columns=['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên', 'ID'],
                                         data_type='list',
                                         col_where={'Đã xóa':('=',0)})
                                         
        
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
            'Ngày lấy': st.column_config.DatetimeColumn('Ngày lấy',width='medium'),
            'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
        }
        
        df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config)
        
        # Chỉ lấy các dòng có Sản phẩm khác None và Số lượng > 0
        df_insert = df_insert.dropna(subset=['ID sản phẩm'])
        df_insert = df_insert[df_insert['Số lượng'] > 0]
        
        
        mapacking = ss.generate_next_code(tablename='Packing', column_name='Mã packing', prefix='PK',num_char=5)
        st.write(f'Mã packing tự động: **{mapacking}**')
        
        df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)

        df_insert['Mã packing'] = mapacking
        df_insert['Ngày packing'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_insert['Người tạo'] = st.session_state.username
        df_insert['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.dataframe(df_insert, width='content')
        
        disabled = not (len(df_insert) > 0)
        
        if st.button("Thêm sản phẩm", disabled=disabled, type="primary"):
            result = ss.insert_data_to_sql_server(table_name='Packing',dataframe=df_insert)
            show_notification("Lỗi:", result)
    
    
    st.header("2. Danh sách packing hiện tại")
    
    # Khởi tạo session state cho filter vật nuôi
    if 'filter_vatnuoi_packing' not in st.session_state:
        st.session_state.filter_vatnuoi_packing = None
    
    # Tạo các nút lọc theo vật nuôi
    filter_cols = st.columns(7)
    with filter_cols[0]:
        btn_style = "primary" if st.session_state.filter_vatnuoi_packing is None else "secondary"
        if st.button("📦 Tất cả", use_container_width=True, type=btn_style, key="packing_filter_all"):
            st.session_state.filter_vatnuoi_packing = None
            st.rerun()
    
    for idx, (code, label) in enumerate(VAT_NUOI_LABELS.items()):
        with filter_cols[idx + 1]:
            btn_style = "primary" if st.session_state.filter_vatnuoi_packing == code else "secondary"
            if st.button(label, use_container_width=True, type=btn_style, key=f"packing_filter_{code}"):
                st.session_state.filter_vatnuoi_packing = code
                st.rerun()
    
    # Xây dựng điều kiện lọc
    col_where = {'Đã xóa': ('=', 0)}
    
    # Nếu có filter_date từ Lịch tháng, thêm điều kiện lọc theo ngày
    if 'filter_date' in st.session_state and st.session_state.filter_date:
        col_where['Ngày packing'] = ('=', st.session_state.filter_date)
    
    # Thêm điều kiện lọc theo vật nuôi nếu có
    if st.session_state.filter_vatnuoi_packing:
        col_where['SanPham.Vật nuôi'] = ('=', st.session_state.filter_vatnuoi_packing)
    
    # Xây dựng joins
    join_config = {
        'table': 'SanPham',
        'on': {'ID sản phẩm': 'ID'},
        'columns': ['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên'],
        'replace_multi':{'ID sản phẩm':['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên']}
    }
    
    dataframe_with_selections(
        table_name="Packing",
        columns=[
            'ID', 'ID sản phẩm', 'Mã packing', 'Số lượng', 'Ngày lấy', 'Khách vãng lai', 'Ghi chú',
            'Người tạo', 'Thời gian tạo'
        ],
        colums_disable=['ID','Mã packing','Người tạo','Thời gian tạo'],
        col_where=col_where,
        col_order={'ID': 'DESC'},
        joins = [join_config],
        # column_config=column_config,
        key=f'Packing_{st.session_state.df_key}',
        join_user_info=False)

