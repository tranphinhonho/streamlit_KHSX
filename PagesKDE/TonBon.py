import streamlit as st
from admin.sys_kde_components import *
import pandas as pd
from datetime import datetime

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
        "✍️ Nhập thủ công",
        "📁 Import Excel",
        "📋 Danh sách Tồn bồn"
    ])
    
    # TAB 1: Nhập thủ công
    with tab1:
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
                value=fn.get_vietnam_time().date(),
                help="Ngày kiểm tra tồn bồn"
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
        if st.button("💾 Lưu Tồn bồn", type="primary", use_container_width=True):
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
                    if st.button("🔄 Tìm email báo cáo tồn bồn", use_container_width=True):
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
                # File local
                excel_path = "EXCEL/Báo cáo tồn bồn thành phẩm 01.2026.xlsm"
                st.markdown(f"**📄 File:** `{excel_path}`")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ngay_kiem = st.date_input(
                    "📅 Ngày kiểm kho",
                    value=fn.get_vietnam_time().date(),
                    help="Ngày kiểm tra tồn bồn",
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
                # Nút đọc nhanh (trực tiếp từ Sheet 2)
                if st.button("⚡ Xem trước dữ liệu (Nhanh)", type="primary", use_container_width=True):
                    with st.spinner("📖 Đang đọc dữ liệu từ Sheet 2..."):
                        df_preview = importer.read_direct_from_cells(excel_path)
                        
                        if len(df_preview) > 0:
                            st.success(f"✅ Đọc được {len(df_preview)} mã sản phẩm")
                            
                            # Tính tổng
                            total_kg = df_preview['Số lượng (kg)'].sum()
                            st.metric("Tổng khối lượng", f"{total_kg:,.0f} kg")
                            
                            st.dataframe(
                                df_preview,
                                use_container_width=True,
                                column_config={
                                    'Số lượng (kg)': st.column_config.NumberColumn(format="%,.0f")
                                }
                            )
                            
                            # Lưu vào session để import
                            st.session_state['tonbon_preview'] = df_preview
                        else:
                            st.warning("⚠️ Không tìm thấy dữ liệu. Kiểm tra file Excel có tồn tại và có dữ liệu ở Sheet 2 không?")
            else:
                st.warning("⚠️ Chưa có file. Nhấn 'Tìm email' rồi 'Tải file' để bắt đầu.")
            
            # Nút Import
            st.markdown("---")
            
            if excel_path:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    overwrite = st.checkbox("🔄 Ghi đè dữ liệu cũ (cùng ngày)", value=False)
                
                with col_btn2:
                    pass
                
                if st.button("📥 Import vào Database", type="primary", use_container_width=True):
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
                        else:
                            if result['not_found']:
                                st.error(f"❌ Không import được. {len(result['not_found'])} mã không tìm thấy trong database.")
                                with st.expander("Chi tiết mã lỗi"):
                                    for code in result['not_found']:
                                        st.markdown(f"- `{code}`")
                            else:
                                st.error(f"❌ Lỗi: {result['errors']}")
                            
        except ImportError as e:
            st.error(f"❌ Lỗi import module: {e}")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
    
    # TAB 3: Danh sách Tồn bồn
    with tab3:
        st.header("📋 Danh sách Tồn bồn")
        
        # Bộ lọc
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_date = st.date_input(
                "Lọc theo ngày",
                value=None,
                help="Để trống để xem tất cả",
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
        if filter_loai != 'Tất cả':
            col_where['Loại sản phẩm'] = ('=', filter_loai)
        if filter_trang_thai != 'Tất cả':
            col_where['Trạng thái'] = ('=', filter_trang_thai)
        if filter_ca != 'Tất cả':
            col_where['Ca sản xuất'] = ('=', filter_ca)
        
        column_config = {
            'Ngày kiểm kho': st.column_config.DateColumn('Ngày kiểm', format='DD/MM/YYYY'),
            'Số lượng (kg)': st.column_config.NumberColumn('Số lượng (kg)', format="%,.0f"),
            'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm'),
        }
        
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
            col_order={'ID': 'DESC'},
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
            join_user_info=False  # Không join để ẩn cột Fullname
        )
        
        # Thống kê tổng hợp
        st.markdown("---")
        st.subheader("📊 Thống kê Tồn bồn")
        
        try:
            import sqlite3
            conn = sqlite3.connect('database_new.db')
            
            # Query thống kê theo loại và trạng thái
            stats_query = """
                SELECT 
                    [Loại sản phẩm],
                    [Trạng thái],
                    COUNT(*) as so_bon,
                    SUM([Số lượng (kg)]) as tong_kg
                FROM TonBon
                WHERE [Đã xóa] = 0
                GROUP BY [Loại sản phẩm], [Trạng thái]
                ORDER BY [Loại sản phẩm], tong_kg DESC
            """
            
            stats = pd.read_sql_query(stats_query, conn)
            conn.close()
            
            if len(stats) > 0:
                # Hiển thị theo loại sản phẩm
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📦 Thành phẩm")
                    tp = stats[stats['Loại sản phẩm'] == 'Thành phẩm']
                    if len(tp) > 0:
                        for _, row in tp.iterrows():
                            st.metric(row['Trạng thái'], f"{row['tong_kg']:,.0f} kg", f"{row['so_bon']} bồn")
                    else:
                        st.info("Không có dữ liệu")
                
                with col2:
                    st.markdown("#### 🔄 Bán thành phẩm")
                    btp = stats[stats['Loại sản phẩm'] == 'Bán thành phẩm']
                    if len(btp) > 0:
                        for _, row in btp.iterrows():
                            st.metric(row['Trạng thái'], f"{row['tong_kg']:,.0f} kg", f"{row['so_bon']} bồn")
                    else:
                        st.info("Không có dữ liệu")
            else:
                st.info("Chưa có dữ liệu thống kê")
                
        except Exception as e:
            st.warning(f"Không thể tải thống kê: {e}")
