import streamlit as st
from admin.sys_kde_components import *
import pandas as pd
from datetime import datetime, timedelta
from utils.import_notification import send_import_notification

# Loại sản phẩm
LOAI_SAN_PHAM = ['Thành phẩm', 'Bán thành phẩm']

# Trạng thái
TRANG_THAI_OPTIONS = [
    'Chờ đóng bao 25kg',
    'Chờ đóng bao 50kg', 
    'Chờ xe Silo',
    'Chờ ép viên',
    'Đang xử lý'
]

# Số bồn (có thể tùy chỉnh)
SO_BON_OPTIONS = [f'Bồn {i}' for i in range(1, 21)]  # Bồn 1-20

# Ca sản xuất
CA_SAN_XUAT = ['Ca 1', 'Ca 2', 'Ca 3']

def app(selected):
    
    # Tạo tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Danh sách Tồn bồn",
        "📁 Import Excel",
        "✍️ Nhập thủ công"
    ])
    
    # TAB 3: Nhập thủ công
    with tab3:
        st.header("✍️ Nhập Tồn bồn thủ công")
        
        st.info("""
        **Tồn bồn** theo dõi sản phẩm trong các bồn chứa:
        - **Bán thành phẩm**: Sau Batching, chờ ép viên
        - **Thành phẩm**: Chờ đóng bao (25/50 kg) hoặc chờ xe Silo lấy
        """)
        
        # Lấy danh sách sản phẩm
        ds_sanpham = ss.get_columns_data(
            table_name='SanPham',
            columns=['Code cám', 'Tên cám', 'ID'],
            data_type='list',
            col_where={'Đã xóa': ('=', 0)}
        )
        
        # Form nhập liệu
        col1, col2 = st.columns(2)
        
        with col1:
            ngay_kiem = st.date_input(
                "📅 Ngày kiểm kho",
                value=fn.get_vietnam_time().date() - timedelta(days=1),
                help="Ngày kiểm tra tồn bồn (mặc định: N-1)"
            )
            
            loai_sp = st.selectbox(
                "📦 Loại sản phẩm",
                options=LOAI_SAN_PHAM,
                help="Thành phẩm hoặc Bán thành phẩm"
            )
            
            so_bon = st.selectbox(
                "🛢️ Số bồn",
                options=SO_BON_OPTIONS,
                help="Chọn bồn chứa"
            )
        
        with col2:
            so_luong = st.number_input(
                "⚖️ Số lượng (kg)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="Số lượng trong bồn (kg)"
            )
            
            # Trạng thái tùy theo loại sản phẩm
            if loai_sp == 'Bán thành phẩm':
                trang_thai_options = ['Chờ ép viên', 'Đang xử lý']
            else:
                trang_thai_options = ['Chờ đóng bao 25kg', 'Chờ đóng bao 50kg', 'Chờ xe Silo', 'Đang xử lý']
            
            trang_thai = st.selectbox(
                "📍 Trạng thái",
                options=trang_thai_options,
                help="Trạng thái hiện tại"
            )
            
            ca_sx = st.selectbox(
                "🕐 Ca sản xuất",
                options=CA_SAN_XUAT,
                help="Ca kiểm kho"
            )
        
        # Chọn sản phẩm
        san_pham = st.selectbox(
            "🏷️ Sản phẩm",
            options=ds_sanpham,
            help="Chọn sản phẩm"
        )
        
        ghi_chu = st.text_area(
            "📝 Ghi chú",
            placeholder="Nhập ghi chú nếu có...",
            height=80
        )
        
        # Nút lưu
        if st.button("💾 Lưu Tồn bồn", type="primary", width="stretch"):
            if san_pham and so_luong > 0:
                # Tách ID sản phẩm
                id_san_pham = san_pham.split('|')[-1].strip() if '|' in san_pham else None
                
                # Tạo mã tự động
                ma_tonbon = ss.generate_next_code(
                    tablename='TonBon',
                    column_name='Mã tồn bồn',
                    prefix='TB',
                    num_char=5
                )
                
                # Xác định kích cỡ đóng bao từ trạng thái
                if '25kg' in trang_thai:
                    kich_co = '25 kg'
                elif '50kg' in trang_thai:
                    kich_co = '50 kg'
                elif 'Silo' in trang_thai:
                    kich_co = 'Silo'
                else:
                    kich_co = 'N/A'
                
                # Tạo dataframe để insert
                df_insert = pd.DataFrame([{
                    'Mã tồn bồn': ma_tonbon,
                    'Ngày kiểm kho': ngay_kiem,
                    'ID sản phẩm': id_san_pham,
                    'Loại sản phẩm': loai_sp,
                    'Số lượng (kg)': so_luong,
                    'Số bồn': so_bon,
                    'Trạng thái': trang_thai,
                    'Kích cỡ đóng bao': kich_co,
                    'Ca sản xuất': ca_sx,
                    'Ghi chú': ghi_chu if ghi_chu else None,
                    'Người tạo': st.session_state.username,
                    'Thời gian tạo': fn.get_vietnam_time()
                }])
                
                result = ss.insert_data_to_sql_server(table_name='TonBon', dataframe=df_insert)
                show_notification("Lỗi:", result)
                
                if result[0]:
                    st.success(f"✅ Đã lưu! Mã: **{ma_tonbon}**")
                    st.session_state.df_key += 1
            else:
                st.error("Vui lòng chọn sản phẩm và nhập số lượng > 0!")
    
    # TAB 2: Import từ Báo cáo tồn bồn
    with tab2:
        st.header("📁 Import từ Báo cáo tồn bồn")
        
        # Chọn nguồn dữ liệu
        data_source = st.radio(
            "🔌 Nguồn dữ liệu",
            options=["📁 File local", "📧 Từ email (Tồn bồn folder)"],
            index=1,  # Mặc định chọn "Từ email"
            horizontal=True,
            key="tonbon_data_source"
        )
        
        # Import TonBonImporter
        try:
            from utils.tonbon_importer import TonBonImporter
            importer = TonBonImporter()
            
            excel_path = None
            
            if "📧" in data_source:
                # Lấy file từ email
                st.info("📧 Lấy file từ folder **Tồn bồn** trong mailbox mixer2@cp.com.vn")
                
                try:
                    from utils.email_receiver import EmailReceiver
                    receiver = EmailReceiver()
                    
                    # Nút tìm email
                    if st.button("🔄 Tìm email báo cáo tồn bồn", width="stretch"):
                        with st.spinner("Đang kết nối Outlook..."):
                            emails = receiver.get_tonbon_emails(days_back=7)
                            if emails:
                                # Lưu vào session state
                                st.session_state['tonbon_emails'] = emails
                                st.session_state['tonbon_receiver'] = receiver
                                st.success(f"✅ Tìm thấy {len(emails)} email")
                            else:
                                st.warning("⚠️ Không tìm thấy email báo cáo tồn bồn trong 7 ngày qua")
                    
                    # Hiển thị email đã tìm thấy
                    if st.session_state.get('tonbon_emails'):
                        emails = st.session_state['tonbon_emails']
                        
                        # Cho phép chọn email trong danh sách
                        email_options = [
                            f"[{i+1}] {e['sender']} - {e['received_time'][:16]}"
                            for i, e in enumerate(emails)
                        ]
                        
                        selected_idx = st.selectbox(
                            "📧 Chọn email để xem chi tiết",
                            options=range(len(emails)),
                            format_func=lambda x: email_options[x],
                            key="tonbon_email_select"
                        )
                        
                        selected_email = emails[selected_idx]
                        
                        st.markdown(f"**📬 Tiêu đề:** {selected_email['subject']}")
                        st.markdown(f"**👤 Từ:** {selected_email['sender']}")
                        st.markdown(f"**📅 Ngày:** {selected_email['received_time']}")
                        
                        if selected_email.get('tonbon_files'):
                            file_info = selected_email['tonbon_files'][0]
                            st.markdown(f"**📎 File:** {file_info['filename']}")
                            
                            # Nút tải file (riêng biệt)
                            if st.button("📥 Tải và sử dụng file này", type="primary", key="btn_download_tonbon"):
                                try:
                                    with st.spinner("Đang tải file..."):
                                        downloaded = receiver.download_attachment(
                                            selected_email, file_info, subfolder="tonbon"
                                        )
                                        if downloaded:
                                            st.session_state['tonbon_excel_path'] = str(downloaded)
                                            st.success(f"✅ Đã tải: {downloaded}")
                                            st.rerun()
                                        else:
                                            st.error("❌ Lỗi tải file!")
                                except Exception as e:
                                    st.error(f"❌ Lỗi: {e}")
                                
                except ImportError as e:
                    st.error(f"❌ Lỗi import EmailReceiver: {e}")
                
                # Sử dụng file đã download
                if st.session_state.get('tonbon_excel_path'):
                    excel_path = st.session_state['tonbon_excel_path']
                    st.info(f"📄 Đang sử dụng file: `{excel_path}`")
                    
            else:
                # File local - tìm file mới nhất (hỗ trợ cả tên có dấu và không dấu)
                from pathlib import Path
                excel_folder = Path("D:/PYTHON/B7KHSX/EXCEL")
                tonbon_files = []
                # Tìm cả file có dấu và không dấu
                tonbon_files.extend(excel_folder.glob("Báo cáo tồn bồn thành phẩm*.*"))
                tonbon_files.extend(excel_folder.glob("Bao cao ton bon thanh pham*.*"))
                # Loại bỏ file Copy/backup
                tonbon_files = [f for f in tonbon_files if not f.name.startswith("Copy")]
                tonbon_files = sorted(tonbon_files, key=lambda f: f.name, reverse=True)
                
                if tonbon_files:
                    excel_path = str(tonbon_files[0])
                    st.markdown(f"**📄 File:** `EXCEL/{tonbon_files[0].name}`")
                else:
                    excel_path = None
                    st.warning("📭 Không tìm thấy file Báo cáo tồn bồn thành phẩm trong folder EXCEL")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ngay_kiem = st.date_input(
                    "📅 Ngày kiểm kho",
                    value=fn.get_vietnam_time().date() - timedelta(days=1),
                    help="Ngày kiểm tra tồn bồn (mặc định: N-1)",
                    key="import_ngay_kiem"
                )
            
            with col2:
                loai_sp = st.selectbox(
                    "📦 Loại sản phẩm",
                    options=LOAI_SAN_PHAM,
                    help="Thành phẩm hoặc Bán thành phẩm",
                    key="import_loai_sp"
                )
            
            # Chỉ hiển thị nút nếu có file path
            if excel_path:
                # Chọn chế độ import
                import_mode = st.radio(
                    "📌 Chế độ import",
                    options=["Import tất cả ngày (1-31)", "Import 1 ngày cụ thể"],
                    horizontal=True,
                    help="Chọn cách import dữ liệu"
                )
                
                if import_mode == "Import tất cả ngày (1-31)":
                    # Nút đọc tất cả sheets
                    if st.button("⚡ Xem trước tất cả ngày", type="primary", width="stretch"):
                        with st.spinner("📖 Đang đọc dữ liệu từ tất cả sheets (1-31)..."):
                            df_preview = importer.read_all_sheets_with_dates(excel_path)
                            
                            if len(df_preview) > 0:
                                unique_days = df_preview['Ngày'].nunique()
                                st.success(f"✅ Đọc được {len(df_preview)} dòng từ {unique_days} ngày")
                                
                                # Thống kê theo ngày
                                stats = df_preview.groupby('Ngày')['Số lượng (kg)'].sum().reset_index()
                                stats.columns = ['Ngày', 'Tổng kg']
                                st.dataframe(stats, width="stretch")
                                
                                st.metric("Tổng khối lượng", f"{df_preview['Số lượng (kg)'].sum():,.0f} kg")
                                
                                st.session_state['tonbon_preview_all'] = df_preview
                            else:
                                st.warning("⚠️ Không tìm thấy dữ liệu trong các sheet 1-31")
                else:
                    # Nút đọc 1 sheet cụ thể
                    if st.button("⚡ Xem trước dữ liệu (1 ngày)", type="primary", width="stretch"):
                        with st.spinner("📖 Đang đọc dữ liệu..."):
                            # Đọc từ sheet có tên = ngày
                            day_num = ngay_kiem.day
                            df_preview = importer.read_direct_from_cells(excel_path, sheet_index=str(day_num))
                            
                            if len(df_preview) > 0:
                                st.success(f"✅ Đọc được {len(df_preview)} mã sản phẩm (ngày {day_num})")
                                
                                total_kg = df_preview['Số lượng (kg)'].sum()
                                st.metric("Tổng khối lượng", f"{total_kg:,.0f} kg")
                                
                                st.dataframe(
                                    df_preview,
                                    width="stretch",
                                    column_config={
                                        'Số lượng (kg)': st.column_config.NumberColumn(format="%,.0f")
                                    }
                                )
                                
                                st.session_state['tonbon_preview'] = df_preview
                            else:
                                st.warning(f"⚠️ Không tìm thấy dữ liệu ở sheet '{day_num}'")
            else:
                st.warning("⚠️ Chưa có file. Nhấn 'Tìm email' rồi 'Tải file' để bắt đầu.")
            
            # Nút Import
            st.markdown("---")
            
            if excel_path:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    overwrite = st.checkbox("🔄 Ghi đè dữ liệu cũ", value=True, help="Mặc định bật: Dữ liệu ngày cũ sẽ bị thay thế khi import lại")
                
                with col_btn2:
                    pass
                
                if import_mode == "Import tất cả ngày (1-31)":
                    if st.button("📥 Import TẤT CẢ các ngày", type="primary", width="stretch"):
                        with st.spinner("Đang import tất cả ngày..."):
                            result = importer.import_all_days(
                                file_path=excel_path,
                                nguoi_import=st.session_state.username,
                                loai_san_pham=loai_sp,
                                overwrite=overwrite
                            )
                            
                            if result['success'] > 0:
                                st.success(f"✅ Import thành công **{result['success']}** dòng từ **{result.get('days_imported', 'N/A')}** ngày!")
                                st.balloons()
                                st.session_state.df_key += 1
                                
                                if result['not_found']:
                                    with st.expander(f"⚠️ {len(result['not_found'])} mã không tìm thấy", expanded=True):
                                        for code in result['not_found'][:20]:
                                            st.markdown(f"- `{code}`")
                                    
                                    # Gửi email thông báo
                                    email_sent = send_import_notification(
                                        not_found_codes=result['not_found'],
                                        filename=excel_path,
                                        import_type='TONBON',
                                        ngay_import='',
                                        nguoi_import=st.session_state.username
                                    )
                                    if email_sent:
                                        st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                            else:
                                if result['not_found']:
                                    st.error(f"❌ Không import được. {len(result['not_found'])} mã không tìm thấy trong database.")
                                    # Gửi email thông báo
                                    email_sent = send_import_notification(
                                        not_found_codes=result['not_found'],
                                        filename=excel_path,
                                        import_type='TONBON',
                                        ngay_import='',
                                        nguoi_import=st.session_state.username
                                    )
                                    if email_sent:
                                        st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                else:
                                    st.error(f"❌ Lỗi: {result.get('errors', 'Unknown')}")
                else:
                    if st.button("📥 Import vào Database (1 ngày)", type="primary", width="stretch"):
                        with st.spinner("Đang import..."):
                            result = importer.import_tonbon(
                                file_path=excel_path,
                                ngay_kiem=ngay_kiem.strftime('%Y-%m-%d'),
                                nguoi_import=st.session_state.username,
                                loai_san_pham=loai_sp,
                                overwrite=overwrite
                            )
                            
                            if result['success'] > 0:
                                st.success(f"✅ Import thành công **{result['success']}** / {result['total']} sản phẩm!")
                                st.session_state.df_key += 1
                                
                                # Hiển thị mã không tìm thấy
                                if result['not_found']:
                                    with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã sản phẩm", expanded=True):
                                        for code in result['not_found']:
                                            st.markdown(f"- `{code}`")
                                    
                                    # Gửi email thông báo
                                    email_sent = send_import_notification(
                                        not_found_codes=result['not_found'],
                                        filename=excel_path,
                                        import_type='TONBON',
                                        ngay_import=ngay_kiem.strftime('%Y-%m-%d'),
                                        nguoi_import=st.session_state.username
                                    )
                                    if email_sent:
                                        st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                            else:
                                if result['not_found']:
                                    st.error(f"❌ Không import được. {len(result['not_found'])} mã không tìm thấy trong database.")
                                    with st.expander("Chi tiết mã lỗi"):
                                        for code in result['not_found']:
                                            st.markdown(f"- `{code}`")
                                    
                                    # Gửi email thông báo
                                    email_sent = send_import_notification(
                                        not_found_codes=result['not_found'],
                                        filename=excel_path,
                                        import_type='TONBON',
                                        ngay_import=ngay_kiem.strftime('%Y-%m-%d'),
                                        nguoi_import=st.session_state.username
                                    )
                                    if email_sent:
                                        st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                else:
                                    st.error(f"❌ Lỗi: {result['errors']}")
                            
        except ImportError as e:
            st.error(f"❌ Lỗi import module: {e}")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
    
    # TAB 1: Danh sách Tồn bồn
    with tab1:
        st.header("📋 Danh sách Tồn bồn")
        
        # Lấy ngày gần nhất có dữ liệu
        import sqlite3
        try:
            conn_check = ss.connect_db()
            cursor = conn_check.cursor()
            cursor.execute("SELECT MAX([Ngày kiểm kho]) FROM TonBon WHERE [Đã xóa] = 0")
            latest = cursor.fetchone()[0]
            conn_check.close()
            
            if latest:
                parts = latest.split('-')
                default_date = datetime(int(parts[0]), int(parts[1]), int(parts[2])).date()
            else:
                default_date = None
        except:
            default_date = None
        
        # Bộ lọc
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_date = st.date_input(
                "Lọc theo ngày",
                value=default_date,
                help="Mặc định là ngày gần nhất có dữ liệu",
                key="filter_date_tonbon"
            )
        with col2:
            filter_loai = st.selectbox(
                "Lọc loại SP",
                options=['Tất cả'] + LOAI_SAN_PHAM,
                help="Lọc theo loại sản phẩm"
            )
        with col3:
            filter_trang_thai = st.selectbox(
                "Lọc trạng thái",
                options=['Tất cả'] + TRANG_THAI_OPTIONS,
                help="Lọc theo trạng thái"
            )
        with col4:
            filter_ca = st.selectbox(
                "Lọc ca",
                options=['Tất cả'] + CA_SAN_XUAT,
                help="Lọc theo ca",
                key="filter_ca_tonbon"
            )
        
        # Build filter conditions
        col_where = {'Đã xóa': ('=', 0)}
        if filter_date:
            col_where['Ngày kiểm kho'] = ('=', filter_date.strftime('%Y-%m-%d'))
            # Mặc định hiển thị All khi lọc theo ngày
            st.session_state.page_size = 'All'
        if filter_loai != 'Tất cả':
            col_where['Loại sản phẩm'] = ('=', filter_loai)
        if filter_trang_thai != 'Tất cả':
            col_where['Trạng thái'] = ('=', filter_trang_thai)
        if filter_ca != 'Tất cả':
            col_where['Ca sản xuất'] = ('=', filter_ca)
        
        # Hàm chuyển đổi format ngày
        def format_dates(df):
            if 'Ngày kiểm kho' in df.columns:
                df['Ngày kiểm kho'] = pd.to_datetime(df['Ngày kiểm kho']).dt.strftime('%d-%m-%Y')
            if 'Thời gian tạo' in df.columns:
                df['Thời gian tạo'] = pd.to_datetime(df['Thời gian tạo']).dt.strftime('%d-%m-%Y %H:%M')
            return df
        
        column_config = {
            'Số lượng (kg)': st.column_config.NumberColumn('Số lượng (kg)', format="%,.0f"),
        }
        
        # Thiết lập page_size = 'All' để hiển thị tất cả
        if 'page_size' not in st.session_state or st.session_state.get('tonbon_first_load', True):
            st.session_state.page_size = 'All'
            st.session_state['tonbon_first_load'] = False
        
        dataframe_with_selections(
            table_name="TonBon",
            columns=[
                'ID', 'Mã tồn bồn', 'Ngày kiểm kho', 'ID sản phẩm',
                'Loại sản phẩm', 'Số lượng (kg)', 'Số bồn',
                'Trạng thái', 'Kích cỡ đóng bao', 'Ca sản xuất',
                'Ghi chú', 'Người tạo', 'Thời gian tạo'
            ],
            colums_disable=['ID', 'Mã tồn bồn', 'Người tạo', 'Thời gian tạo'],
            col_where=col_where,
            col_order={'Ngày kiểm kho': 'DESC', 'ID': 'DESC'},
            joins=[
                {
                    'table': 'SanPham',
                    'on': {'ID sản phẩm': 'ID'},
                    'columns': ['Code cám', 'Tên cám'],
                    'replace_multi': {'ID sản phẩm': ['Code cám', 'Tên cám']}
                }
            ],
            column_config=column_config,
            key=f'TonBon_{st.session_state.df_key}',
            join_user_info=False,
            post_process_func=format_dates
        )
        
        # Thống kê tổng hợp theo số bồn
        st.markdown("---")
        st.subheader("📊 Thống kê Tồn bồn")
        
        try:
            import sqlite3
            conn = ss.connect_db()
            
            # Điều kiện lọc theo ngày
            date_condition = ""
            if filter_date:
                date_condition = f"AND [Ngày kiểm kho] = '{filter_date.strftime('%Y-%m-%d')}'"
            
            # Query thống kê Thành phẩm (bồn 99-134)
            # Số bồn được lưu dạng "X" hoặc "X, Y, Z" (nhiều bồn)
            thanh_pham_query = f"""
                SELECT SUM([Số lượng (kg)]) as tong_kg, COUNT(*) as so_dong
                FROM TonBon
                WHERE [Đã xóa] = 0
                {date_condition}
                AND (
                    CAST(REPLACE(REPLACE([Số bồn], ',', ''), ' ', '') AS INTEGER) BETWEEN 99 AND 134
                    OR [Số bồn] LIKE '%99%' OR [Số bồn] LIKE '%100%' OR [Số bồn] LIKE '%101%'
                    OR [Số bồn] LIKE '%102%' OR [Số bồn] LIKE '%103%' OR [Số bồn] LIKE '%104%'
                    OR [Số bồn] LIKE '%105%' OR [Số bồn] LIKE '%106%' OR [Số bồn] LIKE '%107%'
                    OR [Số bồn] LIKE '%108%' OR [Số bồn] LIKE '%109%' OR [Số bồn] LIKE '%110%'
                    OR [Số bồn] LIKE '%111%' OR [Số bồn] LIKE '%112%' OR [Số bồn] LIKE '%113%'
                    OR [Số bồn] LIKE '%114%' OR [Số bồn] LIKE '%115%' OR [Số bồn] LIKE '%116%'
                    OR [Số bồn] LIKE '%117%' OR [Số bồn] LIKE '%118%' OR [Số bồn] LIKE '%119%'
                    OR [Số bồn] LIKE '%120%' OR [Số bồn] LIKE '%121%' OR [Số bồn] LIKE '%122%'
                    OR [Số bồn] LIKE '%123%' OR [Số bồn] LIKE '%124%' OR [Số bồn] LIKE '%125%'
                    OR [Số bồn] LIKE '%126%' OR [Số bồn] LIKE '%127%' OR [Số bồn] LIKE '%128%'
                    OR [Số bồn] LIKE '%129%' OR [Số bồn] LIKE '%130%' OR [Số bồn] LIKE '%131%'
                    OR [Số bồn] LIKE '%132%' OR [Số bồn] LIKE '%133%' OR [Số bồn] LIKE '%134%'
                )
            """
            
            # Query thống kê Bán thành phẩm (bồn 86-98)
            ban_tp_query = f"""
                SELECT SUM([Số lượng (kg)]) as tong_kg, COUNT(*) as so_dong
                FROM TonBon
                WHERE [Đã xóa] = 0
                {date_condition}
                AND (
                    [Số bồn] LIKE '%86%' OR [Số bồn] LIKE '%87%' OR [Số bồn] LIKE '%88%'
                    OR [Số bồn] LIKE '%89%' OR [Số bồn] LIKE '%90%' OR [Số bồn] LIKE '%91%'
                    OR [Số bồn] LIKE '%92%' OR [Số bồn] LIKE '%93%' OR [Số bồn] LIKE '%94%'
                    OR [Số bồn] LIKE '%95%' OR [Số bồn] LIKE '%96%' OR [Số bồn] LIKE '%97%'
                    OR [Số bồn] LIKE '%98%'
                )
            """
            
            tp_result = pd.read_sql_query(thanh_pham_query, conn)
            btp_result = pd.read_sql_query(ban_tp_query, conn)
            conn.close()
            
            # Hiển thị thống kê
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📦 Thành phẩm (Bồn 99-134)")
                tong_tp = tp_result['tong_kg'].iloc[0] if tp_result['tong_kg'].iloc[0] else 0
                so_dong_tp = tp_result['so_dong'].iloc[0] if tp_result['so_dong'].iloc[0] else 0
                if tong_tp > 0:
                    st.metric("Tổng khối lượng", f"{tong_tp:,.0f} kg", f"{so_dong_tp} dòng")
                else:
                    st.info("Không có dữ liệu")
            
            with col2:
                st.markdown("#### 🔄 Bán thành phẩm (Bồn 86-98)")
                tong_btp = btp_result['tong_kg'].iloc[0] if btp_result['tong_kg'].iloc[0] else 0
                so_dong_btp = btp_result['so_dong'].iloc[0] if btp_result['so_dong'].iloc[0] else 0
                if tong_btp > 0:
                    st.metric("Tổng khối lượng", f"{tong_btp:,.0f} kg", f"{so_dong_btp} dòng")
                else:
                    st.info("Không có dữ liệu")
                    
        except Exception as e:
            st.warning(f"Không thể tải thống kê: {e}")
