import streamlit as st
from admin.sys_kde_components import *
import pandas as pd
from datetime import datetime

# Mapping vật nuôi
VAT_NUOI_LABELS = {
    'H': 'HEO', 'G': 'GÀ', 'B': 'BÒ', 
    'V': 'VỊT', 'C': 'CÚT', 'D': 'DÊ'
}

# Batch size options
BATCH_SIZES = [8000, 8400]

# Đích đến options
DICH_DEN_OPTIONS = ['Pellet', 'Packing']

# Số máy options
SO_MAY_OPTIONS = ['Pellet 1', 'Pellet 2', 'Pellet 3', 'Pellet 4', 'Pellet 5', 'Pellet 6', 'Pellet 7', 'Packing 3']

# Ca sản xuất
CA_SAN_XUAT = ['Ca 1', 'Ca 2', 'Ca 3']

def app(selected):
    
    # Tạo tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Danh sách Batching",
        "📁 Import Excel",
        "✍️ Nhập thủ công"
    ])
    
    # TAB 3: Nhập thủ công
    with tab3:
        st.header("✍️ Nhập Batching thủ công")
        
        st.info("""
        **Batching** là máy trộn cám với batch size 8000 hoặc 8400 kg.
        - Trộn: đạm, xơ, tinh bột, vitamin, khoáng chất, liquid và phụ gia
        - Đích đến: **Pellet** (ép viên) hoặc **Packing** (cám bột - Mash)
        """)
        
        # Lấy danh sách sản phẩm
        ds_sanpham = ss.get_columns_data(
            table_name='SanPham',
            columns=['Code cám', 'Tên cám', 'Batch size', 'ID'],
            data_type='list',
            col_where={'Đã xóa': ('=', 0)}
        )
        
        # Form nhập liệu
        col1, col2 = st.columns(2)
        
        with col1:
            ngay_tron = st.date_input(
                "📅 Ngày trộn",
                value=fn.get_vietnam_time().date(),
                help="Chọn ngày trộn"
            )
            
            batch_size = st.selectbox(
                "⚖️ Batch size (kg)",
                options=BATCH_SIZES,
                index=1,  # Default 8400
                help="Kích thước batch: 8000 hoặc 8400 kg"
            )
            
            dich_den = st.selectbox(
                "🎯 Đích đến",
                options=DICH_DEN_OPTIONS,
                help="Pellet = ép viên, Packing = cám bột (Mash)"
            )
        
        with col2:
            so_luong_thuc_te = st.number_input(
                "📊 Số lượng thực tế (kg)",
                min_value=0.0,
                max_value=float(batch_size),
                value=float(batch_size - 50),  # Default loss ~50kg
                step=10.0,
                help="Số lượng sau khi trộn xong"
            )
            
            ca_san_xuat = st.selectbox(
                "🕐 Ca sản xuất",
                options=CA_SAN_XUAT,
                help="Ca 1, Ca 2 hoặc Ca 3"
            )
            
            # Số máy - tùy theo đích đến
            if dich_den == 'Pellet':
                so_may_options = ['Pellet 1', 'Pellet 2', 'Pellet 3', 'Pellet 4', 'Pellet 5', 'Pellet 6', 'Pellet 7']
            else:
                so_may_options = ['Packing 3']
            
            so_may = st.selectbox(
                "🔧 Số máy",
                options=so_may_options,
                help="Máy đích đến sau khi trộn"
            )
        
        # Chọn sản phẩm
        san_pham = st.selectbox(
            "🏷️ Sản phẩm",
            options=ds_sanpham,
            help="Chọn sản phẩm cần trộn"
        )
        
        ghi_chu = st.text_area(
            "📝 Ghi chú",
            placeholder="Nhập ghi chú nếu có...",
            height=80
        )
        
        # Tính toán Loss
        loss_kg = batch_size - so_luong_thuc_te
        loss_percent = (loss_kg / batch_size) * 100 if batch_size > 0 else 0
        
        # Hiển thị Loss metrics
        st.markdown("### 📉 Thông tin Loss (Hao hụt)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Loss (kg)", f"{loss_kg:,.0f} kg")
        with col2:
            st.metric("Loss (%)", f"{loss_percent:.2f}%")
        with col3:
            # Cảnh báo nếu loss cao
            if loss_percent > 2:
                st.error("⚠️ Loss cao!")
            elif loss_percent > 1:
                st.warning("⚡ Loss trung bình")
            else:
                st.success("✅ Loss bình thường")
        
        # Nút lưu
        if st.button("💾 Lưu Batching", type="primary", width="stretch"):
            if san_pham:
                # Tách ID sản phẩm
                id_san_pham = san_pham.split('|')[-1].strip() if '|' in san_pham else None
                
                # Tạo mã mixer tự động
                ma_mixer = ss.generate_next_code(
                    tablename='Mixer',
                    column_name='Mã mixer',
                    prefix='MX',
                    num_char=5
                )
                
                # Tạo dataframe để insert
                df_insert = pd.DataFrame([{
                    'Mã mixer': ma_mixer,
                    'Ngày trộn': ngay_tron,
                    'ID sản phẩm': id_san_pham,
                    'Batch size': batch_size,
                    'Số lượng thực tế': so_luong_thuc_te,
                    'Loss (kg)': loss_kg,
                    'Loss (%)': round(loss_percent, 2),
                    'Đích đến': dich_den,
                    'Số máy': so_may,
                    'Ca sản xuất': ca_san_xuat,
                    'Ghi chú': ghi_chu if ghi_chu else None,
                    'Người tạo': st.session_state.username,
                    'Thời gian tạo': fn.get_vietnam_time()
                }])
                
                result = ss.insert_data_to_sql_server(table_name='Mixer', dataframe=df_insert)
                show_notification("Lỗi:", result)
                
                if result[0]:
                    st.success(f"✅ Đã lưu! Mã mixer: **{ma_mixer}**")
                    st.session_state.df_key += 1  # Refresh danh sách
            else:
                st.error("Vui lòng chọn sản phẩm!")
    
    # TAB 2: Import Excel
    with tab2:
        st.header("📁 Import Batching từ Excel")
        
        st.info("""
        **Hướng dẫn:**
        - **File CSV**: Import trực tiếp từ file PRODUCTION*.csv
        - **File XLSM**: Import từ file đã chạy VBA TransposeReport (dữ liệu ở cột CA-CF)
        """)
        
        # Import ProductionImporter
        try:
            from utils.production_importer import ProductionImporter
            IMPORTER_AVAILABLE = True
        except ImportError:
            IMPORTER_AVAILABLE = False
        
        if not IMPORTER_AVAILABLE:
            st.error("❌ Không thể import module ProductionImporter")
            return
        
        # File uploader
        uploaded_file = st.file_uploader(
            "📤 Chọn file Excel hoặc CSV",
            type=['xlsx', 'xlsm', 'csv'],
            help="Chọn file PRODUCTION (CSV hoặc XLSM đã chạy VBA)"
        )
        
        # Date selector
        col1, col2 = st.columns(2)
        with col1:
            ngay_san_xuat = st.date_input(
                "📅 Ngày sản xuất",
                value=fn.get_vietnam_time().date(),
                help="Chọn ngày sản xuất cho dữ liệu import"
            )
        with col2:
            overwrite = st.checkbox(
                "🔄 Ghi đè nếu đã import",
                value=False,
                help="Nếu tick, sẽ xóa dữ liệu cũ và import lại"
            )
        
        if uploaded_file:
            try:
                # Lưu file tạm
                import tempfile
                import os
                
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                importer = ProductionImporter()
                
                # Preview section
                st.subheader("👀 Xem trước dữ liệu")
                
                if file_ext == 'csv':
                    # Preview CSV
                    df_preview = pd.read_csv(tmp_path, header=None, encoding='utf-8-sig')
                    st.caption(f"📊 File CSV có {len(df_preview)} hàng x {len(df_preview.columns)} cột")
                    st.dataframe(df_preview.head(20), width="stretch")
                    import_type = 'csv'
                else:
                    # Preview XLSM/XLSX - dùng hàm preview
                    df_preview = importer.preview_production_xlsm(tmp_path)
                    
                    if len(df_preview) > 0:
                        st.success(f"✅ Tìm thấy {len(df_preview)} sản phẩm trong file")
                        
                        # Hiển thị preview với format đẹp
                        st.dataframe(
                            df_preview,
                            column_config={
                                'Required (kg)': st.column_config.NumberColumn('Required (kg)', format='%,.0f'),
                                'Actual (kg)': st.column_config.NumberColumn('Actual (kg)', format='%,.0f'),
                                'Deviation (kg)': st.column_config.NumberColumn('Deviation (kg)', format='%,.2f'),
                                'Deviation (%)': st.column_config.NumberColumn('Deviation (%)', format='%.2f'),
                            },
                            width="stretch"
                        )
                        import_type = 'xlsm'
                    else:
                        st.warning("⚠️ Không tìm thấy dữ liệu ở cột CA-CF. Hãy đảm bảo đã chạy VBA TransposeReport!")
                        import_type = None
                
                # Import button
                if import_type:
                    st.markdown("---")
                    if st.button("📥 Import vào Database", type="primary", width="stretch"):
                        with st.spinner("Đang import..."):
                            ngay_sx_str = ngay_san_xuat.strftime('%Y-%m-%d')
                            username = st.session_state.get('username', 'system')
                            
                            if import_type == 'csv':
                                result = importer.import_production(
                                    file_path=tmp_path,
                                    nguoi_import=username,
                                    ngay_san_xuat=ngay_sx_str,
                                    overwrite=overwrite
                                )
                            else:  # xlsm
                                result = importer.import_production_xlsm(
                                    file_path=tmp_path,
                                    nguoi_import=username,
                                    ngay_san_xuat=ngay_sx_str,
                                    overwrite=overwrite
                                )
                            
                            # Hiển thị kết quả
                            if result.get('skipped'):
                                st.warning(f"⚠️ File đã được import trước đó! Tick 'Ghi đè' để import lại.")
                            elif result['success'] > 0:
                                st.success(f"✅ Import thành công **{result['success']}** sản phẩm!")
                                st.balloons()
                                
                                # Hiển thị sản phẩm không tìm thấy
                                not_found = result.get('not_found', [])
                                if not_found:
                                    with st.expander(f"⚠️ {len(not_found)} mã không tìm thấy trong danh sách sản phẩm"):
                                        for code in not_found[:30]:
                                            st.text(f"- {code}")
                                        if len(not_found) > 30:
                                            st.text(f"... và {len(not_found) - 30} mã khác")
                                
                                errors = result.get('errors', [])
                                if errors:
                                    with st.expander(f"❌ {len(errors)} lỗi"):
                                        for err in errors[:10]:
                                            st.text(err)
                                
                                st.session_state.df_key += 1
                            else:
                                st.error("❌ Không import được sản phẩm nào!")
                                if result.get('errors'):
                                    for err in result['errors']:
                                        st.error(err)
                
                # Cleanup temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
            except Exception as e:
                st.error(f"❌ Lỗi đọc file: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())
    
    
    # TAB 1: Danh sách Mixer
    with tab1:
        st.header("📋 Danh sách Batching")
        
        # Lấy ngày gần nhất có dữ liệu
        import sqlite3
        try:
            conn_check = sqlite3.connect('database_new.db')
            cursor = conn_check.cursor()
            cursor.execute("SELECT MAX([Ngày trộn]) FROM Mixer WHERE [Đã xóa] = 0")
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
            filter_date_from = st.date_input(
                "Lọc từ ngày",
                value=default_date,
                help="Ngày bắt đầu lọc"
            )
        with col2:
            filter_date_to = st.date_input(
                "Đến ngày",
                value=default_date,
                help="Ngày kết thúc lọc"
            )
        with col3:
            filter_dich_den = st.selectbox(
                "Lọc theo đích đến",
                options=['Tất cả'] + DICH_DEN_OPTIONS,
                help="Lọc theo Pellet hoặc Packing"
            )
        with col4:
            filter_ca = st.selectbox(
                "Lọc theo ca",
                options=['Tất cả'] + CA_SAN_XUAT,
                help="Lọc theo ca sản xuất"
            )
        
        # Build filter conditions
        col_where = {'Đã xóa': ('=', 0)}
        if filter_date_from and filter_date_to:
            col_where['Ngày trộn'] = {'Between': [filter_date_from.strftime('%Y-%m-%d'), filter_date_to.strftime('%Y-%m-%d')]}
            # Mặc định hiển thị All khi lọc theo ngày
            st.session_state.page_size = 'All'
        elif filter_date_from:
            col_where['Ngày trộn'] = ('>=', filter_date_from.strftime('%Y-%m-%d'))
            st.session_state.page_size = 'All'
        if filter_dich_den != 'Tất cả':
            col_where['Đích đến'] = ('=', filter_dich_den)
        if filter_ca != 'Tất cả':
            col_where['Ca sản xuất'] = ('=', filter_ca)
        
        column_config = {
            'Ngày trộn': st.column_config.TextColumn('Ngày trộn'),
            'Batch size': st.column_config.NumberColumn('Batch size (kg)', format="%,.0f"),
            'Số lượng thực tế': st.column_config.NumberColumn('SL thực tế (kg)', format="%,.0f"),
            'Loss (kg)': st.column_config.NumberColumn('Loss (kg)', format="%,.0f"),
            'Loss (%)': st.column_config.NumberColumn('Loss (%)', format="%.2f"),
            'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm'),
            'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm')
        }
        
        # Hàm format ngày từ yyyy-mm-dd thành dd-mm-yyyy
        def format_date_column(df):
            if 'Ngày trộn' in df.columns:
                df['Ngày trộn'] = df['Ngày trộn'].apply(
                    lambda x: '-'.join(str(x).split('-')[::-1]) if x and '-' in str(x) else x
                )
            return df
        
        dataframe_with_selections(
            table_name="Mixer",
            columns=[
                'ID', 'Mã mixer', 'Ngày trộn', 'ID sản phẩm', 'Batch size',
                'Số lượng thực tế', 'Loss (kg)', 'Loss (%)', 'Ghi chú',
                'Người tạo', 'Thời gian tạo'
            ],
            colums_disable=['ID', 'Mã mixer', 'Loss (kg)', 'Loss (%)', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'],
            col_where=col_where,
            col_order={'Ngày trộn': 'DESC', 'ID': 'DESC'},
            joins=[
                {
                    'table': 'SanPham',
                    'on': {'ID sản phẩm': 'ID'},
                    'columns': ['Code cám', 'Tên cám'],
                    'replace_multi': {'ID sản phẩm': ['Code cám', 'Tên cám']}
                }
            ],
            column_config=column_config,
            key=f'Mixer_{st.session_state.df_key}',
            join_user_info=False,
            post_process_func=format_date_column
        )
        
        # Thống kê tổng hợp
        st.markdown("---")
        st.subheader("📊 Thống kê")
        
        try:
            import sqlite3
            conn = sqlite3.connect('database_new.db')
            
            # Điều kiện lọc theo ngày
            date_condition = ""
            if filter_date_from and filter_date_to:
                date_condition = f"AND [Ngày trộn] BETWEEN '{filter_date_from.strftime('%Y-%m-%d')}' AND '{filter_date_to.strftime('%Y-%m-%d')}'"
            elif filter_date_from:
                date_condition = f"AND [Ngày trộn] >= '{filter_date_from.strftime('%Y-%m-%d')}'"
            
            # Query thống kê
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_batches,
                    SUM([Batch size]) as total_input,
                    SUM([Số lượng thực tế]) as total_output,
                    SUM([Loss (kg)]) as total_loss,
                    AVG([Loss (%)]) as avg_loss_percent
                FROM Mixer
                WHERE [Đã xóa] = 0
                {date_condition}
            """
            
            stats = pd.read_sql_query(stats_query, conn)
            conn.close()
            
            if len(stats) > 0 and stats['total_batches'].iloc[0] > 0:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tổng code cám", f"{stats['total_batches'].iloc[0]:,.0f}")
                with col2:
                    st.metric("Tổng đầu vào", f"{stats['total_input'].iloc[0]:,.0f} kg")
                with col3:
                    st.metric("Tổng đầu ra", f"{stats['total_output'].iloc[0]:,.0f} kg")
                with col4:
                    avg_loss = stats['avg_loss_percent'].iloc[0] or 0
                    st.metric("TB Loss", f"{avg_loss:.2f}%")
            else:
                st.info("Chưa có dữ liệu thống kê cho ngày này")
                
        except Exception as e:
            st.warning(f"Không thể tải thống kê: {e}")
