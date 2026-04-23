import streamlit as st
from admin.sys_kde_components import *
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

def app(selected):
    
    # Công suất mặc định (fallback khi không có dữ liệu T/h)
    DEFAULT_MACHINES = {
        'PL1': 10,  # tấn/giờ
        'PL2': 10,
        'PL3': 9,
        'PL4': 9,
        'PL5': 8,
        'PL6': 8,
        'PL7': 8
    }
    
    # Mapping tên hiển thị
    MACHINE_DISPLAY = {
        'PL1': 'Pellet 1',
        'PL2': 'Pellet 2',
        'PL3': 'Pellet 3',
        'PL4': 'Pellet 4',
        'PL5': 'Pellet 5',
        'PL6': 'Pellet 6',
        'PL7': 'Pellet 7'
    }
    
    MAX_HOURS = 24  # Giới hạn 24 giờ/ngày
    
    # Tạo tabs - thêm Tab Import T/h và Kế hoạch SX
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Import T/h",
        "🤖 Phân bổ tự động", 
        "✍️ Nhập thủ công",
        "📋 Danh sách Pellet",
        "📊 Kế hoạch SX"
    ])
    
    # TAB 1: Import T/h
    with tab1:
        st.header("📥 Import dữ liệu T/h từ vận hành cám viên")
        
        st.markdown("""
        **Thu thập dữ liệu T/h và Kwh/T từ file vận hành cám viên (PL1-PL7)**
        - Dữ liệu được thu thập theo ngày
        - Chọn ngày có T/h cao nhất làm thông số mặc định cho mỗi cặp (cám, máy)
        - Hỗ trợ import từ email hoặc file thủ công
        """)
        
        # Sub-tabs cho email và manual import
        import_tab1, import_tab2, import_tab_quality, import_tab3 = st.tabs([
            "📧 Từ Email (Ưu tiên)",
            "📁 Từ File",
            "📈 Theo dõi chất lượng",
            "📊 Dữ liệu hiện có"
        ])
        
        with import_tab1:
            st.subheader("📧 Import từ Email")
            
            try:
                from utils.platform_utils import is_windows
                
                if is_windows():
                    from utils.email_receiver import EmailReceiver
                    
                    if st.button("🔗 Kết nối Outlook & Quét email", type="primary"):
                        with st.spinner("Đang kết nối và quét email..."):
                            try:
                                receiver = EmailReceiver()
                                if receiver.connect():
                                    emails = receiver.get_pellet_emails(days_back=30)
                                    st.session_state['pellet_emails'] = emails
                                    st.success(f"✅ Tìm thấy {len(emails)} email có file vận hành cám viên")
                                else:
                                    st.error("❌ Không thể kết nối Outlook")
                            except Exception as e:
                                st.error(f"❌ Lỗi: {e}")
                    
                    # Hiển thị danh sách email
                    if 'pellet_emails' in st.session_state:
                        emails = st.session_state['pellet_emails']
                        
                        if emails:
                            st.markdown("### 📧 Email tìm thấy")
                            
                            for idx, email in enumerate(emails):
                                with st.expander(f"📧 {email['sender']} - {email['received_time'][:10]}", expanded=False):
                                    st.write(f"**Subject:** {email['subject']}")
                                    st.write(f"**Thời gian:** {email['received_time']}")
                                    
                                    for file_info in email.get('pellet_files', []):
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.write(f"📄 {file_info['filename']}")
                                        with col2:
                                            if st.button("⬇️ Download & Import", key=f"import_email_{idx}_{file_info['index']}"):
                                                with st.spinner("Đang download và import..."):
                                                    try:
                                                        receiver = EmailReceiver()
                                                        receiver.connect()
                                                        
                                                        file_path = receiver.download_attachment(
                                                            email, file_info, subfolder="pellet"
                                                        )
                                                        
                                                        if file_path:
                                                            from utils.pellet_capacity_importer import PelletCapacityImporter
                                                            importer = PelletCapacityImporter()
                                                            result = importer.import_file(
                                                                file_path, 
                                                                nguoi_import=st.session_state.get('username', 'system')
                                                            )
                                                            
                                                            if result['success']:
                                                                st.success(f"✅ Import thành công {result['imported']} records!")
                                                                st.balloons()
                                                            else:
                                                                st.error(f"❌ Lỗi: {result.get('error', 'Unknown')}")
                                                        else:
                                                            st.error("❌ Không thể download file")
                                                    except Exception as e:
                                                        st.error(f"❌ Lỗi: {e}")
                        else:
                            st.info("📭 Không tìm thấy email nào có file vận hành cám viên")
                else:
                    st.warning("⚠️ Tính năng email chỉ hỗ trợ trên Windows với Outlook")
                    
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
        
        with import_tab2:
            st.subheader("📁 Import từ File")
            
            try:
                from utils.pellet_capacity_importer import PelletCapacityImporter
                
                # Cho phép chọn folder import
                import os
                default_folder = "EXCEL"
                
                # Input để chọn folder khác
                col_folder, col_browse = st.columns([4, 1])
                with col_folder:
                    excel_folder = st.text_input(
                        "📂 Folder chứa file PL*.xlsx",
                        value=default_folder,
                        help="Nhập đường dẫn folder chứa file vận hành cám viên (VD: EXCEL hoặc D:\\Data\\Pellet)",
                        key="pellet_import_folder"
                    )
                with col_browse:
                    st.caption("Đường dẫn folder")
                    if st.button("🔄 Làm mới", key="refresh_folder_btn"):
                        st.rerun()
                
                if os.path.exists(excel_folder):
                    pellet_files = [f for f in os.listdir(excel_folder) 
                                   if f.startswith('PL') and f.endswith(('.xlsx', '.xlsm'))]
                    
                    if pellet_files:
                        st.info(f"📂 Tìm thấy {len(pellet_files)} file trong folder EXCEL/")
                        
                        # Button Import tất cả
                        col_all, col_single = st.columns([1, 2])
                        
                        with col_all:
                            if st.button("🚀 Import TẤT CẢ", type="primary", help="Import cùng lúc tất cả file PL"):
                                importer = PelletCapacityImporter()
                                
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                total_imported = 0
                                total_deleted = 0
                                success_count = 0
                                errors = []
                                
                                for idx, file_name in enumerate(pellet_files):
                                    file_path = os.path.join(excel_folder, file_name)
                                    status_text.text(f"📥 Đang import {file_name}... ({idx+1}/{len(pellet_files)})")
                                    
                                    try:
                                        result = importer.import_file(
                                            file_path,
                                            nguoi_import=st.session_state.get('username', 'system'),
                                            overwrite=True
                                        )
                                        
                                        if result.get('success'):
                                            total_imported += result.get('imported', 0)
                                            total_deleted += result.get('deleted', 0)
                                            success_count += 1
                                        else:
                                            errors.append(f"{file_name}: {result.get('error')}")
                                    except Exception as e:
                                        errors.append(f"{file_name}: {str(e)}")
                                    
                                    progress_bar.progress((idx + 1) / len(pellet_files))
                                
                                status_text.empty()
                                progress_bar.empty()
                                
                                st.success(f"""
                                ✅ **Import hoàn tất!**
                                - File thành công: **{success_count}/{len(pellet_files)}**
                                - Tổng records: **{total_imported}**
                                - Đã xóa cũ: **{total_deleted}**
                                """)
                                st.balloons()
                                
                                if errors:
                                    with st.expander(f"⚠️ {len(errors)} lỗi"):
                                        for err in errors:
                                            st.error(err)
                        
                        with col_single:
                            st.caption("Hoặc chọn file đơn lẻ:")
                        
                        # Import từng file
                        selected_file = st.selectbox(
                            "Chọn file để import",
                            options=pellet_files,
                            format_func=lambda x: x
                        )
                        
                        if selected_file:
                            file_path = os.path.join(excel_folder, selected_file)
                            
                            if st.button("🚀 Import file", type="secondary"):
                                with st.spinner(f"Đang import {selected_file}..."):
                                    importer = PelletCapacityImporter()
                                    result = importer.import_file(
                                        file_path,
                                        nguoi_import=st.session_state.get('username', 'system')
                                    )
                                    
                                    if result['success']:
                                        st.success(f"""
                                        ✅ Import thành công!
                                        - Máy: **{result['machine']}**
                                        - Tháng/Năm: **{result['month']}/{result['year']}**
                                        - Records: **{result['imported']}**
                                        - Đã xóa cũ: **{result.get('deleted', 0)}**
                                        """)
                                        st.balloons()
                                        
                                        if result.get('not_found'):
                                            with st.expander(f"⚠️ {len(result['not_found'])} mã cám không tìm thấy"):
                                                for code in result['not_found'][:20]:
                                                    st.text(f"- {code}")
                                    else:
                                        st.error(f"❌ Lỗi: {result.get('error', 'Unknown')}")
                    else:
                        st.warning("Không tìm thấy file PL*.xlsx trong folder EXCEL/")
                
                # Hoặc upload file
                st.markdown("---")
                st.markdown("**Hoặc upload file từ máy:**")
                
                uploaded = st.file_uploader(
                    "Chọn file vận hành cám viên",
                    type=['xlsx', 'xlsm'],
                    key="pellet_upload"
                )
                
                if uploaded:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as f:
                        f.write(uploaded.read())
                        temp_path = f.name
                    
                    if st.button("🚀 Import uploaded file", type="primary"):
                        with st.spinner("Đang import..."):
                            importer = PelletCapacityImporter()
                            result = importer.import_file(
                                temp_path,
                                nguoi_import=st.session_state.get('username', 'system')
                            )
                            
                            if result['success']:
                                st.success(f"✅ Import thành công {result['imported']} records!")
                            else:
                                st.error(f"❌ Lỗi: {result.get('error', 'Unknown')}")
                                
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())
        
        with import_tab_quality:
            st.subheader("📈 Theo dõi chất lượng cám viên")
            st.caption("Theo dõi khuôn ép viên, công suất (T/h) và năng lượng (Kwh/T) theo từng máy PL1-PL7")
            
            try:
                import sqlite3 as sqlite3_local
                from utils.pellet_capacity_importer import PelletCapacityImporter
                importer = PelletCapacityImporter()
                
                # Lấy dữ liệu từ database
                conn = ss.connect_db()
                
                # Thống kê theo máy
                query_by_machine = """
                SELECT 
                    [Số máy],
                    COUNT(DISTINCT [Code cám]) as [Số loại cám],
                    AVG([T/h]) as [T/h TB],
                    MAX([T/h]) as [T/h Max],
                    MIN([T/h]) as [T/h Min],
                    AVG([Kwh/T]) as [Kwh/T TB],
                    MAX([Kwh/T]) as [Kwh/T Max],
                    MIN([Kwh/T]) as [Kwh/T Min],
                    SUM([Số lô]) as [Tổng lô SX],
                    MAX([Ngày]) as [Ngày cập nhật]
                FROM PelletCapacity
                WHERE [Đã xóa] = 0
                GROUP BY [Số máy]
                ORDER BY [Số máy]
                """
                df_machines = pd.read_sql_query(query_by_machine, conn)
                
                if len(df_machines) > 0:
                    # Hiển thị metrics tổng quan
                    st.markdown("### 🏭 Tổng quan 7 máy Pellet")
                    
                    cols = st.columns(4)
                    with cols[0]:
                        st.metric("Tổng máy hoạt động", f"{len(df_machines)}/7")
                    with cols[1]:
                        avg_th = df_machines['T/h TB'].mean()
                        st.metric("T/h trung bình", f"{avg_th:.2f}" if pd.notna(avg_th) else "-")
                    with cols[2]:
                        avg_kwh = df_machines['Kwh/T TB'].mean()
                        st.metric("Kwh/T trung bình", f"{avg_kwh:.2f}" if pd.notna(avg_kwh) else "-")
                    with cols[3]:
                        total_lots = df_machines['Tổng lô SX'].sum()
                        st.metric("Tổng lô sản xuất", f"{int(total_lots):,}" if pd.notna(total_lots) else "-")
                    
                    st.markdown("---")
                    
                    # Bảng thống kê theo máy
                    st.markdown("### 🔧 Thống kê theo từng máy")
                    
                    st.dataframe(
                        df_machines,
                        column_config={
                            'Số máy': st.column_config.TextColumn('Máy', width='small'),
                            'Số loại cám': st.column_config.NumberColumn('Số loại cám', format="%d"),
                            'T/h TB': st.column_config.NumberColumn('T/h TB', format="%.2f", help="Công suất trung bình (tấn/giờ)"),
                            'T/h Max': st.column_config.NumberColumn('T/h Max', format="%.2f"),
                            'T/h Min': st.column_config.NumberColumn('T/h Min', format="%.2f"),
                            'Kwh/T TB': st.column_config.NumberColumn('Kwh/T TB', format="%.2f", help="Năng lượng trung bình"),
                            'Kwh/T Max': st.column_config.NumberColumn('Kwh/T Max', format="%.2f"),
                            'Kwh/T Min': st.column_config.NumberColumn('Kwh/T Min', format="%.2f"),
                            'Tổng lô SX': st.column_config.NumberColumn('Tổng lô SX', format="%d"),
                            'Ngày cập nhật': st.column_config.TextColumn('Cập nhật cuối', width='medium')
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.markdown("---")
                    
                    # Theo dõi khuôn ép viên theo máy
                    st.markdown("### 🔩 Theo dõi khuôn ép viên")
                    st.info("💡 Khuôn ép viên cần được thay thế khi T/h giảm hoặc Kwh/T tăng bất thường")
                    
                    # Chế độ xem: Theo máy hoặc Theo ngày
                    view_mode = st.radio(
                        "Chế độ xem",
                        options=["📊 Theo máy", "📅 Theo ngày (tất cả 7 máy)"],
                        horizontal=True,
                        key="quality_view_mode"
                    )
                    
                    if view_mode == "📊 Theo máy":
                        # Chọn máy để xem chi tiết
                        selected_machine = st.selectbox(
                            "Chọn máy để xem chi tiết",
                            options=df_machines['Số máy'].tolist(),
                            key="quality_machine_select"
                        )
                        
                        if selected_machine:
                            # Lấy dữ liệu chi tiết theo máy
                            query_detail = """
                            SELECT 
                                pc.[Số máy],
                                pc.[Code cám],
                                pc.[T/h],
                                pc.[Kwh/T],
                                pc.[Số lô],
                                pc.[Ngày],
                                sp.[Tên cám],
                                sp.[Vật nuôi],
                                sp.[Kích cỡ ép viên],
                                pc.[Thông số khuôn]
                            FROM PelletCapacity pc
                            LEFT JOIN SanPham sp ON (pc.[Code cám] = sp.[Code cám] OR pc.[Code cám] = sp.[Tên cám])
                            WHERE pc.[Số máy] = ? AND pc.[Đã xóa] = 0
                            ORDER BY pc.[T/h] DESC
                            """
                            df_detail = pd.read_sql_query(query_detail, conn, params=(selected_machine,))
                    else:
                        # Lấy danh sách ngày có dữ liệu
                        query_dates = "SELECT DISTINCT [Ngày] FROM PelletCapacity WHERE [Đã xóa] = 0 ORDER BY [Ngày] DESC"
                        df_dates = pd.read_sql_query(query_dates, conn)
                        
                        if len(df_dates) > 0:
                            date_list = df_dates['Ngày'].tolist()
                            
                            # Tính ngày N-1 (hôm qua)
                            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                            
                            # Tìm index mặc định theo quy tắc N-1
                            default_index = 0
                            if yesterday in date_list:
                                default_index = date_list.index(yesterday)
                            elif len(date_list) > 1:
                                # Nếu không có ngày hôm qua, lấy ngày gần nhất thứ 2
                                default_index = 1
                            
                            selected_date = st.selectbox(
                                "Chọn ngày để xem chi tiết tất cả 7 máy (mặc định N-1)",
                                options=date_list,
                                index=default_index,
                                key="quality_date_select"
                            )
                            
                            if selected_date:
                                # Lấy dữ liệu chi tiết tất cả máy theo ngày
                                query_detail = """
                                SELECT 
                                    pc.[Số máy],
                                    pc.[Code cám],
                                    pc.[T/h],
                                    pc.[Kwh/T],
                                    pc.[Số lô],
                                    pc.[Ngày],
                                    sp.[Tên cám],
                                    sp.[Vật nuôi],
                                    sp.[Kích cỡ ép viên],
                                    pc.[Thông số khuôn]
                                FROM PelletCapacity pc
                                LEFT JOIN SanPham sp ON (pc.[Code cám] = sp.[Code cám] OR pc.[Code cám] = sp.[Tên cám])
                                WHERE pc.[Ngày] = ? AND pc.[Đã xóa] = 0
                                ORDER BY pc.[Số máy], pc.[T/h] DESC
                                """
                                df_detail = pd.read_sql_query(query_detail, conn, params=(selected_date,))
                                selected_machine = f"Tất cả máy ngày {selected_date}"
                        else:
                            df_detail = pd.DataFrame()
                            selected_machine = None
                        
                        if len(df_detail) > 0:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                max_th = df_detail['T/h'].max()
                                min_th = df_detail['T/h'].min()
                                diff_th = max_th - min_th if pd.notna(max_th) and pd.notna(min_th) else 0
                                st.metric(
                                    f"Công suất {selected_machine}", 
                                    f"{df_detail['T/h'].mean():.2f} T/h",
                                    delta=f"Biên độ: {diff_th:.2f}",
                                    delta_color="off"
                                )
                            
                            with col2:
                                avg_kwh = df_detail['Kwh/T'].mean()
                                st.metric(
                                    "Năng lượng TB", 
                                    f"{avg_kwh:.2f} Kwh/T" if pd.notna(avg_kwh) else "-"
                                )
                            
                            with col3:
                                total_feeds = len(df_detail[['Code cám']].drop_duplicates())
                                st.metric("Số loại cám", f"{total_feeds}")
                            
                            # Phân loại theo hiệu suất
                            st.markdown(f"#### 📊 Chi tiết theo sản phẩm - {selected_machine}")
                            
                            # Thêm cột đánh giá hiệu suất
                            mean_th = df_detail['T/h'].mean()
                            mean_kwh = df_detail['Kwh/T'].mean()
                            
                            def evaluate_quality(row):
                                score = 0
                                if pd.notna(row['T/h']) and pd.notna(mean_th):
                                    if row['T/h'] >= mean_th: score += 1
                                if pd.notna(row['Kwh/T']) and pd.notna(mean_kwh):
                                    if row['Kwh/T'] <= mean_kwh: score += 1
                                if score == 2: return "🟢 Tốt"
                                elif score == 1: return "🟡 TB"
                                else: return "🔴 Cần cải thiện"
                            
                            df_detail['Đánh giá'] = df_detail.apply(evaluate_quality, axis=1)
                            
                            # Xác định column_order dựa trên chế độ xem
                            if view_mode == "📅 Theo ngày (tất cả 7 máy)":
                                col_order = ['Số máy', 'Code cám', 'T/h', 'Kwh/T', 'Số lô', 'Tên cám', 'Vật nuôi', 'Kích cỡ ép viên', 'Thông số khuôn', 'Đánh giá']
                            else:
                                col_order = ['Code cám', 'T/h', 'Kwh/T', 'Số lô', 'Ngày', 'Tên cám', 'Vật nuôi', 'Kích cỡ ép viên', 'Thông số khuôn', 'Đánh giá']
                            
                            st.dataframe(
                                df_detail,
                                column_config={
                                    'Số máy': st.column_config.TextColumn('Máy', width='small'),
                                    'Code cám': st.column_config.TextColumn('Mã cám', width='small'),
                                    'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                    'T/h': st.column_config.NumberColumn('T/h', format="%.2f"),
                                    'Kwh/T': st.column_config.NumberColumn('Kwh/T', format="%.2f"),
                                    'Số lô': st.column_config.NumberColumn('Số lô', format="%d"),
                                    'Ngày': st.column_config.TextColumn('Ngày SX', width='small'),
                                    'Vật nuôi': st.column_config.TextColumn('Vật nuôi', width='small'),
                                    'Kích cỡ ép viên': st.column_config.TextColumn('Kích cỡ', width='small'),
                                    'Thông số khuôn': st.column_config.TextColumn('Thông số khuôn', width='medium'),
                                    'Đánh giá': st.column_config.TextColumn('Đánh giá', width='medium')
                                },
                                column_order=col_order,
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Cảnh báo về khuôn
                            st.markdown("#### ⚠️ Cảnh báo khuôn ép viên")
                            
                            # Sản phẩm có T/h thấp bất thường (< 70% trung bình)
                            low_th_threshold = mean_th * 0.7 if pd.notna(mean_th) else 0
                            df_low_th = df_detail[df_detail['T/h'] < low_th_threshold] if low_th_threshold > 0 else pd.DataFrame()
                            
                            # Sản phẩm có Kwh/T cao bất thường (> 130% trung bình)
                            high_kwh_threshold = mean_kwh * 1.3 if pd.notna(mean_kwh) else 999
                            df_high_kwh = df_detail[df_detail['Kwh/T'] > high_kwh_threshold] if pd.notna(mean_kwh) else pd.DataFrame()
                            
                            if len(df_low_th) > 0:
                                st.warning(f"📉 {len(df_low_th)} sản phẩm có T/h thấp bất thường (< {low_th_threshold:.2f} T/h)")
                                with st.expander("Xem chi tiết sản phẩm T/h thấp"):
                                    st.dataframe(
                                        df_low_th[['Code cám', 'Tên cám', 'T/h', 'Kwh/T', 'Thông số khuôn', 'Ngày']],
                                        column_config={
                                            'Kwh/T': st.column_config.NumberColumn('Kwh/T', format="%.2f")
                                        },
                                        hide_index=True
                                    )
                            
                            if len(df_high_kwh) > 0:
                                st.warning(f"⚡ {len(df_high_kwh)} sản phẩm có Kwh/T cao bất thường (> {high_kwh_threshold:.2f} Kwh/T)")
                                with st.expander("Xem chi tiết sản phẩm Kwh/T cao"):
                                    st.dataframe(
                                        df_high_kwh[['Code cám', 'Tên cám', 'T/h', 'Kwh/T', 'Thông số khuôn', 'Ngày']],
                                        column_config={
                                            'Kwh/T': st.column_config.NumberColumn('Kwh/T', format="%.2f")
                                        },
                                        hide_index=True
                                    )
                            
                            if len(df_low_th) == 0 and len(df_high_kwh) == 0:
                                st.success(f"✅ Không có cảnh báo bất thường cho máy {selected_machine}")
                        else:
                            st.info(f"📭 Chưa có dữ liệu chi tiết cho máy {selected_machine}")
                else:
                    st.info("📭 Chưa có dữ liệu. Hãy import file vận hành cám viên từ tab 'Từ Email' hoặc 'Từ File'.")
                
                conn.close()
                
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())
        
        with import_tab3:
            st.subheader("📊 Dữ liệu T/h hiện có")
            
            try:
                from utils.pellet_capacity_importer import PelletCapacityImporter
                importer = PelletCapacityImporter()
                
                # Hiển thị T/h tối ưu theo máy + cám
                st.markdown("### 🏆 T/h tối ưu theo máy & cám")
                st.caption("(Lấy ngày có tổng T/h cao nhất cho mỗi cặp máy-cám)")
                
                df_optimal = importer.get_all_optimal_by_machine()
                
                if len(df_optimal) > 0:
                    # Đổi tên cột Code cám thành Tên cám
                    df_display = df_optimal.rename(columns={'Code cám': 'Tên cám'})
                    
                    st.dataframe(
                        df_display,
                        column_config={
                            'Số máy': st.column_config.TextColumn('Số máy', width='small'),
                            'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                            'T/h': st.column_config.NumberColumn('T/h (tấn/giờ)', format="%.2f"),
                            'Kwh/T': st.column_config.NumberColumn('Kwh/T', format="%.2f"),
                            'Ngày tối ưu': st.column_config.TextColumn('Ngày tối ưu', width='medium'),
                            'Số lô': st.column_config.NumberColumn(
                                'Số lô', 
                                format="%d",
                                help="Số lần sản xuất loại cám này trên máy trong ngày tối ưu"
                            ),
                            'Vật nuôi': st.column_config.TextColumn('Vật nuôi', width='medium')
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.caption(f"Tổng: {len(df_optimal)} cặp (máy, cám)")
                    
                    st.markdown("---")
                    
                    # ==========================================
                    # MỤC MỚI: DỮ LIỆU TRUNG BÌNH T/h VỚI CẢNH BÁO BẤT THƯỜNG
                    # ==========================================
                    st.markdown("### 📊 Dữ liệu trung bình T/h theo sản phẩm")
                    st.caption("Tính trung bình T/h cho từng sản phẩm, phát hiện và loại bỏ giá trị bất thường")
                    
                    try:
                        import sqlite3 as sqlite3_avg
                        import numpy as np
                        
                        conn_avg = ss.connect_db()
                        
                        # Lấy tất cả dữ liệu T/h theo sản phẩm (group by Code cám, lấy tất cả records)
                        query_all_th = """
                        SELECT 
                            pc.[Code cám],
                            pc.[T/h],
                            pc.[Kwh/T],
                            pc.[Số máy],
                            pc.[Ngày],
                            pc.[Số lô],
                            pc.ID as RecordID,
                            sp.[Tên cám],
                            sp.[Vật nuôi]
                        FROM PelletCapacity pc
                        LEFT JOIN SanPham sp ON (pc.[Code cám] = sp.[Code cám] OR pc.[Code cám] = sp.[Tên cám])
                        WHERE pc.[Đã xóa] = 0 AND pc.[T/h] > 0
                        ORDER BY pc.[Code cám], pc.[Ngày] DESC
                        """
                        df_all_th = pd.read_sql_query(query_all_th, conn_avg)
                        
                        if len(df_all_th) > 0:
                            # Tính trung bình, std, và ngưỡng IQR cho từng sản phẩm
                            # Sử dụng phương pháp IQR (Interquartile Range) để phát hiện outliers
                            
                            def detect_outliers(group):
                                th_values = group['T/h']
                                if len(th_values) < 3:
                                    # Không đủ dữ liệu để phát hiện outlier
                                    group['Loại'] = 'Bình thường'
                                    return group
                                
                                q1 = th_values.quantile(0.25)
                                q3 = th_values.quantile(0.75)
                                iqr = q3 - q1
                                
                                # Ngưỡng: Q1 - 1.5*IQR và Q3 + 1.5*IQR
                                lower_bound = q1 - 1.5 * iqr
                                upper_bound = q3 + 1.5 * iqr
                                
                                def classify(val):
                                    if val < lower_bound:
                                        return '🔻 Thấp bất thường'
                                    elif val > upper_bound:
                                        return '🔺 Cao bất thường'
                                    else:
                                        return '✅ Bình thường'
                                
                                group['Loại'] = th_values.apply(classify)
                                group['Ngưỡng thấp'] = lower_bound
                                group['Ngưỡng cao'] = upper_bound
                                return group
                            
                            # Áp dụng phát hiện outlier cho từng sản phẩm
                            df_with_outliers = df_all_th.groupby('Code cám', group_keys=False).apply(detect_outliers)
                            
                            # Đếm số outlier
                            outliers_low = len(df_with_outliers[df_with_outliers['Loại'] == '🔻 Thấp bất thường'])
                            outliers_high = len(df_with_outliers[df_with_outliers['Loại'] == '🔺 Cao bất thường'])
                            total_records = len(df_with_outliers)
                            normal_records = total_records - outliers_low - outliers_high
                            
                            # Hiển thị metrics
                            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                            with col_m1:
                                st.metric("Tổng records", f"{total_records:,}")
                            with col_m2:
                                st.metric("✅ Bình thường", f"{normal_records:,}")
                            with col_m3:
                                st.metric("🔻 Thấp bất thường", f"{outliers_low:,}", delta=f"-{outliers_low}" if outliers_low > 0 else None, delta_color="inverse")
                            with col_m4:
                                st.metric("🔺 Cao bất thường", f"{outliers_high:,}", delta=f"+{outliers_high}" if outliers_high > 0 else None, delta_color="inverse")
                            
                            st.markdown("---")
                            
                            # Filter options
                            filter_col1, filter_col2 = st.columns(2)
                            with filter_col1:
                                show_filter = st.selectbox(
                                    "Lọc theo loại",
                                    options=["Tất cả", "🔻 Thấp bất thường", "🔺 Cao bất thường", "⚠️ Tất cả bất thường", "✅ Chỉ bình thường"],
                                    key="filter_outlier_type"
                                )
                            
                            with filter_col2:
                                # Lấy danh sách sản phẩm unique
                                product_list = ["Tất cả"] + sorted(df_with_outliers['Code cám'].unique().tolist())
                                selected_product = st.selectbox(
                                    "Lọc theo sản phẩm",
                                    options=product_list,
                                    key="filter_product_avg"
                                )
                            
                            # Áp dụng filter
                            df_filtered = df_with_outliers.copy()
                            
                            if show_filter == "🔻 Thấp bất thường":
                                df_filtered = df_filtered[df_filtered['Loại'] == '🔻 Thấp bất thường']
                            elif show_filter == "🔺 Cao bất thường":
                                df_filtered = df_filtered[df_filtered['Loại'] == '🔺 Cao bất thường']
                            elif show_filter == "⚠️ Tất cả bất thường":
                                df_filtered = df_filtered[df_filtered['Loại'].isin(['🔻 Thấp bất thường', '🔺 Cao bất thường'])]
                            elif show_filter == "✅ Chỉ bình thường":
                                df_filtered = df_filtered[df_filtered['Loại'] == '✅ Bình thường']
                            
                            if selected_product != "Tất cả":
                                df_filtered = df_filtered[df_filtered['Code cám'] == selected_product]
                            
                            # Hiển thị bảng với checkbox để loại bỏ
                            if len(df_filtered) > 0:
                                st.markdown(f"#### 📋 Chi tiết dữ liệu ({len(df_filtered)} records)")
                                
                                # Initialize session state for excluded records
                                if 'excluded_records' not in st.session_state:
                                    st.session_state['excluded_records'] = set()
                                
                                # Add checkbox column for exclusion
                                df_display_avg = df_filtered[['Code cám', 'Tên cám', 'T/h', 'Kwh/T', 'Số máy', 'Ngày', 'Số lô', 'Loại', 'RecordID']].copy()
                                
                                st.dataframe(
                                    df_display_avg,
                                    column_config={
                                        'Code cám': st.column_config.TextColumn('Mã cám', width='small'),
                                        'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                        'T/h': st.column_config.NumberColumn('T/h', format="%.2f"),
                                        'Kwh/T': st.column_config.NumberColumn('Kwh/T', format="%.2f"),
                                        'Số máy': st.column_config.TextColumn('Máy', width='small'),
                                        'Ngày': st.column_config.TextColumn('Ngày', width='small'),
                                        'Số lô': st.column_config.NumberColumn('Số lô', format="%d"),
                                        'Loại': st.column_config.TextColumn('Trạng thái', width='medium'),
                                        'RecordID': st.column_config.NumberColumn('ID', width='small')
                                    },
                                    hide_index=True,
                                    use_container_width=True
                                )
                                
                                # Tính T/h trung bình SAU KHI loại bỏ outliers
                                st.markdown("---")
                                st.markdown("#### 📈 Trung bình T/h theo sản phẩm (sau khi loại bỏ bất thường)")
                                
                                # Chỉ tính trung bình từ dữ liệu bình thường
                                df_normal_only = df_with_outliers[df_with_outliers['Loại'] == '✅ Bình thường']
                                
                                if len(df_normal_only) > 0:
                                    # Tính trung bình theo sản phẩm
                                    df_avg_by_product = df_normal_only.groupby('Code cám').agg({
                                        'T/h': ['mean', 'std', 'count', 'min', 'max'],
                                        'Kwh/T': 'mean',
                                        'Tên cám': 'first',
                                        'Vật nuôi': 'first'
                                    }).reset_index()
                                    
                                    # Flatten column names
                                    df_avg_by_product.columns = ['Code cám', 'T/h TB', 'T/h Std', 'Số lượt', 'T/h Min', 'T/h Max', 'Kwh/T TB', 'Tên cám', 'Vật nuôi']
                                    
                                    # Sắp xếp theo T/h TB giảm dần
                                    df_avg_by_product = df_avg_by_product.sort_values('T/h TB', ascending=False)
                                    
                                    st.dataframe(
                                        df_avg_by_product,
                                        column_config={
                                            'Code cám': st.column_config.TextColumn('Mã cám', width='small'),
                                            'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                            'T/h TB': st.column_config.NumberColumn('T/h TB', format="%.2f", help="Trung bình T/h (đã loại outliers)"),
                                            'T/h Std': st.column_config.NumberColumn('Độ lệch chuẩn', format="%.2f"),
                                            'Số lượt': st.column_config.NumberColumn('Số lượt', format="%d", help="Số lượt sản xuất được tính"),
                                            'T/h Min': st.column_config.NumberColumn('T/h Min', format="%.2f"),
                                            'T/h Max': st.column_config.NumberColumn('T/h Max', format="%.2f"),
                                            'Kwh/T TB': st.column_config.NumberColumn('Kwh/T TB', format="%.2f"),
                                            'Vật nuôi': st.column_config.TextColumn('Vật nuôi', width='small')
                                        },
                                        hide_index=True,
                                        use_container_width=True
                                    )
                                    
                                    st.info(f"📊 Đã tính trung bình từ **{len(df_normal_only):,}** records bình thường (loại bỏ **{outliers_low + outliers_high:,}** outliers)")
                                else:
                                    st.warning("⚠️ Không có dữ liệu bình thường để tính trung bình")
                            else:
                                st.info("📭 Không có dữ liệu phù hợp với filter đã chọn")
                        else:
                            st.info("📭 Chưa có dữ liệu T/h. Hãy import file vận hành cám viên.")
                        
                        conn_avg.close()
                        
                    except Exception as e_avg:
                        st.error(f"❌ Lỗi khi tính trung bình T/h: {e_avg}")
                        import traceback
                        with st.expander("Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                    
                    st.markdown("---")
                    
                    # Các nút cập nhật
                    st.markdown("### 🔧 Công cụ cập nhật")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🐷 Cập nhật Vật nuôi", type="secondary", help="Cập nhật Vật nuôi từ file CSV"):
                            with st.spinner("Đang cập nhật Vật nuôi..."):
                                try:
                                    import os
                                    csv_path = 'EXCEL/12334.csv'
                                    if os.path.exists(csv_path):
                                        import pandas as pd_csv
                                        df_csv = pd_csv.read_csv(csv_path)
                                        df_unique = df_csv[['Tên cám', 'Vật nuôi']].drop_duplicates()
                                        
                                        import sqlite3
                                        conn = ss.connect_db()
                                        cursor = conn.cursor()
                                        updated = 0
                                        
                                        for _, row in df_unique.iterrows():
                                            cursor.execute("""
                                                UPDATE SanPham
                                                SET [Vật nuôi] = ?
                                                WHERE ([Code cám] = ? OR [Tên cám] = ?) AND [Đã xóa] = 0
                                            """, (row['Vật nuôi'], row['Tên cám'], row['Tên cám']))
                                            updated += cursor.rowcount
                                        
                                        conn.commit()
                                        conn.close()
                                        st.success(f"✅ Đã cập nhật {updated} sản phẩm")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Không tìm thấy file {csv_path}")
                                except Exception as e:
                                    st.error(f"❌ Lỗi: {e}")
                    
                    with col2:
                        if st.button("⚡ Cập nhật T/h", type="secondary", help="Cập nhật T/h tối ưu vào SanPham"):
                            with st.spinner("Đang cập nhật T/h..."):
                                result = importer.update_sanpham_optimal_th()
                                st.success(f"✅ Đã cập nhật T/h cho {result['updated']}/{result['total']} sản phẩm")
                    
                    with col3:
                        if st.button("🔋 Cập nhật Kwh/T", type="secondary", help="Cập nhật Kwh/T vào SanPham"):
                            with st.spinner("Đang cập nhật Kwh/T..."):
                                try:
                                    import sqlite3
                                    conn = ss.connect_db()
                                    cursor = conn.cursor()
                                    
                                    # Cập nhật Kwh/T từ dữ liệu tối ưu
                                    cursor.execute("""
                                        UPDATE SanPham
                                        SET [Kwh/T] = (
                                            SELECT AVG(pc.[Kwh/T])
                                            FROM PelletCapacity pc
                                            WHERE (pc.[Code cám] = SanPham.[Code cám] OR pc.[Code cám] = SanPham.[Tên cám])
                                            AND pc.[Đã xóa] = 0
                                            AND pc.[Kwh/T] > 0
                                        )
                                        WHERE [Đã xóa] = 0
                                    """)
                                    updated = cursor.rowcount
                                    conn.commit()
                                    conn.close()
                                    st.success(f"✅ Đã cập nhật Kwh/T cho {updated} sản phẩm")
                                except Exception as e:
                                    st.error(f"❌ Lỗi: {e}")
                                    
                else:
                    st.info("📭 Chưa có dữ liệu T/h. Hãy import file vận hành cám viên.")
                    
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
    
    # TAB 2: Phân bổ tự động
    with tab2:
        st.header("🤖 Phân bổ Pellet tự động (Sử dụng T/h tối ưu)")
        
        st.info("💡 **Công suất sử dụng T/h tối ưu** từ dữ liệu vận hành thực tế. Nếu không có dữ liệu sẽ dùng công suất mặc định.")
        
        # Chọn ngày
        col1, col2 = st.columns(2)
        with col1:
            ngay_sx = st.date_input(
                "Ngày sản xuất", 
                value=fn.get_vietnam_time().date(),
                help="Chọn ngày cần phân bổ sản xuất Pellet",
                key="pellet_ngay_sx"
            )
        
        with col2:
            total_default = sum(DEFAULT_MACHINES.values())
            st.metric("Công suất mặc định", f"{total_default} tấn/giờ", help="7 máy: 10+10+9+9+8+8+8 tấn/giờ")
        
        if st.button("🔄 Phân bổ tự động", type="primary", key="btn_phan_bo"):
            with st.spinner("Đang tính toán phân bổ với T/h tối ưu..."):
                phan_bo = tinh_toan_phan_bo_pellet_v2(ngay_sx, DEFAULT_MACHINES)
                
                if phan_bo:
                    st.session_state['phan_bo_pellet'] = phan_bo
                    st.success(f"✅ Đã phân bổ xong! Tổng: {phan_bo['tong_san_luong']:.1f} tấn")
                    
                    # Hiển thị cảnh báo nếu có cám không có T/h
                    if phan_bo.get('warnings'):
                        with st.expander(f"⚠️ {len(phan_bo['warnings'])} cảnh báo", expanded=True):
                            for warn in phan_bo['warnings']:
                                st.warning(warn)
                else:
                    st.warning("⚠️ Không có kế hoạch cho ngày này")
        
        # Hiển thị kế hoạch đã tính
        if 'phan_bo_pellet' in st.session_state and st.session_state['phan_bo_pellet']:
            hien_thi_phan_bo_v2(st.session_state['phan_bo_pellet'], ngay_sx, DEFAULT_MACHINES)
    
    # TAB 3: Nhập thủ công
    with tab3:
        st.header("✍️ Nhập Pellet thủ công")
        
        # Lấy danh sách sản phẩm
        ds_sanpham = ss.get_columns_data(
            table_name='SanPham',
            columns=['Code cám', 'Tên cám', 'Dạng ép viên', 'Kích cỡ ép viên', 'ID'],
            data_type='list',
            col_where={'Đã xóa': ('=', 0)}
        )
        
        data = {
            'Ngày sản xuất': [None],
            'ID sản phẩm': [None],
            'Số lượng': [0],
            'Số máy': ['Pellet 1'],
            'Thời gian bắt đầu': [None],
            'Ghi chú': [None]
        }
        
        df = pd.DataFrame(data)
        
        machine_options = [MACHINE_DISPLAY[m] for m in DEFAULT_MACHINES.keys()]
        
        column_config = {
            'Ngày sản xuất': st.column_config.DateColumn('Ngày sản xuất', format='DD/MM/YYYY', width='medium'),
            'ID sản phẩm': st.column_config.SelectboxColumn(
                'ID sản phẩm', 
                options=ds_sanpham, 
                format_func=lambda x: x, 
                width='large',
                help="Chọn sản phẩm cần ép"
            ),
            'Số lượng': st.column_config.NumberColumn('Số lượng (tấn)', min_value=0, step=0.1, format="%.1f", width='small'),
            'Số máy': st.column_config.SelectboxColumn(
                'Số máy', 
                options=machine_options, 
                width='medium'
            ),
            'Thời gian bắt đầu': st.column_config.DatetimeColumn('Thời gian bắt đầu', format='DD/MM/YYYY HH:mm', width='medium'),
            'Ghi chú': st.column_config.TextColumn('Ghi chú', width='large')
        }
        
        df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='pellet_manual')
        
        df_insert = df_insert.dropna(subset=['ID sản phẩm'])
        df_insert = df_insert[df_insert['Số lượng'] > 0]
        
        # Tính toán thời gian kết thúc và thời gian chạy
        if len(df_insert) > 0:
            df_insert = fn.tachma_df(df_insert, column_names=['ID sản phẩm'], delimiter='|', index=-1)
            
            # Sử dụng công suất mặc định cho nhập thủ công
            reverse_display = {v: k for k, v in MACHINE_DISPLAY.items()}
            df_insert['Công suất máy (tấn/giờ)'] = df_insert['Số máy'].apply(
                lambda x: DEFAULT_MACHINES.get(reverse_display.get(x, 'PL1'), 8)
            )
            df_insert['Thời gian chạy (giờ)'] = df_insert.apply(
                lambda row: round(row['Số lượng'] / row['Công suất máy (tấn/giờ)'], 2), 
                axis=1
            )
            
            # Tính thời gian kết thúc
            df_insert['Thời gian kết thúc'] = df_insert.apply(
                lambda row: row['Thời gian bắt đầu'] + timedelta(hours=row['Thời gian chạy (giờ)']) 
                if pd.notna(row['Thời gian bắt đầu']) else None,
                axis=1
            )
            
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.dataframe(df_insert, width='content')
        
        disabled = not (len(df_insert) > 0)
        
        if st.button("Thêm Pellet", disabled=disabled, type="primary", key='btn_add_pellet'):
            result = ss.insert_data_to_sql_server(table_name='Pellet', dataframe=df_insert)
            show_notification("Lỗi:", result)
            if result[0]:
                st.session_state.pop('phan_bo_pellet', None)  # Xóa cache
    
    # TAB 4: Danh sách Pellet
    with tab4:
        st.header("📋 Danh sách Pellet hiện tại")
        
        column_config = {
            'Ngày sản xuất': st.column_config.DateColumn('Ngày sản xuất', format='DD/MM/YYYY'),
            'Thời gian bắt đầu': st.column_config.DatetimeColumn('Thời gian bắt đầu', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian kết thúc': st.column_config.DatetimeColumn('Thời gian kết thúc', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss'),
            'T/h': st.column_config.NumberColumn('T/h', format="%.2f"),
            'Kwh/T': st.column_config.NumberColumn('Kwh/T', format="%.2f")
        }
        
        dataframe_with_selections(
            table_name="Pellet",
            columns=[
                'ID', 'Ngày sản xuất', 'ID sản phẩm', 'Số lượng', 'Số máy',
                'Thời gian bắt đầu', 'Thời gian kết thúc', 'Thời gian chạy (giờ)',
                'Công suất máy (tấn/giờ)', 'T/h', 'Kwh/T', 'Ghi chú', 'Người tạo', 'Thời gian tạo'
            ],
            colums_disable=['ID', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'],
            col_where={'Đã xóa': ('=', 0)},
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
            key=f'Pellet_{st.session_state.df_key}',
            join_user_info=True
        )
    
    # TAB 5: Kế hoạch SX (PLAN PELLET MILL like Excel)
    with tab5:
        st.header("📊 Kế hoạch Sản xuất - PLAN PELLET MILL")
        st.caption("Layout giống file Excel KE HOACH PL - Hiển thị 7 máy x 3 ca")
        
        try:
            from utils.pellet_plan_utils import (
                calculate_pellet_plan_layout, 
                get_plan_data_for_date,
                save_pellet_plan,
                get_saved_pellet_plan
            )
            
            # Chọn ngày và tuần
            col_date, col_week, col_btn = st.columns([2, 1, 2])
            
            with col_date:
                ngay_plan = st.date_input(
                    "📅 Ngày kế hoạch",
                    value=fn.get_vietnam_time().date(),
                    key="pellet_plan_date"
                )
            
            with col_week:
                week_num = ngay_plan.isocalendar()[1]
                st.metric("📆 Tuần", week_num)
            
            with col_btn:
                if st.button("🔄 Tính toán phân bổ", type="primary", key="btn_calc_pellet_plan"):
                    with st.spinner("Đang tính toán phân bổ..."):
                        plan_data = calculate_pellet_plan_layout(ngay_plan)
                        if plan_data:
                            st.session_state['pellet_plan_layout'] = plan_data
                            st.success(f"✅ Đã tính toán! Tổng: {plan_data['totals']['PLAN_PL']['tons']} tấn")
                        else:
                            st.warning("⚠️ Không có Plan cho ngày này. Vui lòng tạo Plan trước.")
            
            st.markdown("---")
            
            # Hiển thị bảng PLAN PELLET MILL
            if 'pellet_plan_layout' in st.session_state:
                plan_data = st.session_state['pellet_plan_layout']
                
                # Header với Date và Week
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin: 0;">PLAN PELLET MILL</h2>
                    <p style="margin: 5px 0 0 0;">📅 {plan_data['date']} | 📆 Week {plan_data['week']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Tạo DataFrame cho bảng hiển thị
                machines = ['PL1', 'PL2', 'PL3', 'PL4', 'PL5', 'PL6', 'PL7']
                
                # Prepare data for each machine
                display_data = []
                
                # Row: TỒN ĐẦU (empty for now)
                row_ton_dau = {'Hạng mục': '🟢 TỒN ĐẦU'}
                for m in machines:
                    row_ton_dau[f'{m}_Code'] = ''
                    row_ton_dau[f'{m}_Mẻ'] = ''
                    row_ton_dau[f'{m}_Tons'] = ''
                    row_ton_dau[f'{m}_Giờ'] = ''
                display_data.append(row_ton_dau)
                
                # Rows for CA 1, CA 2, CA 3
                for ca in ['CA1', 'CA2', 'CA3']:
                    ca_display = ca.replace('CA', 'CA ')
                    
                    # Get max jobs in this shift across all machines
                    max_jobs = max(len(plan_data['machines'][m][ca]) for m in machines)
                    max_jobs = max(max_jobs, 1)  # At least 1 row
                    
                    for job_idx in range(max_jobs):
                        row = {'Hạng mục': f'🟡 {ca_display}' if job_idx == 0 else ''}
                        
                        for m in machines:
                            jobs = plan_data['machines'][m][ca]
                            if job_idx < len(jobs):
                                job = jobs[job_idx]
                                row[f'{m}_Code'] = job['code']
                                row[f'{m}_Mẻ'] = job['me']
                                row[f'{m}_Tons'] = job['tons']
                                row[f'{m}_Giờ'] = job['gio']
                            else:
                                row[f'{m}_Code'] = ''
                                row[f'{m}_Mẻ'] = ''
                                row[f'{m}_Tons'] = ''
                                row[f'{m}_Giờ'] = ''
                        
                        display_data.append(row)
                    
                    # Target row for this shift
                    row_target = {'Hạng mục': f'🔵 TARGET {ca_display}'}
                    for m in machines:
                        target = plan_data['machines'][m][f'TARGET_{ca}']
                        row_target[f'{m}_Code'] = ''
                        row_target[f'{m}_Mẻ'] = ''
                        row_target[f'{m}_Tons'] = target if target > 0 else ''
                        row_target[f'{m}_Giờ'] = ''
                    display_data.append(row_target)
                
                # TOTAL row
                row_total = {'Hạng mục': '⬜ TOTAL'}
                for m in machines:
                    row_total[f'{m}_Code'] = ''
                    row_total[f'{m}_Mẻ'] = ''
                    row_total[f'{m}_Tons'] = round(plan_data['machines'][m]['total_tons'], 1)
                    row_total[f'{m}_Giờ'] = round(plan_data['machines'][m]['total_hours'], 1)
                display_data.append(row_total)
                
                # PLAN PL row
                row_plan = {'Hạng mục': '⬜ PLAN PL'}
                total_hours = plan_data['totals']['PLAN_PL']['hours']
                total_tons = plan_data['totals']['PLAN_PL']['tons']
                row_plan['PL1_Code'] = 'HOURS'
                row_plan['PL1_Mẻ'] = ''
                row_plan['PL1_Tons'] = total_hours
                row_plan['PL1_Giờ'] = ''
                row_plan['PL2_Code'] = 'TONS'
                row_plan['PL2_Mẻ'] = ''
                row_plan['PL2_Tons'] = total_tons
                row_plan['PL2_Giờ'] = ''
                for m in machines[2:]:
                    row_plan[f'{m}_Code'] = ''
                    row_plan[f'{m}_Mẻ'] = ''
                    row_plan[f'{m}_Tons'] = ''
                    row_plan[f'{m}_Giờ'] = ''
                display_data.append(row_plan)
                
                # KHSX row
                row_khsx = {'Hạng mục': '⬜ KHSX (MX)'}
                row_khsx['PL1_Code'] = ''
                row_khsx['PL1_Mẻ'] = ''
                row_khsx['PL1_Tons'] = plan_data['totals']['KHSX']
                row_khsx['PL1_Giờ'] = ''
                for m in machines[1:]:
                    row_khsx[f'{m}_Code'] = ''
                    row_khsx[f'{m}_Mẻ'] = ''
                    row_khsx[f'{m}_Tons'] = ''
                    row_khsx[f'{m}_Giờ'] = ''
                display_data.append(row_khsx)
                
                df_plan = pd.DataFrame(display_data)
                
                # Display using data_editor for editing capability
                st.markdown("### 📋 Bảng phân bổ 7 máy Pellet")
                
                # Create column config for multi-column layout
                col_config = {
                    'Hạng mục': st.column_config.TextColumn('Hạng mục', width='medium')
                }
                
                for m in machines:
                    col_config[f'{m}_Code'] = st.column_config.TextColumn(f'{m} Code', width='small')
                    col_config[f'{m}_Mẻ'] = st.column_config.NumberColumn(f'{m} Mẻ', format='%.1f', width='small')
                    col_config[f'{m}_Tons'] = st.column_config.NumberColumn(f'{m} Tons', format='%.1f', width='small')
                    col_config[f'{m}_Giờ'] = st.column_config.NumberColumn(f'{m} Giờ', format='%.1f', width='small')
                
                # Show the table
                edited_df = st.data_editor(
                    df_plan,
                    column_config=col_config,
                    hide_index=True,
                    use_container_width=True,
                    key="pellet_plan_table_editor"
                )
                
                # Summary metrics
                st.markdown("---")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric("⏱️ Tổng giờ SX", f"{plan_data['totals']['PLAN_PL']['hours']:.1f} giờ")
                
                with col_m2:
                    st.metric("📦 Tổng sản lượng", f"{plan_data['totals']['PLAN_PL']['tons']:.1f} tấn")
                
                with col_m3:
                    st.metric("🏭 KHSX (Mixer)", f"{plan_data['totals']['KHSX']:.1f} tấn")
                
                with col_m4:
                    # Count active machines
                    active_machines = sum(1 for m in machines if plan_data['machines'][m]['total_tons'] > 0)
                    st.metric("🔧 Máy hoạt động", f"{active_machines}/7")
                
                # Save button
                st.markdown("---")
                col_save1, col_save2 = st.columns([1, 2])
                
                with col_save1:
                    if st.button("💾 Lưu kế hoạch", type="primary", key="btn_save_pellet_plan"):
                        try:
                            count = save_pellet_plan(
                                plan_data, 
                                ngay_plan, 
                                nguoi_tao=st.session_state.get('username', 'system')
                            )
                            st.success(f"✅ Đã lưu {count} dòng vào PelletPlan!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ Lỗi khi lưu: {e}")
                
                with col_save2:
                    if st.button("🗑️ Xóa dữ liệu tính toán", key="btn_clear_pellet_plan"):
                        del st.session_state['pellet_plan_layout']
                        st.rerun()
            
            else:
                # Check if there's saved data
                df_saved = get_saved_pellet_plan(ngay_plan)
                
                if len(df_saved) > 0:
                    st.info(f"📄 Đã có dữ liệu PelletPlan cho ngày {ngay_plan.strftime('%d/%m/%Y')}. Bấm nút để tính toán lại hoặc xem dữ liệu đã lưu.")
                    
                    with st.expander("📋 Xem dữ liệu đã lưu", expanded=False):
                        st.dataframe(df_saved, hide_index=True, use_container_width=True)
                else:
                    # Show instructions
                    st.info("""
                    ### 📋 Hướng dẫn sử dụng
                    
                    1. **Chọn ngày** kế hoạch muốn xem
                    2. **Bấm "Tính toán phân bổ"** để tự động phân bổ Plan vào 7 máy
                    3. **Chỉnh sửa trực tiếp** trên bảng nếu cần
                    4. **Bấm "Lưu kế hoạch"** để lưu vào database
                    
                    > ⚠️ Lưu ý: Cần có dữ liệu Plan cho ngày được chọn. Nếu chưa có, vào menu **Plan** để tạo kế hoạch.
                    """)
        
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
            import traceback
            with st.expander("Chi tiết lỗi"):
                st.code(traceback.format_exc())


def tinh_toan_phan_bo_pellet_v2(ngay_sx, DEFAULT_MACHINES):
    """
    Tính toán phân bổ tự động cho 7 máy Pellet
    SỬ DỤNG T/h TỐI ƯU từ dữ liệu thực tế
    
    Logic:
    1. Lấy kế hoạch từ bảng Plan
    2. Với mỗi loại cám, tìm T/h tối ưu cho từng máy
    3. Ưu tiên phân bổ vào máy có T/h cao nhất
    4. Nếu máy full, chuyển sang máy khác (T/h thấp hơn)
    5. Nếu không có dữ liệu T/h, dùng công suất mặc định + cảnh báo
    """
    from utils.pellet_capacity_importer import PelletCapacityImporter
    
    conn = ss.connect_db()
    
    # Lấy kế hoạch từ bảng Plan
    query = """
    SELECT 
        p.ID,
        p.[Mã plan],
        sp.[Code cám],
        sp.[Tên cám] as [Tên sản phẩm],
        p.[Số lượng],
        sp.[Dạng ép viên]
    FROM Plan p
    LEFT JOIN SanPham sp ON p.[ID sản phẩm] = sp.ID
    WHERE p.[Ngày plan] = ? 
    AND p.[Đã xóa] = 0
    ORDER BY p.[Số lượng] DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(ngay_sx,))
    conn.close()
    
    if len(df) == 0:
        return None
    
    # Khởi tạo importer để lấy T/h tối ưu
    importer = PelletCapacityImporter()
    
    # Khởi tạo trạng thái máy
    machines = {}
    for machine_code, default_cap in DEFAULT_MACHINES.items():
        machines[machine_code] = {
            'capacity': default_cap,  # Công suất mặc định
            'hours_used': 0,
            'jobs': []
        }
    
    # Phân bổ từng công việc
    phan_bo = []
    warnings = []
    
    for _, job in df.iterrows():
        code_cam = job['Code cám']
        so_luong = job['Số lượng']
        
        # Tìm T/h của tất cả máy cho loại cám này
        df_machines = importer.get_all_machines_for_feed(code_cam)
        
        if len(df_machines) > 0:
            # Có dữ liệu T/h - ưu tiên máy có T/h cao nhất còn trống
            allocated = False
            
            for _, machine_row in df_machines.iterrows():
                machine_code = machine_row['Số máy']
                optimal_th = machine_row['T/h']
                kwh_t = machine_row.get('Kwh/T', 0)
                
                if machine_code in machines:
                    # Tính thời gian cần thiết với T/h tối ưu
                    hours_needed = so_luong / optimal_th if optimal_th > 0 else so_luong / DEFAULT_MACHINES[machine_code]
                    
                    # Kiểm tra máy còn trống không
                    if machines[machine_code]['hours_used'] + hours_needed <= 24:
                        # Phân bổ vào máy này
                        phan_bo.append({
                            'ID Kế hoạch': job['ID'],
                            'Mã plan': job['Mã plan'],
                            'Code cám': code_cam,
                            'Tên sản phẩm': job['Tên sản phẩm'],
                            'Số lượng': so_luong,
                            'Số máy': machine_code,
                            'T/h': optimal_th,
                            'Kwh/T': kwh_t,
                            'Thời gian chạy (giờ)': round(hours_needed, 2),
                            'Nguồn T/h': 'Từ dữ liệu thực tế'
                        })
                        
                        machines[machine_code]['hours_used'] += hours_needed
                        machines[machine_code]['jobs'].append(job['Tên sản phẩm'])
                        allocated = True
                        break
            
            if not allocated:
                # Tất cả máy đã full, cảnh báo
                warnings.append(f"⚠️ {code_cam}: Tất cả máy đã đầy, không thể phân bổ {so_luong} tấn")
        else:
            # KHÔNG có dữ liệu T/h - dùng công suất mặc định + cảnh báo
            warnings.append(f"📢 {code_cam}: Không có dữ liệu T/h, dùng công suất mặc định")
            
            # Tìm máy trống có công suất cao nhất
            best_machine = None
            best_capacity = 0
            
            for machine_code, info in machines.items():
                if info['hours_used'] < 24:
                    default_cap = DEFAULT_MACHINES[machine_code]
                    if default_cap > best_capacity:
                        best_capacity = default_cap
                        best_machine = machine_code
            
            if best_machine:
                hours_needed = so_luong / best_capacity
                
                if machines[best_machine]['hours_used'] + hours_needed <= 24:
                    phan_bo.append({
                        'ID Kế hoạch': job['ID'],
                        'Mã plan': job['Mã plan'],
                        'Code cám': code_cam,
                        'Tên sản phẩm': job['Tên sản phẩm'],
                        'Số lượng': so_luong,
                        'Số máy': best_machine,
                        'T/h': best_capacity,
                        'Kwh/T': None,
                        'Thời gian chạy (giờ)': round(hours_needed, 2),
                        'Nguồn T/h': 'Mặc định (chưa có dữ liệu)'
                    })
                    
                    machines[best_machine]['hours_used'] += hours_needed
                    machines[best_machine]['jobs'].append(job['Tên sản phẩm'])
    
    tong_san_luong = sum(item['Số lượng'] for item in phan_bo)
    
    return {
        'phan_bo': phan_bo,
        'machines': machines,
        'tong_san_luong': tong_san_luong,
        'warnings': warnings
    }


def hien_thi_phan_bo_v2(data, ngay_sx, DEFAULT_MACHINES):
    """Hiển thị kết quả phân bổ với T/h và Kwh/T"""
    
    MACHINE_DISPLAY = {
        'PL1': 'Pellet 1', 'PL2': 'Pellet 2', 'PL3': 'Pellet 3',
        'PL4': 'Pellet 4', 'PL5': 'Pellet 5', 'PL6': 'Pellet 6', 'PL7': 'Pellet 7'
    }
    
    st.subheader(f"📅 Phân bổ ngày {ngay_sx.strftime('%d/%m/%Y')}")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng sản lượng", f"{data['tong_san_luong']:.1f} tấn")
    with col2:
        machines_used = len([m for m in data['machines'].values() if m['hours_used'] > 0])
        st.metric("Số máy sử dụng", f"{machines_used}/7 máy")
    with col3:
        avg_hours = sum(m['hours_used'] for m in data['machines'].values()) / len(data['machines'])
        st.metric("Trung bình giờ chạy", f"{avg_hours:.1f} giờ/máy")
    
    # Hiển thị bảng phân bổ
    if data['phan_bo']:
        df_phan_bo = pd.DataFrame(data['phan_bo'])
        
        # Đổi tên số máy sang tên hiển thị
        df_phan_bo['Số máy'] = df_phan_bo['Số máy'].map(MACHINE_DISPLAY)
        
        st.dataframe(
            df_phan_bo[[
                'Mã plan', 'Code cám', 'Tên sản phẩm', 'Số lượng', 
                'Số máy', 'T/h', 'Kwh/T', 'Thời gian chạy (giờ)', 'Nguồn T/h'
            ]],
            column_config={
                'Số lượng': st.column_config.NumberColumn('Số lượng (tấn)', format="%.1f"),
                'T/h': st.column_config.NumberColumn('T/h', format="%.2f"),
                'Kwh/T': st.column_config.NumberColumn('Kwh/T', format="%.2f"),
                'Thời gian chạy (giờ)': st.column_config.NumberColumn('Giờ chạy', format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Hiển thị từng máy
    st.markdown("### 🔧 Chi tiết từng máy")
    
    for machine_code, machine_info in data['machines'].items():
        if machine_info['hours_used'] > 0:
            display_name = MACHINE_DISPLAY.get(machine_code, machine_code)
            default_cap = DEFAULT_MACHINES.get(machine_code, 8)
            
            with st.expander(f"🔧 {display_name} - Mặc định {default_cap} tấn/giờ", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Danh sách công việc
                    machine_jobs = [job for job in data['phan_bo'] if job['Số máy'] == machine_code]
                    if machine_jobs:
                        df_jobs = pd.DataFrame(machine_jobs)
                        st.dataframe(
                            df_jobs[['Tên sản phẩm', 'Số lượng', 'T/h', 'Kwh/T', 'Thời gian chạy (giờ)']],
                            hide_index=True
                        )
                
                with col2:
                    st.metric("Thời gian chạy", f"{machine_info['hours_used']:.1f} / 24 giờ")
                    
                    # Progress bar
                    progress = machine_info['hours_used'] / 24
                    st.progress(progress)
                    
                    # Cảnh báo nếu gần đầy
                    if machine_info['hours_used'] > 20:
                        st.warning("⚠️ Gần đạt giới hạn!")
                    elif machine_info['hours_used'] > 16:
                        st.info("ℹ️ Tải cao")
    
    # Nút lưu
    if st.button("💾 Lưu phân bổ vào Database", type="primary", key="btn_save_phanbo"):
        luu_phan_bo_v2(data['phan_bo'], ngay_sx)


def luu_phan_bo_v2(phan_bo, ngay_sx):
    """Lưu phân bổ vào database với T/h và Kwh/T"""
    
    MACHINE_DISPLAY = {
        'PL1': 'Pellet 1', 'PL2': 'Pellet 2', 'PL3': 'Pellet 3',
        'PL4': 'Pellet 4', 'PL5': 'Pellet 5', 'PL6': 'Pellet 6', 'PL7': 'Pellet 7'
    }
    
    df = pd.DataFrame(phan_bo)
    df['Ngày sản xuất'] = ngay_sx
    df['Người tạo'] = st.session_state.username
    df['Thời gian tạo'] = fn.get_vietnam_time()
    
    # Đổi tên máy sang tên hiển thị để lưu
    df['Số máy'] = df['Số máy'].map(MACHINE_DISPLAY)
    
    # Rename cột để match với database
    df = df.rename(columns={
        'Thời gian chạy (giờ)': 'Thời gian chạy (giờ)',
        'T/h': 'Công suất máy (tấn/giờ)'  # Map T/h vào cột công suất
    })
    
    # Tính thời gian bắt đầu và kết thúc (giả định bắt đầu từ 7:00)
    start_time = datetime.combine(ngay_sx, datetime.min.time()).replace(hour=7)
    
    for idx, row in df.iterrows():
        df.at[idx, 'Thời gian bắt đầu'] = start_time
        df.at[idx, 'Thời gian kết thúc'] = start_time + timedelta(hours=row['Thời gian chạy (giờ)'])
        start_time = df.at[idx, 'Thời gian kết thúc']
    
    # Chọn cột để lưu
    columns_to_save = [
        'Ngày sản xuất', 'ID Kế hoạch', 'Số lượng', 'Số máy',
        'Công suất máy (tấn/giờ)', 'Kwh/T', 'Thời gian chạy (giờ)',
        'Thời gian bắt đầu', 'Thời gian kết thúc',
        'Người tạo', 'Thời gian tạo'
    ]
    
    # Chỉ lấy các cột có trong df
    columns_to_save = [c for c in columns_to_save if c in df.columns]
    df_save = df[columns_to_save]
    
    result = ss.insert_data_to_sql_server(table_name='Pellet', dataframe=df_save)
    show_notification("Lỗi:", result)
    
    if result[0]:
        st.session_state.pop('phan_bo_pellet', None)  # Xóa cache
        st.rerun()


# Legacy function for backward compatibility
def tinh_toan_phan_bo_pellet(ngay_sx):
    """Legacy function - redirects to v2"""
    DEFAULT_MACHINES = {
        'PL1': 10, 'PL2': 10, 'PL3': 9,
        'PL4': 9, 'PL5': 8, 'PL6': 8, 'PL7': 8
    }
    return tinh_toan_phan_bo_pellet_v2(ngay_sx, DEFAULT_MACHINES)


def hien_thi_phan_bo(data, ngay_sx, MACHINES):
    """Legacy function - redirects to v2"""
    DEFAULT_MACHINES = {
        'PL1': 10, 'PL2': 10, 'PL3': 9,
        'PL4': 9, 'PL5': 8, 'PL6': 8, 'PL7': 8
    }
    hien_thi_phan_bo_v2(data, ngay_sx, DEFAULT_MACHINES)


def luu_phan_bo(phan_bo, ngay_sx):
    """Legacy function - redirects to v2"""
    luu_phan_bo_v2(phan_bo, ngay_sx)
