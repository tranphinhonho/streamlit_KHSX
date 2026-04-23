import streamlit as st
from admin.sys_kde_components import *

def app(selected):
    
    # Tabs: Tính toán tự động đưa lên đầu, Nhập thủ công xuống sau
    tab1, tab2 = st.tabs(["🧮 Tính toán tự động", "📝 Nhập thủ công"])
    
    with tab1:
        st.header("Tính toán Stock đầu ngày")
        
        st.markdown("""
        **Công thức:** Stock đầu ngày (N) = Stock Old (N-2) + Packing (N-1) - Sale (N-1)
        """)
        
        # Chọn ngày tính toán
        from datetime import timedelta
        
        col1, col2 = st.columns(2)
        with col1:
            ngay_tinh = st.date_input("📅 Ngày tính toán (Stock đầu ngày)", value=fn.get_vietnam_time().date())
        
        with col2:
            st.write("")  # Spacing
        
        # Tính ngày mặc định
        default_ngay_stock_old = ngay_tinh - timedelta(days=2)  # N-2
        default_ngay_packing_sale = ngay_tinh - timedelta(days=1)  # N-1
        
        st.markdown("---")
        st.markdown("**⚙️ Tùy chỉnh ngày lấy dữ liệu** (điều chỉnh khi có ngày nghỉ):")
        
        col_so, col_pk, col_sl = st.columns(3)
        with col_so:
            ngay_stock_old = st.date_input(
                "📦 Ngày Stock Old", 
                value=default_ngay_stock_old,
                help="Mặc định: N-2 (2 ngày trước ngày tính toán)"
            )
        with col_pk:
            ngay_packing = st.date_input(
                "🏭 Ngày Packing", 
                value=default_ngay_packing_sale,
                help="Mặc định: N-1 (1 ngày trước ngày tính toán)"
            )
        with col_sl:
            ngay_sale = st.date_input(
                "🚚 Ngày Sale", 
                value=default_ngay_packing_sale,
                help="Mặc định: N-1 (1 ngày trước ngày tính toán)"
            )
        
        # Hiển thị công thức thực tế
        st.info(f"📊 **Công thức thực tế:** Stock đầu ngày {ngay_tinh.strftime('%d/%m/%Y')} = Stock Old ({ngay_stock_old.strftime('%d/%m/%Y')}) + Packing ({ngay_packing.strftime('%d/%m/%Y')}) - Sale ({ngay_sale.strftime('%d/%m/%Y')})")
        
        st.markdown("---")
        
        # Khởi tạo session state
        if 'calculation_results' not in st.session_state:
            st.session_state.calculation_results = None
        
        # Button tính toán
        if st.button("🧮 Tính toán", type="primary", width="stretch"):
            import sqlite3
            from datetime import datetime
            
            try:
                conn = ss.connect_db()
                cursor = conn.cursor()
                
                # Lấy tất cả sản phẩm
                cursor.execute("""
                    SELECT ID, [Code cám], [Tên cám]
                    FROM SanPham
                    WHERE [Đã xóa] = 0
                """)
                all_products = cursor.fetchall()
                
                st.info(f"📊 Đang xử lý {len(all_products)} sản phẩm...")
                
                # Tính toán cho từng sản phẩm
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Sử dụng các ngày đã chọn (có thể tùy chỉnh khi có ngày nghỉ)
                ngay_n_minus_2 = ngay_stock_old.strftime('%Y-%m-%d')  # Stock Old
                ngay_n_minus_1_packing = ngay_packing.strftime('%Y-%m-%d')  # Packing
                ngay_n_minus_1_sale = ngay_sale.strftime('%Y-%m-%d')  # Sale
                
                # === TÍNH GHI CHÚ 2: Tìm thứ 7 gần nhất và khoảng tuần ===
                # weekday(): Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
                is_saturday = ngay_tinh.weekday() == 5  # Kiểm tra có phải thứ 7 không
                
                # Tuần B (tuần hiện tại): T7 hiện tại
                if is_saturday:
                    saturday_B = ngay_tinh  # Nếu hôm nay là T7, dùng hôm nay
                else:
                    days_since_saturday = (ngay_tinh.weekday() + 2) % 7
                    if days_since_saturday == 0:
                        days_since_saturday = 7
                    saturday_B = ngay_tinh - timedelta(days=days_since_saturday)
                
                friday_B = saturday_B + timedelta(days=6)  # T6 tuần sau
                
                # Tuần A (tuần trước): T7 tuần trước
                saturday_A = saturday_B - timedelta(days=7)
                friday_A = saturday_A + timedelta(days=6)  # T6 của tuần A
                
                # Format dates
                ngay_t7_A = saturday_A.strftime('%Y-%m-%d')
                ngay_t6_A = friday_A.strftime('%Y-%m-%d')
                ngay_t7_B = saturday_B.strftime('%Y-%m-%d')
                ngay_t6_B = friday_B.strftime('%Y-%m-%d')
                
                # Hiển thị thông tin tuần cho user
                if is_saturday:
                    st.info(f"📅 **Ngày thứ 7**: Tính cả 2 Ghi chú 2 (A và B)\n\n"
                            f"- **Tuần A**: Stock T7 ({saturday_A.strftime('%d/%m/%Y')}) + Batching ({saturday_A.strftime('%d/%m')}-{friday_A.strftime('%d/%m')}) - Forecast/KVL\n"
                            f"- **Tuần B**: Stock T7 ({saturday_B.strftime('%d/%m/%Y')}) + Batching ({saturday_B.strftime('%d/%m')}-{friday_B.strftime('%d/%m')}) - Forecast/KVL")
                
                for idx, (id_sanpham, code_cam, ten_cam) in enumerate(all_products):
                    
                    # Stock Old - lấy theo ngày N-2
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM StockOld
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                        AND [Ngày stock old] = ?
                    """, (id_sanpham, ngay_n_minus_2))
                    stock_old = cursor.fetchone()[0]
                    
                    # Packing - lấy theo ngày N-1
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM Packing
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                        AND [Ngày packing] = ?
                    """, (id_sanpham, ngay_n_minus_1_packing))
                    packing = cursor.fetchone()[0]
                    
                    # Sale - lấy theo ngày N-1
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM Sale
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                        AND [Ngày sale] = ?
                    """, (id_sanpham, ngay_n_minus_1_sale))
                    sale = cursor.fetchone()[0]
                    
                    # Tính toán Stock đầu ngày
                    stock_hom_nay = stock_old + packing - sale
                    
                    # === TÍNH GHI CHÚ 2 - TUẦN B (tuần hiện tại) ===
                    # 1. Stock thứ 7 tuần B
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM StockHomNay
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                        AND [Ngày stock] = ?
                    """, (id_sanpham, ngay_t7_B))
                    stock_t7_B = cursor.fetchone()[0]
                    
                    # 2. Batching tuần B
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng thực tế]), 0)
                        FROM Mixer
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                        AND [Ngày trộn] >= ? AND [Ngày trộn] <= ?
                    """, (id_sanpham, ngay_t7_B, ngay_t6_B))
                    batching_B = cursor.fetchone()[0]
                    
                    # 3. Forecast tuần B
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM DatHang
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                        AND [Loại đặt hàng] = 'Forecast hàng tuần'
                        AND [Ngày đặt] >= ? AND [Ngày đặt] <= ?
                    """, (id_sanpham, ngay_t7_B, ngay_t6_B))
                    forecast_B = cursor.fetchone()[0]
                    
                    # 4. KVL tuần B
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM DatHang
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                        AND [Loại đặt hàng] = 'Khách vãng lai'
                        AND [Ngày lấy] >= ? AND [Ngày lấy] <= ?
                    """, (id_sanpham, ngay_t7_B, ngay_t6_B))
                    kvl_B = cursor.fetchone()[0]
                    
                    # Tính Ghi chú 2 B
                    ghi_chu_2_B = stock_t7_B + batching_B - (forecast_B + kvl_B)
                    ghi_chu_2_text_B = f"T7({stock_t7_B:,.0f})+Bat({batching_B:,.0f})-FC({forecast_B:,.0f})-KVL({kvl_B:,.0f})={ghi_chu_2_B:,.0f}"
                    
                    # === TÍNH GHI CHÚ 2 - TUẦN A (tuần trước) - chỉ khi là thứ 7 ===
                    ghi_chu_2_A = 0
                    ghi_chu_2_text_A = ""
                    
                    if is_saturday:
                        # 1. Stock thứ 7 tuần A
                        cursor.execute("""
                            SELECT COALESCE(SUM([Số lượng]), 0)
                            FROM StockHomNay
                            WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                            AND [Ngày stock] = ?
                        """, (id_sanpham, ngay_t7_A))
                        stock_t7_A = cursor.fetchone()[0]
                        
                        # 2. Batching tuần A
                        cursor.execute("""
                            SELECT COALESCE(SUM([Số lượng thực tế]), 0)
                            FROM Mixer
                            WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                            AND [Ngày trộn] >= ? AND [Ngày trộn] <= ?
                        """, (id_sanpham, ngay_t7_A, ngay_t6_A))
                        batching_A = cursor.fetchone()[0]
                        
                        # 3. Forecast tuần A
                        cursor.execute("""
                            SELECT COALESCE(SUM([Số lượng]), 0)
                            FROM DatHang
                            WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                            AND [Loại đặt hàng] = 'Forecast hàng tuần'
                            AND [Ngày đặt] >= ? AND [Ngày đặt] <= ?
                        """, (id_sanpham, ngay_t7_A, ngay_t6_A))
                        forecast_A = cursor.fetchone()[0]
                        
                        # 4. KVL tuần A
                        cursor.execute("""
                            SELECT COALESCE(SUM([Số lượng]), 0)
                            FROM DatHang
                            WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                            AND [Loại đặt hàng] = 'Khách vãng lai'
                            AND [Ngày lấy] >= ? AND [Ngày lấy] <= ?
                        """, (id_sanpham, ngay_t7_A, ngay_t6_A))
                        kvl_A = cursor.fetchone()[0]
                        
                        # Tính Ghi chú 2 A
                        ghi_chu_2_A = stock_t7_A + batching_A - (forecast_A + kvl_A)
                        ghi_chu_2_text_A = f"T7({stock_t7_A:,.0f})+Bat({batching_A:,.0f})-FC({forecast_A:,.0f})-KVL({kvl_A:,.0f})={ghi_chu_2_A:,.0f}"
                    
                    # Chỉ lưu sản phẩm có số lượng > 0
                    if stock_hom_nay > 0:
                        results.append({
                            'id_sanpham': id_sanpham,
                            'code_cam': code_cam,
                            'ten_cam': ten_cam,
                            'stock_old': stock_old,
                            'packing': packing,
                            'sale': sale,
                            'stock_hom_nay': stock_hom_nay,
                            'ghi_chu_2': ghi_chu_2_text_B,  # Giữ tương thích với cột cũ
                            'ketqua_gc2': ghi_chu_2_B,
                            'ghi_chu_2_A': ghi_chu_2_text_A,
                            'ketqua_gc2_A': ghi_chu_2_A,
                            'ghi_chu_2_B': ghi_chu_2_text_B,
                            'ketqua_gc2_B': ghi_chu_2_B
                        })
                    
                    # Update progress
                    progress = (idx + 1) / len(all_products)
                    progress_bar.progress(progress)
                    status_text.text(f"Đang tính toán: {idx + 1}/{len(all_products)}")
                
                progress_bar.empty()
                status_text.empty()
                conn.close()
                
                # Lưu vào session state
                st.session_state.calculation_results = {
                    'results': results,
                    'ngay_tinh': ngay_tinh
                }
                
                st.success(f"✅ Tính toán hoàn tất: {len(results)} sản phẩm có tồn kho > 0")
                st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())
        
        # Hiển thị kết quả nếu đã tính toán
        if st.session_state.calculation_results is not None:
            results = st.session_state.calculation_results['results']
            ngay_tinh_saved = st.session_state.calculation_results['ngay_tinh']
            
            st.success(f"✅ Có {len(results)} sản phẩm sẵn sàng để lưu")
            
            # Hiển thị bảng kết quả
            with st.expander(f"👁️ Xem chi tiết ({len(results)} sản phẩm)", expanded=True):
                df_result = pd.DataFrame(results)
                df_result.rename(columns={
                    'code_cam': 'Code cám',
                    'ten_cam': 'Tên cám',
                    'stock_old': 'Stock Old',
                    'packing': 'Packing',
                    'sale': 'Sale',
                    'stock_hom_nay': 'Stock đầu ngày',
                    'ghi_chu_2': 'Ghi chú 2',
                    'ghi_chu_2_A': 'GC2-A (tuần trước)',
                    'ghi_chu_2_B': 'GC2-B (tuần hiện tại)',
                    'ketqua_gc2_A': 'KQ-A',
                    'ketqua_gc2_B': 'KQ-B'
                }, inplace=True)
                
                # Chọn cột hiển thị - thêm A và B nếu là thứ 7
                display_columns = ['Code cám', 'Tên cám', 'Stock Old', 'Packing', 'Sale', 'Stock đầu ngày', 'Ghi chú 2']
                if 'GC2-A (tuần trước)' in df_result.columns and df_result['GC2-A (tuần trước)'].notna().any():
                    display_columns.extend(['GC2-A (tuần trước)', 'GC2-B (tuần hiện tại)'])
                
                st.dataframe(
                    df_result[display_columns],
                    width='stretch',
                    hide_index=True
                )
            
            # Xác nhận lưu
            st.warning(f"⚠️ Hành động này sẽ xóa dữ liệu Stock đầu ngày của ngày **{ngay_tinh_saved.strftime('%d/%m/%Y')}** và lưu dữ liệu mới!")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Xác nhận Lưu", type="primary", width="stretch"):
                    import sqlite3
                    from datetime import datetime
                    
                    conn = ss.connect_db()
                    cursor = conn.cursor()
                    
                    # Chỉ xóa dữ liệu của ngày đang tính toán (không xóa các ngày khác)
                    ngay_stock = ngay_tinh_saved.strftime('%Y-%m-%d')
                    cursor.execute("""
                        UPDATE StockHomNay
                        SET [Đã xóa] = 1
                        WHERE [Đã xóa] = 0 AND [Ngày stock] = ?
                    """, (ngay_stock,))
                    
                    # Tạo mã Stock mới
                    cursor.execute("""
                        SELECT MAX([Mã stock]) 
                        FROM StockHomNay 
                        WHERE [Mã stock] LIKE 'ST%'
                    """)
                    result = cursor.fetchone()[0]
                    if result:
                        last_num = int(result[2:])
                        next_num = last_num + 1
                    else:
                        next_num = 1
                    ma_stock = f"ST{next_num:05d}"
                    
                    # ngay_stock đã được định nghĩa ở trên
                    thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Insert dữ liệu mới (bao gồm cả cột A và B)
                    for item in results:
                        cursor.execute("""
                            INSERT INTO StockHomNay
                            ([ID sản phẩm], [Mã stock], [Số lượng], [Ngày stock],
                             [Ghi chú], [Ghi chú 2], [Kết quả GC2], 
                             [Ghi chú 2 A], [Kết quả GC2 A], [Ghi chú 2 B], [Kết quả GC2 B],
                             [Người tạo], [Thời gian tạo], [Đã xóa])
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """, (
                            item['id_sanpham'],
                            ma_stock,
                            item['stock_hom_nay'],
                            ngay_stock,
                            f"SO({item['stock_old']}) + Pk({item['packing']}) - Sale({item['sale']})",
                            item.get('ghi_chu_2', ''),
                            item.get('ketqua_gc2', 0),
                            item.get('ghi_chu_2_A', ''),
                            item.get('ketqua_gc2_A', 0),
                            item.get('ghi_chu_2_B', ''),
                            item.get('ketqua_gc2_B', 0),
                            st.session_state.username,
                            thoi_gian_tao
                        ))
                    
                    conn.commit()
                    conn.close()
                    
                    # Xóa session state
                    st.session_state.calculation_results = None
                    
                    st.success(f"🎉 Đã lưu {len(results)} sản phẩm vào Stock đầu ngày với mã: **{ma_stock}**")
                    st.balloons()
                    st.rerun()
            
            with col_btn2:
                if st.button("❌ Hủy", width="stretch"):
                    st.session_state.calculation_results = None
                    st.rerun()
    
    with tab2:
        st.header("1. Stock đầu ngày")
        # Code cám	Tên cám	Kích cỡ ép viên	Dạng ép viên	Kích cỡ đóng bao	Pellet	Packing	Batch size
        
        ds_sanpham = ss.get_columns_data(table_name='SanPham',
                                         columns=['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên', 'ID'],
                                         data_type='list',
                                         col_where={'Đã xóa':('=',0)})
                                         
        
        data = {
            'ID sản phẩm': [None],
            'Số lượng': [0],
            'Ngày stock': [None],
            'Ghi chú': [None]
        }
        
        df = pd.DataFrame(data)
        
        column_config={
            'ID sản phẩm': st.column_config.SelectboxColumn('ID sản phẩm',options=ds_sanpham,format_func=lambda x: x,width='large'),
            'Số lượng': st.column_config.NumberColumn('Số lượng',min_value=0,step=1,format="%d",width='small'),
            'Ngày stock': st.column_config.DateColumn('Ngày stock', format='DD/MM/YYYY',width='medium'),
            'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
        }
        
        df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config)
        
        # Chỉ lấy các dòng có Sản phẩm khác None và Số lượng > 0
        df_insert = df_insert.dropna(subset=['ID sản phẩm'])
        df_insert = df_insert[df_insert['Số lượng'] > 0]
        
        
        mastock = ss.generate_next_code(tablename='StockHomNay', column_name='Mã stock', prefix='ST',num_char=5)
        st.write(f'Mã stock tự động: **{mastock}**')
        
        df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)

        df_insert['Mã stock'] = mastock
        df_insert['Ngày stock'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_insert['Người tạo'] = st.session_state.username
        df_insert['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.dataframe(df_insert, width='content')
        
        disabled = not (len(df_insert) > 0)
        
        if st.button("Thêm sản phẩm", disabled=disabled, type="primary"):
            result = ss.insert_data_to_sql_server(table_name='StockHomNay',dataframe=df_insert)
            show_notification("Lỗi:", result)
    
    
    st.header("2. Danh sách stock đầu ngày hiện tại")
    
    # Lấy danh sách các ngày đã có stock trong tháng
    import sqlite3
    from datetime import datetime
    import calendar
    
    current_date = fn.get_vietnam_time().date()
    
    # Khởi tạo session state cho tháng/năm được chọn
    if 'view_stock_year' not in st.session_state:
        st.session_state.view_stock_year = current_date.year
    if 'view_stock_month' not in st.session_state:
        st.session_state.view_stock_month = current_date.month
    
    # Dropdown chọn tháng/năm
    col_month, col_year, col_today = st.columns([1, 1, 1])
    
    with col_month:
        months = list(range(1, 13))
        month_names = [f"Tháng {m}" for m in months]
        selected_month_idx = st.selectbox(
            "📅 Chọn tháng",
            range(len(months)),
            index=st.session_state.view_stock_month - 1,
            format_func=lambda x: month_names[x],
            key="month_selector"
        )
        if months[selected_month_idx] != st.session_state.view_stock_month:
            st.session_state.view_stock_month = months[selected_month_idx]
            st.session_state.selected_stock_day = None
            st.rerun()
    
    with col_year:
        years = list(range(2024, current_date.year + 1))
        selected_year = st.selectbox(
            "📆 Chọn năm",
            years,
            index=years.index(st.session_state.view_stock_year) if st.session_state.view_stock_year in years else len(years) - 1,
            key="year_selector"
        )
        if selected_year != st.session_state.view_stock_year:
            st.session_state.view_stock_year = selected_year
            st.session_state.selected_stock_day = None
            st.rerun()
    
    with col_today:
        st.write("")  # Spacing
        if st.button("📍 Về tháng hiện tại", width="stretch"):
            st.session_state.view_stock_year = current_date.year
            st.session_state.view_stock_month = current_date.month
            st.session_state.selected_stock_day = None
            st.rerun()
    
    # Sử dụng tháng/năm đã chọn
    current_year = st.session_state.view_stock_year
    current_month = st.session_state.view_stock_month
    days_in_month = calendar.monthrange(current_year, current_month)[1]
    
    # Query các ngày đã có stock
    conn = ss.connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT strftime('%d', [Ngày stock]) as day
        FROM StockHomNay
        WHERE [Đã xóa] = 0 
        AND strftime('%Y', [Ngày stock]) = ?
        AND strftime('%m', [Ngày stock]) = ?
    """, (str(current_year), str(current_month).zfill(2)))
    days_with_stock = set(int(row[0]) for row in cursor.fetchall())
    conn.close()
    
    # Khởi tạo session state cho ngày được chọn
    if 'selected_stock_day' not in st.session_state:
        st.session_state.selected_stock_day = None
    
    # Hiển thị tiêu đề tháng
    st.markdown(f"**📅 Tháng {current_month}/{current_year}** - 🟢 Đã có stock | 🟡 Chưa có stock")
    
    # CSS cho các nút ngày
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div > div > button {
        min-height: 35px !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Tạo các nút ngày sử dụng Streamlit buttons
    # Chia thành các hàng, mỗi hàng 16 nút
    cols_per_row = 16
    for row_start in range(1, days_in_month + 1, cols_per_row):
        row_end = min(row_start + cols_per_row, days_in_month + 1)
        cols = st.columns(cols_per_row)
        
        for i, day in enumerate(range(row_start, row_end)):
            with cols[i]:
                # Xác định màu nút
                if day in days_with_stock:
                    btn_type = "primary"  # Xanh
                else:
                    btn_type = "secondary"  # Vàng/Xám
                
                # Kiểm tra nếu ngày đang được chọn
                is_selected = st.session_state.selected_stock_day == day
                
                if st.button(
                    f"{'✓ ' if is_selected else ''}{day}", 
                    key=f"day_btn_{day}",
                    type=btn_type if day in days_with_stock else "secondary",
                    width="stretch"
                ):
                    if st.session_state.selected_stock_day == day:
                        st.session_state.selected_stock_day = None  # Bỏ chọn nếu nhấn lại
                    else:
                        st.session_state.selected_stock_day = day
                        # Mặc định hiển thị All khi chọn ngày
                        st.session_state.page_size = 'All'
                    st.rerun()
    
    # Hiển thị thông tin ngày đang lọc
    if st.session_state.selected_stock_day:
        selected_date = f"{current_year}-{current_month:02d}-{st.session_state.selected_stock_day:02d}"
        col_info, col_clear = st.columns([4, 1])
        with col_info:
            st.info(f"📆 Đang hiển thị stock đầu ngày: **{st.session_state.selected_stock_day:02d}/{current_month:02d}/{current_year}**")
        with col_clear:
            if st.button("❌ Xóa bộ lọc", width="stretch"):
                st.session_state.selected_stock_day = None
                st.session_state.selected_animal_filter = None
                st.rerun()
        
        # === CẢNH BÁO KVL MỚI ===
        # Kiểm tra xem có đơn KVL nào cho ngày hôm nay không
        import sqlite3
        conn_kvl = ss.connect_db()
        cursor_kvl = conn_kvl.cursor()
        today_str = fn.get_vietnam_time().strftime('%Y-%m-%d')
        cursor_kvl.execute("""
            SELECT COUNT(*), COALESCE(SUM([Số lượng]), 0)
            FROM DatHang
            WHERE [Đã xóa] = 0 
            AND [Loại đặt hàng] = 'Khách vãng lai'
            AND [Ngày lấy] = ?
        """, (today_str,))
        kvl_count, kvl_total = cursor_kvl.fetchone()
        conn_kvl.close()
        
        if kvl_count and kvl_count > 0:
            st.warning(f"⚠️ **Có {kvl_count} đơn Khách vãng lai** cần lấy hôm nay (tổng: **{kvl_total:,.0f} kg**). "
                      f"Bấm **'Gửi tất cả Plan > 0'** bên dưới để cập nhật Plan!")
        
        # Lọc theo ngày được chọn
        col_where = {'Đã xóa': ('=', 0), 'Ngày stock': ('=', selected_date)}
    else:
        col_where = {'Đã xóa': ('=', 0)}
    
    # Khởi tạo session state cho bộ lọc vật nuôi
    if 'selected_animal_filter' not in st.session_state:
        st.session_state.selected_animal_filter = None
    
    # Mapping giữa tên hiển thị và giá trị trong database
    animal_mapping = {
        'TẤT CẢ': None,
        'HEO': 'H',
        'GÀ': 'G', 
        'BÒ': 'B',
        'VỊT': 'V',
        'CÚT': 'C',
        'DÊ': 'D'
    }
    
    # Tạo các nút lọc theo vật nuôi
    st.markdown("**🐾 Lọc theo vật nuôi:**")
    animal_types = ['TẤT CẢ', 'HEO', 'GÀ', 'BÒ', 'VỊT', 'CÚT', 'DÊ']
    animal_cols = st.columns(len(animal_types))
    
    for idx, animal in enumerate(animal_types):
        with animal_cols[idx]:
            is_selected = (animal == 'TẤT CẢ' and st.session_state.selected_animal_filter is None) or \
                          (st.session_state.selected_animal_filter == animal_mapping.get(animal))
            btn_label = f"{'✓ ' if is_selected else ''}{animal}"
            
            if st.button(btn_label, key=f"animal_btn_{animal}", width="stretch",
                        type="primary" if is_selected else "secondary"):
                if animal == 'TẤT CẢ':
                    st.session_state.selected_animal_filter = None
                else:
                    st.session_state.selected_animal_filter = animal_mapping.get(animal)
                st.rerun()
    
    # === NÚT ẨN/HIỆN CỘT ===
    # Danh sách cột tương ứng với nút toggle
    column_toggle_list = [
        ('Select', 'Sel'),
        ('ID', 'ID'),
        ('ID sản phẩm', 'SP'),
        ('Số lượng', 'SL'),
        ('Ghi chú', 'GC'),
        ('Ghi chú 2', 'GC2'),
        ('Kết quả GC2', 'KQ'),
        ('Ghi chú 2 A', 'A'),
        ('Kết quả GC2 A', 'KQA'),
        ('Ghi chú 2 B', 'B'),
        ('Kết quả GC2 B', 'KQB'),
        ('Aver', 'Aver'),
        ('DOH', 'DOH'),
        ('Ngày stock', 'Date'),
        ('Plan', 'Plan'),
        ('Day5', 'Day5'),
        ('Người tạo', 'Per'),
        ('Vật nuôi', 'Pet')
    ]
    
    # Khởi tạo session state cho trạng thái hiển thị cột
    # Mặc định ẩn một số cột
    if 'column_visibility' not in st.session_state:
        default_hidden = ['Ngày stock', 'Người tạo', 'Ghi chú 2 A', 'Kết quả GC2 A', 'Ghi chú 2 B', 'Kết quả GC2 B']
        st.session_state.column_visibility = {
            col[0]: (col[0] not in default_hidden) for col in column_toggle_list
        }
    
    # CSS để đổi màu nút primary thành cam
    st.markdown("""
    <style>
    /* Đổi màu nút primary thành cam */
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #FF8C00 !important;
        border-color: #FF8C00 !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="primary"]:hover {
        background-color: #FF7000 !important;
        border-color: #FF7000 !important;
    }
    /* Nút secondary giữ màu xanh */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background-color: #4A90D9 !important;
        border-color: #4A90D9 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hiển thị các nút toggle
    st.markdown("**🔧 Ẩn/Hiện cột:** (🟠 Hiện | 🔵 Ẩn)")
    toggle_cols = st.columns(len(column_toggle_list))
    
    for idx, (col_name, btn_label) in enumerate(column_toggle_list):
        with toggle_cols[idx]:
            is_visible = st.session_state.column_visibility.get(col_name, True)
            btn_type = "primary" if is_visible else "secondary"  # primary = cam, secondary = xanh
            
            if st.button(
                btn_label,
                key=f"toggle_col_{col_name}",
                type=btn_type,
                use_container_width=True
            ):
                # Toggle trạng thái
                st.session_state.column_visibility[col_name] = not is_visible
                st.rerun()
    
    column_config = {
        'Ngày stock': st.column_config.TextColumn('Ngày stock', width='small'),
        'Thời gian tạo': st.column_config.TextColumn('Thời gian tạo'),
        'Kết quả GC2': st.column_config.NumberColumn('KQ', format='%d'),
        'Số lượng': st.column_config.NumberColumn('Số lượng', format='%d'),
        'Người tạo': st.column_config.TextColumn('Person', width='small'),
        'Vật nuôi': st.column_config.TextColumn('Pet', width='small'),
        'Aver': st.column_config.NumberColumn('Aver', format='%d', width='small'),
        'DOH': st.column_config.NumberColumn('DOH', format='%.1f', width='small'),
        'Plan': st.column_config.NumberColumn('Plan', format='%d', width='small'),
        'Day5': st.column_config.NumberColumn('Day5', format='%d', width='small'),
        'Ghi chú 2 A': st.column_config.TextColumn('GC2-A', width='large'),
        'Kết quả GC2 A': st.column_config.NumberColumn('KQ-A', format='%d'),
        'Ghi chú 2 B': st.column_config.TextColumn('GC2-B', width='large'),
        'Kết quả GC2 B': st.column_config.NumberColumn('KQ-B', format='%d')
    }
    
    # Tạo joins với điều kiện lọc theo vật nuôi
    joins_config = [
        {
            'table': 'SanPham',
            'on': {'ID sản phẩm': 'ID'},
            'columns': ['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên', 'Vật nuôi'],
            'replace_multi':{'ID sản phẩm':['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên']}
        }
    ]
    
    # Nếu có lọc theo vật nuôi, thêm vào col_where với prefix bảng
    if st.session_state.selected_animal_filter:
        col_where['SanPham.[Vật nuôi]'] = ('=', st.session_state.selected_animal_filter)
    
    # Hàm xử lý để format số nguyên, đổi tên cột và tính Aver, DOH, Plan, Day5
    def format_numeric_columns(df):
        if 'Kết quả GC2' in df.columns:
            df['Kết quả GC2'] = df['Kết quả GC2'].apply(lambda x: int(x) if pd.notna(x) else 0)
        if 'Số lượng' in df.columns:
            df['Số lượng'] = df['Số lượng'].apply(lambda x: int(x) if pd.notna(x) else 0)
        # Đổi tên cột Vật nuôi cho gọn
        if 'SanPham_Vật nuôi' in df.columns:
            df = df.rename(columns={'SanPham_Vật nuôi': 'Vật nuôi'})
        
        # Tính Aver, DOH, Plan, Day5
        if 'ID sản phẩm' in df.columns and 'Số lượng' in df.columns:
            import sqlite3
            from datetime import datetime, timedelta
            
            conn = ss.connect_db()
            cursor = conn.cursor()
            
            # Lấy danh sách ID sản phẩm từ dataframe
            # ID có thể là số hoặc chuỗi dạng "34 | 114001B | 511B | 2.5", cần extract ID số
            raw_product_ids = df['ID sản phẩm'].unique().tolist()
            product_ids = []
            for pid in raw_product_ids:
                if pd.isna(pid):
                    continue
                # Nếu là chuỗi có chứa "|", lấy phần đầu tiên là ID
                if isinstance(pid, str) and '|' in pid:
                    try:
                        product_ids.append(int(pid.split('|')[0].strip()))
                    except:
                        pass
                else:
                    try:
                        product_ids.append(int(pid))
                    except:
                        pass
            
            # Query tổng sản lượng bán, số ngày bán, batch size, và packing 5 ngày cho từng sản phẩm
            aver_dict = {}
            batch_size_dict = {}
            day5_dict = {}
            
            # Tính ngày hiện tại và ngày 5 ngày trước
            today = fn.get_vietnam_time().date()
            date_5_days_ago = today - timedelta(days=5)
            
            for pid in product_ids:
                # Query Aver (tổng bán / số ngày bán)
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM([Số lượng]), 0) as total_sale,
                        COUNT(DISTINCT [Ngày sale]) as num_days
                    FROM Sale
                    WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                """, (pid,))
                result = cursor.fetchone()
                total_sale = result[0] if result[0] else 0
                num_days = result[1] if result[1] else 0
                aver = total_sale / num_days if num_days > 0 else 0
                aver_dict[pid] = aver
                
                # Query Batch size từ SanPham
                cursor.execute("""
                    SELECT [Batch size] FROM SanPham WHERE ID = ?
                """, (pid,))
                bs_result = cursor.fetchone()
                batch_size = bs_result[0] if bs_result and bs_result[0] else 2800  # Mặc định 2800 nếu không có
                batch_size_dict[pid] = batch_size
                
                # Query Day5: Tổng packing trong 5 ngày gần nhất
                cursor.execute("""
                    SELECT COALESCE(SUM([Số lượng]), 0)
                    FROM Packing
                    WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                    AND [Ngày packing] >= ?
                """, (pid, date_5_days_ago.strftime('%Y-%m-%d')))
                day5_result = cursor.fetchone()
                day5_dict[pid] = day5_result[0] if day5_result and day5_result[0] else 0
            
            conn.close()
            
            # Hàm để lấy giá trị từ ID sản phẩm (có thể là chuỗi hoặc số)
            def extract_pid(id_sanpham):
                if pd.isna(id_sanpham):
                    return None
                if isinstance(id_sanpham, str) and '|' in id_sanpham:
                    try:
                        return int(id_sanpham.split('|')[0].strip())
                    except:
                        return None
                else:
                    try:
                        return int(id_sanpham)
                    except:
                        return None
            
            def get_aver(id_sanpham):
                pid = extract_pid(id_sanpham)
                return aver_dict.get(pid, 0) if pid else 0
            
            def get_batch_size(id_sanpham):
                pid = extract_pid(id_sanpham)
                return batch_size_dict.get(pid, 2800) if pid else 2800
            
            def get_day5(id_sanpham):
                pid = extract_pid(id_sanpham)
                return day5_dict.get(pid, 0) if pid else 0
            
            # Thêm cột Aver
            df['Aver'] = df['ID sản phẩm'].apply(get_aver).astype(int)
            
            # Tính DOH = Số lượng stock / Aver (làm tròn 1 chữ số thập phân)
            df['DOH'] = df.apply(
                lambda row: round(row['Số lượng'] / row['Aver'], 1) if row['Aver'] > 0 else 0.0,
                axis=1
            )
            
            # Tính Plan = min(Aver * 3, |Kết quả GC2|), làm tròn lên theo batch size
            # Điều kiện: DOH < 3 và KQ < 0 thì mới tính Plan
            def calculate_plan(row):
                aver = row['Aver']
                kq = row.get('Kết quả GC2', 0)
                doh = row.get('DOH', 0)
                batch_size = get_batch_size(row['ID sản phẩm'])
                
                # Nếu DOH >= 3, không cần sản xuất
                if doh >= 3:
                    return 0
                
                # Nếu KQ >= 0, không cần sản xuất
                if kq >= 0:
                    return 0
                
                # Plan = min(Aver * 3, |KQ|)
                plan_raw = min(aver * 3, abs(kq))
                
                if plan_raw <= 0 or batch_size <= 0:
                    return 0
                
                # Làm tròn lên theo batch size
                import math
                plan_rounded = math.ceil(plan_raw / batch_size) * batch_size
                return int(plan_rounded)
            
            # Chỉ tính Plan và Day5 nếu DataFrame không rỗng
            if len(df) > 0:
                df['Plan'] = df.apply(calculate_plan, axis=1, result_type='reduce')
                
                # Tính Day5 = min(stock tồn, tổng packing 5 ngày)
                # Nếu packing 5 ngày >= stock tồn: Day5 = stock tồn (100% hàng mới)
                # Nếu packing 5 ngày < stock tồn: Day5 = tổng packing (chỉ phần hàng mới)
                def calculate_day5(row):
                    stock = row['Số lượng']
                    packing_5days = get_day5(row['ID sản phẩm'])
                    return min(stock, packing_5days)
                
                df['Day5'] = df.apply(calculate_day5, axis=1, result_type='reduce').astype(int)
            else:
                df['Plan'] = []
                df['Day5'] = []
        
        # Sắp xếp theo thứ tự Vật nuôi: H → G → V → B → C → D
        if 'Vật nuôi' in df.columns:
            pet_order = {'H': 1, 'G': 2, 'V': 3, 'B': 4, 'C': 5, 'D': 6}
            df['_pet_order'] = df['Vật nuôi'].map(pet_order).fillna(99)
            df = df.sort_values(['_pet_order', 'Kết quả GC2'] if 'Kết quả GC2' in df.columns else ['_pet_order'])
            df = df.drop(columns=['_pet_order'])
        
        return df
    
    # Tạo danh sách output_columns dựa trên trạng thái visibility
    all_output_columns = ['ID', 'ID sản phẩm', 'Số lượng', 'Ghi chú', 'Ghi chú 2', 'Kết quả GC2', 
                          'Ghi chú 2 A', 'Kết quả GC2 A', 'Ghi chú 2 B', 'Kết quả GC2 B',
                          'Aver', 'DOH', 'Ngày stock', 'Plan', 'Day5', 'Người tạo', 'Vật nuôi']
    
    # Lọc các cột được hiển thị (trừ Select vì nó được xử lý riêng trong dataframe_with_selections)
    visible_columns = [col for col in all_output_columns if st.session_state.column_visibility.get(col, True)]
    
    # Kiểm tra xem Select có bị ẩn không
    show_select = st.session_state.column_visibility.get('Select', True)
    
    dataframe_with_selections(
        table_name="StockHomNay",
        columns=[
            'ID sản phẩm', 'Số lượng', 'Ghi chú', 'Ghi chú 2', 'Kết quả GC2', 'Ngày stock', 'ID',
            'Người tạo', 'Ghi chú 2 A', 'Kết quả GC2 A', 'Ghi chú 2 B', 'Kết quả GC2 B'
        ],
        output_columns=visible_columns,
        colums_disable=['ID', 'Người tạo', 'Kết quả GC2', 'Aver', 'DOH', 'Kết quả GC2 A', 'Kết quả GC2 B'],
        col_where=col_where,
        col_order={'Kết quả GC2': 'ASC'},
        joins=joins_config,
        column_config=column_config,
        key=f'StockHomNay_{st.session_state.df_key}_{st.session_state.selected_stock_day}_{st.session_state.selected_animal_filter}',
        join_user_info=False,
        post_process_func=format_numeric_columns,
        return_selected_rows=True,
        add_select=show_select)
    
    # === NÚT GỬI TẤT CẢ PLAN > 0 SANG PLAN (luôn hiện) ===
    st.markdown("---")
    if st.button("📤 Gửi tất cả Plan > 0 sang Plan", type="primary", key="btn_auto_transfer_plan"):
        import sqlite3
        from datetime import datetime, timedelta
        import math
        
        conn = ss.connect_db()
        cursor = conn.cursor()
        
        # Lấy ngày stock hiện tại đang hiển thị
        if st.session_state.selected_stock_day:
            selected_date = f"{fn.get_vietnam_time().year}-{fn.get_vietnam_time().month:02d}-{st.session_state.selected_stock_day:02d}"
        else:
            selected_date = fn.get_vietnam_time().strftime('%Y-%m-%d')
        
        # === 1. LẤY PLAN TỪ STOCK ĐẦU NGÀY (DOH < 3 và KQ < 0) ===
        cursor.execute("""
            SELECT 
                s.[ID sản phẩm], 
                p.[Code cám], 
                p.[Tên cám],
                s.[Số lượng],
                s.[Kết quả GC2],
                p.[Batch size]
            FROM StockHomNay s
            LEFT JOIN SanPham p ON s.[ID sản phẩm] = p.ID
            WHERE s.[Đã xóa] = 0 AND s.[Ngày stock] = ?
        """, (selected_date,))
        
        stock_data = cursor.fetchall()
        
        # Tính Aver cho từng sản phẩm và lọc DOH < 3
        plan_from_stock = {}
        for row in stock_data:
            id_sp, code_cam, ten_cam, stock_qty, kq_gc2, batch_size = row
            if not id_sp or not code_cam:
                continue
            
            # Tính Aver
            cursor.execute("""
                SELECT COALESCE(SUM([Số lượng]), 0), COUNT(DISTINCT [Ngày sale])
                FROM Sale WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
            """, (id_sp,))
            sale_result = cursor.fetchone()
            total_sale = sale_result[0] if sale_result else 0
            num_days = sale_result[1] if sale_result else 0
            aver = total_sale / num_days if num_days > 0 else 0
            
            # Tính DOH
            doh = stock_qty / aver if aver > 0 else 999
            
            # Chỉ lấy sản phẩm có DOH < 3 và KQ < 0
            if doh < 3 and (kq_gc2 or 0) < 0:
                batch_size = batch_size or 2800
                plan_raw = min(aver * 3, abs(kq_gc2))
                if plan_raw > 0 and batch_size > 0:
                    plan_value = int(math.ceil(plan_raw / batch_size) * batch_size)
                    if plan_value > 0:
                        plan_from_stock[id_sp] = {
                            'code_cam': code_cam,
                            'ten_cam': ten_cam,
                            'qty': plan_value,
                            'source': 'Stock đầu ngày'
                        }
        
        # === 2. LẤY ĐẶT HÀNG TỪ ĐẠI LÝ BÁ CANG (ngày N+1) ===
        today = fn.get_vietnam_time().date()
        tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT 
                d.[ID sản phẩm],
                p.[Code cám],
                p.[Tên cám],
                SUM(d.[Số lượng]) as total_qty
            FROM DatHang d
            LEFT JOIN SanPham p ON d.[ID sản phẩm] = p.ID
            WHERE d.[Đã xóa] = 0 
            AND d.[Loại đặt hàng] = 'Đại lý Bá Cang'
            AND d.[Ngày lấy] = ?
            GROUP BY d.[ID sản phẩm]
        """, (tomorrow,))
        
        bacang_data = cursor.fetchall()
        plan_from_bacang = {}
        for row in bacang_data:
            id_sp, code_cam, ten_cam, qty = row
            if id_sp and code_cam and qty > 0:
                plan_from_bacang[id_sp] = {
                    'code_cam': code_cam,
                    'ten_cam': ten_cam,
                    'qty': qty,
                    'source': 'Đại lý Bá Cang'
                }
        
        # === 3. LẤY ĐẶT HÀNG TỪ XE BỒN SILO (ngày N+1) ===
        cursor.execute("""
            SELECT 
                d.[ID sản phẩm],
                p.[Code cám],
                p.[Tên cám],
                SUM(d.[Số lượng]) as total_qty
            FROM DatHang d
            LEFT JOIN SanPham p ON d.[ID sản phẩm] = p.ID
            WHERE d.[Đã xóa] = 0 
            AND d.[Loại đặt hàng] = 'Xe bồn Silo'
            AND d.[Ngày lấy] = ?
            GROUP BY d.[ID sản phẩm]
        """, (tomorrow,))
        
        silo_data = cursor.fetchall()
        plan_from_silo = {}
        for row in silo_data:
            id_sp, code_cam, ten_cam, qty = row
            if id_sp and code_cam and qty > 0:
                plan_from_silo[id_sp] = {
                    'code_cam': code_cam,
                    'ten_cam': ten_cam,
                    'qty': qty,
                    'source': 'Xe bồn Silo'
                }
        
        # === 4. LẤY ĐẶT HÀNG TỪ KHÁCH VÃNG LAI (ngày N - hôm nay) ===
        today_str = today.strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT 
                d.[ID sản phẩm],
                p.[Code cám],
                p.[Tên cám],
                SUM(d.[Số lượng]) as total_qty
            FROM DatHang d
            LEFT JOIN SanPham p ON d.[ID sản phẩm] = p.ID
            WHERE d.[Đã xóa] = 0 
            AND d.[Loại đặt hàng] = 'Khách vãng lai'
            AND d.[Ngày lấy] = ?
            GROUP BY d.[ID sản phẩm]
        """, (today_str,))
        
        kvl_data = cursor.fetchall()
        plan_from_kvl = {}
        for row in kvl_data:
            id_sp, code_cam, ten_cam, qty = row
            if id_sp and code_cam and qty > 0:
                plan_from_kvl[id_sp] = {
                    'code_cam': code_cam,
                    'ten_cam': ten_cam,
                    'qty': qty,
                    'source': 'Khách vãng lai'
                }
        
        conn.close()
        
        # === 5. TỔNG HỢP TẤT CẢ NGUỒN ===
        all_ids = set(plan_from_stock.keys()) | set(plan_from_bacang.keys()) | set(plan_from_silo.keys()) | set(plan_from_kvl.keys())
        
        transfer_data = []
        for id_sp in all_ids:
            stock_item = plan_from_stock.get(id_sp, {})
            bacang_item = plan_from_bacang.get(id_sp, {})
            silo_item = plan_from_silo.get(id_sp, {})
            kvl_item = plan_from_kvl.get(id_sp, {})
            
            # Lấy thông tin sản phẩm từ nguồn có data
            code_cam = stock_item.get('code_cam') or bacang_item.get('code_cam') or silo_item.get('code_cam') or kvl_item.get('code_cam')
            ten_cam = stock_item.get('ten_cam') or bacang_item.get('ten_cam') or silo_item.get('ten_cam') or kvl_item.get('ten_cam')
            
            # Tổng số lượng từ các nguồn
            qty_stock = stock_item.get('qty', 0)
            qty_bacang = bacang_item.get('qty', 0)
            qty_silo = silo_item.get('qty', 0)
            qty_kvl = kvl_item.get('qty', 0)
            total_qty = qty_stock + qty_bacang + qty_silo + qty_kvl
            
            # Ghi chú nguồn
            sources = []
            if qty_stock > 0:
                sources.append(f"Stock:{qty_stock:,.0f}")
            if qty_bacang > 0:
                sources.append(f"BC:{qty_bacang:,.0f}")
            if qty_silo > 0:
                sources.append(f"Silo:{qty_silo:,.0f}")
            if qty_kvl > 0:
                sources.append(f"KVL:{qty_kvl:,.0f}")
            
            if total_qty > 0:
                transfer_data.append({
                    'Code cám': code_cam,
                    'Tên cám': ten_cam,
                    'Số lượng': total_qty,
                    'Ngày plan': selected_date,
                    'Ghi chú': ' + '.join(sources)
                })
        
        if transfer_data:
            st.session_state['plan_transfer_data'] = {
                'data': transfer_data,
                'source': f'Tổng hợp - Stock + Bá Cang + Silo + KVL',
                'ngay_lay': selected_date,
                'sheet': ''
            }
            st.success(f"✅ Đã gửi **{len(transfer_data)}** sản phẩm sang Plan!")
            st.info(f"📊 Nguồn: Stock ({len(plan_from_stock)}), Bá Cang ({len(plan_from_bacang)}), Silo ({len(plan_from_silo)}), KVL ({len(plan_from_kvl)})")
            st.info("👉 Vào **Plan > Nhập kế hoạch thủ công** để xem và lưu.")
        else:
            st.warning("⚠️ Không có sản phẩm nào có Plan > 0!")
    
    # Xử lý sản phẩm đã chọn - hiển thị form nhập số lượng để gửi qua Plan
    selection_key = f"dws_selection_state_StockHomNay_{st.session_state.df_key}_{st.session_state.selected_stock_day}_{st.session_state.selected_animal_filter}"
    
    if selection_key in st.session_state and st.session_state[selection_key]:
        selected_ids = list(st.session_state[selection_key])
        
        if len(selected_ids) > 0:
            st.markdown("---")
            st.subheader("📤 Chuyển sang Plan")
            
            # Lấy thông tin sản phẩm đã chọn + tính Plan
            import sqlite3
            from datetime import timedelta
            
            conn = ss.connect_db()
            cursor = conn.cursor()
            
            plan_data = []
            for stock_id in selected_ids:
                cursor.execute("""
                    SELECT s.ID, s.[ID sản phẩm], s.[Số lượng], p.[Code cám], p.[Tên cám], p.[Batch size],
                           s.[Kết quả GC2]
                    FROM StockHomNay s
                    LEFT JOIN SanPham p ON s.[ID sản phẩm] = p.ID
                    WHERE s.ID = ?
                """, (stock_id,))
                row = cursor.fetchone()
                if row:
                    stock_id_val = row[0]
                    id_sanpham = row[1]
                    stock_qty = row[2] or 0
                    code_cam = row[3] or ''
                    ten_cam = row[4] or ''
                    batch_size = row[5] or 2800
                    kq_gc2 = row[6] or 0  # Lấy trực tiếp từ cột Kết quả GC2
                    
                    # Tính Aver
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0), COUNT(DISTINCT [Ngày sale])
                        FROM Sale WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                    """, (id_sanpham,))
                    sale_result = cursor.fetchone()
                    total_sale = sale_result[0] if sale_result and sale_result[0] else 0
                    num_days = sale_result[1] if sale_result and sale_result[1] else 0
                    aver = total_sale / num_days if num_days > 0 else 0
                    
                    # Tính Plan = min(Aver * 3, |KQ|) làm tròn theo batch size
                    plan_value = 0
                    if kq_gc2 < 0:
                        import math
                        plan_raw = min(aver * 3, abs(kq_gc2))
                        if plan_raw > 0 and batch_size > 0:
                            plan_value = int(math.ceil(plan_raw / batch_size) * batch_size)
                    
                    plan_data.append({
                        'stock_id': stock_id_val,
                        'id_sanpham': id_sanpham,
                        'stock_qty': stock_qty,
                        'code_cam': code_cam,
                        'ten_cam': ten_cam,
                        'plan_value': plan_value
                    })
            conn.close()
            
            if plan_data:
                st.info(f"Đã chọn **{len(plan_data)}** sản phẩm. Nhập số lượng (kg) cần sản xuất:")
                
                # Form nhập số lượng cho từng sản phẩm
                ngay_plan = fn.get_vietnam_time().date()
                
                # Khởi tạo session state cho số lượng nếu chưa có
                if 'stock_to_plan_qty' not in st.session_state:
                    st.session_state.stock_to_plan_qty = {}
                
                # Theo dõi các sản phẩm đã được khởi tạo Plan
                if 'plan_initialized_ids' not in st.session_state:
                    st.session_state.plan_initialized_ids = set()
                
                # Cập nhật giá trị mặc định từ Plan cho sản phẩm mới được chọn
                need_rerun = False
                for item in plan_data:
                    if item['stock_id'] not in st.session_state.plan_initialized_ids:
                        st.session_state.stock_to_plan_qty[item['stock_id']] = item['plan_value']
                        st.session_state.plan_initialized_ids.add(item['stock_id'])
                        need_rerun = True
                
                # Rerun ngay nếu có sản phẩm mới được chọn để hiển thị đúng giá trị
                if need_rerun:
                    st.rerun()
                
                # Hiển thị bảng nhập liệu
                col_header = st.columns([2, 3, 2, 2])
                col_header[0].markdown("**Code cám**")
                col_header[1].markdown("**Tên cám**")
                col_header[2].markdown("**Tồn kho (kg)**")
                col_header[3].markdown("**SL sản xuất (kg)**")
                
                for item in plan_data:
                    col_row = st.columns([2, 3, 2, 2])
                    col_row[0].write(item['code_cam'])
                    col_row[1].write(item['ten_cam'])
                    col_row[2].write(f"{item['stock_qty']:,.0f}")
                    
                    # Input số lượng với giá trị mặc định từ Plan
                    qty_key = f"plan_qty_{item['stock_id']}"
                    default_value = st.session_state.stock_to_plan_qty.get(item['stock_id'], item['plan_value'])
                    qty = col_row[3].number_input(
                        "SL",
                        min_value=0,
                        value=default_value,
                        step=1000,
                        key=qty_key,
                        label_visibility="collapsed"
                    )
                    st.session_state.stock_to_plan_qty[item['stock_id']] = qty
                
                # Nút gửi qua Plan
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📤 Gửi qua Plan", type="primary", key="btn_send_to_plan_stock"):
                        # Chuẩn bị dữ liệu
                        transfer_data = []
                        for item in plan_data:
                            qty = st.session_state.stock_to_plan_qty.get(item['stock_id'], 0)
                            if qty > 0:
                                transfer_data.append({
                                    'Code cám': item['code_cam'],
                                    'Tên cám': item['ten_cam'],
                                    'Số lượng': qty,
                                    'Ngày plan': ngay_plan.strftime('%Y-%m-%d'),
                                    'Ghi chú': ''
                                })
                        
                        if transfer_data:
                            st.session_state['plan_transfer_data'] = {
                                'data': transfer_data,
                                'source': f'Stock đầu ngày - {st.session_state.selected_stock_day}',
                                'ngay_lay': ngay_plan.strftime('%Y-%m-%d'),
                                'sheet': ''
                            }
                            st.success(f"✅ Đã gửi **{len(transfer_data)}** sản phẩm sang Plan!")
                            st.info("👉 Vào **Plan > Nhập kế hoạch thủ công** để xem và lưu.")
                            
                            # Clear selection
                            st.session_state.stock_to_plan_qty = {}
                        else:
                            st.warning("⚠️ Chưa nhập số lượng cho sản phẩm nào!")
                
                with col_btn2:
                    if st.button("❌ Hủy chọn", key="btn_cancel_plan_stock"):
                        st.session_state[selection_key] = set()
                        st.session_state.stock_to_plan_qty = {}
                        st.rerun()

