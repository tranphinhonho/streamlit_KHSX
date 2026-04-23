import streamlit as st
import re
from pathlib import Path
from admin.sys_kde_components import *
from utils.import_notification import send_import_notification

def _extract_month_year_from_filename(filename: str):
    """Trích xuất tháng và năm từ tên file DAILY SALED REPORT THANG X.YYYY"""
    match = re.search(r'THANG\s*(\d{1,2})[.\s]*(\d{4})', filename, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def _find_sale_report_files():
    """Tìm tất cả file DAILY SALED REPORT trong folder EXCEL"""
    excel_folder = Path("D:/PYTHON/B7KHSX/EXCEL")
    files = list(excel_folder.glob("DAILY SALED REPORT*.xls*"))
    return sorted(files, reverse=True)

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
            
            if st.button("🔄 Xóa bộ lọc ngày", key="clear_filter_sale"):
                st.session_state.filter_date = None
                st.session_state.navigate_to = None
                st.rerun()
    
    # Tabs: Import Excel đưa lên đầu
    tab1, tab2 = st.tabs(["📁 Import Excel", "📝 Nhập thủ công"])
    
    with tab1:
        st.header("Import Sale từ file DAILY SALED REPORT")
        
        st.markdown("""
        **Import sản lượng bán hàng từ file Excel DAILY SALED REPORT**
        - Chọn file Excel chứa dữ liệu sale theo ngày
        - Chọn ngày (sheet) cần import
        - Preview và xác nhận trước khi import
        """)
        
        try:
            from utils.sale_importer import SaleImporter
            
            importer = SaleImporter()
            
            # Tìm file DAILY SALED REPORT trong folder EXCEL
            available_files = _find_sale_report_files()
            
            # File selector
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Tìm file mặc định mới nhất
                if available_files:
                    default_file = available_files[0]  # File mới nhất
                    default_name = default_file.name
                else:
                    default_file = None
                    default_name = "Không tìm thấy file"
                
                use_default = st.checkbox(
                    f"Sử dụng file mặc định: EXCEL/{default_name}",
                    value=True
                )
                
                if use_default:
                    if default_file:
                        file_path = str(default_file)
                        file_name_for_date = default_name
                        st.info(f"📁 File: EXCEL/{default_name}")
                    else:
                        file_path = None
                        file_name_for_date = ""
                        st.warning("📭 Không tìm thấy file DAILY SALED REPORT trong folder EXCEL")
                else:
                    uploaded = st.file_uploader(
                        "Chọn file Excel DAILY SALED REPORT",
                        type=['xlsx', 'xlsm']
                    )
                    if uploaded:
                        file_name_for_date = uploaded.name
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsm') as f:
                            f.write(uploaded.read())
                            file_path = f.name
                    else:
                        file_path = None
                        file_name_for_date = ""
            
            if file_path:
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
                        st.subheader(f"📋 Preview dữ liệu ngày {selected_sheet}")
                        
                        with st.spinner("Đang đọc dữ liệu..."):
                            preview_df = importer.preview_data(
                                file_path=file_path,
                                sheet_name=selected_sheet,
                                limit=None  # Hiển thị tất cả
                            )
                        
                        if len(preview_df) > 0:
                            st.dataframe(
                                preview_df,
                                width="stretch",
                                column_config={
                                    'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                    'Kích cỡ bao (kg)': st.column_config.TextColumn('Kích cỡ bao (kg)', width='small'),
                                    'Số lượng bao': st.column_config.NumberColumn('Số lượng bao', format='%d'),
                                    'Số lượng (kg)': st.column_config.NumberColumn('Số lượng (kg)', format='%.0f')
                                }
                            )
                            
                            # Tính tổng sản lượng từ preview
                            total_kg = preview_df['Số lượng (kg)'].sum()
                            
                            # Lấy giá trị tổng từ Excel M4
                            excel_total = importer.get_excel_total(
                                file_path=file_path,
                                sheet_name=selected_sheet
                            )
                            
                            st.caption(f"Tổng cộng: {len(preview_df)} dòng dữ liệu")
                            st.caption(f"📊 **Tổng sản lượng (tính từ preview):** {total_kg:,.0f} kg")
                            if excel_total is not None:
                                st.caption(f"📋 **Tổng sản lượng Excel (ô M4):** {excel_total:,.0f} kg")
                                # Kiểm tra chênh lệch
                                if abs(total_kg - excel_total) > 1:
                                    st.warning(f"⚠️ Chênh lệch: {abs(total_kg - excel_total):,.0f} kg (có thể do mã cám không tìm thấy)")
                            
                            col_btn1, col_btn2 = st.columns([1, 3])
                            
                            with col_btn1:
                                if st.button("🚀 Import vào Database", type="primary"):
                                    with st.spinner(f"Đang import dữ liệu ngày {selected_sheet}..."):
                                        # Trích xuất tháng/năm từ tên file
                                        sale_month, sale_year = _extract_month_year_from_filename(file_name_for_date)
                                        if not sale_month or not sale_year:
                                            st.error("❌ Không thể trích xuất tháng/năm từ tên file. Tên file phải chứa 'THANG X.YYYY'")
                                            st.stop()
                                        
                                        result = importer.import_sale_data(
                                            file_path=file_path,
                                            sheet_name=selected_sheet,
                                            nguoi_import=st.session_state.get('username', 'system'),
                                            year=sale_year,
                                            month=sale_month
                                        )
                                    
                                    if result['success'] > 0:
                                        deleted_msg = ""
                                        if result.get('deleted', 0) > 0:
                                            deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                        
                                        st.success(
                                            f"{deleted_msg}"
                                            f"✅ Import thành công **{result['success']}** sản phẩm!\n\n"
                                            f"📦 Mã Sale: **{result['ma_sale']}**\n\n"
                                            f"📅 Ngày: **{result['ngay_sale']}**"
                                        )
                                        st.balloons()
                                        
                                        if result['not_found']:
                                            with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã cám"):
                                                for code in result['not_found'][:20]:
                                                    st.text(f"- {code}")
                                                if len(result['not_found']) > 20:
                                                    st.text(f"... và {len(result['not_found']) - 20} mã khác")
                                            
                                            # Gửi email thông báo
                                            email_sent = send_import_notification(
                                                not_found_codes=result['not_found'],
                                                filename=file_path,
                                                import_type='SALE',
                                                ngay_import=result.get('ngay_sale', ''),
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                            if email_sent:
                                                st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                    else:
                                        st.error("❌ Không import được sản phẩm nào!")
                                        if result['errors']:
                                            for err in result['errors']:
                                                st.error(err)
                                        if result['not_found']:
                                            st.warning(f"Không tìm thấy {len(result['not_found'])} mã cám trong database")
                                            # Gửi email thông báo
                                            email_sent = send_import_notification(
                                                not_found_codes=result['not_found'],
                                                filename=file_path,
                                                import_type='SALE',
                                                ngay_import='',
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                            if email_sent:
                                                st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                        else:
                            st.info("📅 Ngày này không có dữ liệu bán hàng")
                            
                except Exception as e:
                    st.error(f"❌ Lỗi đọc file: {e}")
                    import traceback
                    with st.expander("Chi tiết lỗi"):
                        st.code(traceback.format_exc())
                        
        except ImportError as e:
            st.error(f"❌ Không thể import module: {e}")
    
    
    with tab2:
        st.header("1. Sale")
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
        
        
        masale = ss.generate_next_code(tablename='Sale', column_name='Mã sale', prefix='SL',num_char=5)
        st.write(f'Mã sale tự động: **{masale}**')
        
        df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)

        df_insert['Mã sale'] = masale
        df_insert['Ngày sale'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_insert['Người tạo'] = st.session_state.username
        df_insert['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.dataframe(df_insert, width='content')
        
        disabled = not (len(df_insert) > 0)
        
        if st.button("Thêm sản phẩm", disabled=disabled, type="primary"):
            result = ss.insert_data_to_sql_server(table_name='Sale',dataframe=df_insert)
            show_notification("Lỗi:", result)
    
    
    
    st.header("2. Danh sách sale hiện tại")
    
    # Khởi tạo session state cho filter vật nuôi
    if 'filter_vatnuoi_sale' not in st.session_state:
        st.session_state.filter_vatnuoi_sale = None
    
    # Tạo các nút lọc theo vật nuôi
    filter_cols = st.columns(7)
    with filter_cols[0]:
        btn_style = "primary" if st.session_state.filter_vatnuoi_sale is None else "secondary"
        if st.button("📦 Tất cả", width="stretch", type=btn_style, key="sale_filter_all"):
            st.session_state.filter_vatnuoi_sale = None
            st.rerun()
    
    for idx, (code, label) in enumerate(VAT_NUOI_LABELS.items()):
        with filter_cols[idx + 1]:
            btn_style = "primary" if st.session_state.filter_vatnuoi_sale == code else "secondary"
            if st.button(label, width="stretch", type=btn_style, key=f"sale_filter_{code}"):
                st.session_state.filter_vatnuoi_sale = code
                st.rerun()
    
    # Filter theo ngày
    col_date, col_search = st.columns([1, 3])
    with col_date:
        selected_date = st.date_input(
            "Lọc theo ngày",
            value=None,
            format="YYYY/MM/DD",
            key="sale_date_filter"
        )
        if selected_date:
            st.session_state.filter_date = selected_date.strftime('%Y-%m-%d')
            # Khi lọc theo ngày, mặc định hiển thị tất cả
            st.session_state.page_size = 'All'
        elif 'filter_date' in st.session_state and st.session_state.get('filter_date'):
            pass
    
    # Xây dựng điều kiện lọc
    col_where = {'Đã xóa': ('=', 0)}
    
    # Nếu có filter_date từ Lịch tháng, thêm điều kiện lọc theo ngày
    if 'filter_date' in st.session_state and st.session_state.filter_date:
        col_where['Ngày sale'] = ('=', st.session_state.filter_date)
    
    # Thêm điều kiện lọc theo vật nuôi nếu có
    if st.session_state.filter_vatnuoi_sale:
        col_where['SanPham.Vật nuôi'] = ('=', st.session_state.filter_vatnuoi_sale)
    
    # Xây dựng joins
    join_config = {
        'table': 'SanPham',
        'on': {'ID sản phẩm': 'ID'},
        'columns': ['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên'],
        'replace_multi':{'ID sản phẩm':['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên']}
    }
    
    dataframe_with_selections(
        table_name="Sale",
        columns=[
            'ID', 'ID sản phẩm', 'Mã sale', 'Số lượng', 'Ngày lấy', 'Khách vãng lai', 'Ghi chú',
            'Người tạo', 'Thời gian tạo'
        ],
        colums_disable=['ID','Mã sale','Người tạo','Thời gian tạo'],
        col_where=col_where,
        col_order={'ID': 'DESC'},
        joins = [join_config],
        # column_config=column_config,
        key=f'Sale_{st.session_state.df_key}',
        join_user_info=False)

