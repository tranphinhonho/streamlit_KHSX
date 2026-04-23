import streamlit as st
from admin.sys_kde_components import *
import plotly.express as px
import plotly.graph_objects as go
from utils.import_notification import send_import_notification

# Mapping vật nuôi
VAT_NUOI_LABELS = {
    'H': 'HEO', 'G': 'GÀ', 'B': 'BÒ', 
    'V': 'VỊT', 'C': 'CÚT', 'D': 'DÊ'
}

VAT_NUOI_COLORS = {
    'H': '#FF6B6B', 'G': '#4ECDC4', 'B': '#45B7D1',
    'V': '#96CEB4', 'C': '#FFEAA7', 'D': '#DDA0DD'
}

def get_stock_by_vatnuoi(filter_date=None):
    """Lấy tổng tồn kho theo vật nuôi"""
    date_condition = ""
    if filter_date:
        date_condition = f"AND s.[Ngày stock old] = '{filter_date}'"
    
    sql = f"""
        SELECT sp.[Vật nuôi], SUM(s.[Số lượng]) as TongKg
        FROM StockOld s
        LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
        WHERE s.[Đã xóa] = 0 AND sp.[Vật nuôi] IS NOT NULL
        {date_condition}
        GROUP BY sp.[Vật nuôi]
    """
    df = ss.query_database_sqlite(sql_string=sql, data_type='dataframe')
    return df

def get_latest_stock_date():
    """Lấy ngày stock old gần nhất có dữ liệu"""
    sql = """
        SELECT MAX([Ngày stock old]) as NgayMoiNhat
        FROM StockOld
        WHERE [Đã xóa] = 0
    """
    result = ss.query_database_sqlite(sql_string=sql, data_type='list')
    if result and result[0]:
        return result[0]
    return None

def app(selected):
    
    # Lấy ngày gần nhất có dữ liệu
    latest_date = get_latest_stock_date()
    
    # Xác định ngày filter - mặc định là ngày gần nhất
    if 'filter_date' not in st.session_state or not st.session_state.filter_date:
        # Tự động set ngày gần nhất
        if latest_date:
            st.session_state.filter_date = latest_date
    
    filter_date = st.session_state.get('filter_date', latest_date)
    
    # Hiển thị thông báo và biểu đồ trên cùng 1 dòng
    if filter_date:
        # PostgreSQL trả về date object, SQLite trả về string
        if hasattr(filter_date, 'strftime'):
            day = filter_date.day
            month = filter_date.month
            year = filter_date.year
        else:
            parts = str(filter_date).split('-')
            if len(parts) == 3:
                day = int(parts[2])
                month = int(parts[1])
                year = int(parts[0])
            else:
                day, month, year = 1, 1, 2020
        
        col_info, col_table, col_chart = st.columns([1, 1, 2])
        
        with col_info:
            st.info(f"""
            📅 **Ngày: {day:02d}/{month:02d}/{year}**
            
            Dữ liệu lọc theo ngày **{filter_date}**.
            """)
            
            if st.button("🔄 Xóa bộ lọc ngày", key="clear_filter_stockold"):
                st.session_state.filter_date = None
                st.session_state.navigate_to = None
                st.rerun()
        
        # Lấy dữ liệu biểu đồ theo ngày filter
        df_chart = get_stock_by_vatnuoi(filter_date)
        
        with col_table:
            # Bảng tóm tắt
            st.markdown("**📋 Tóm tắt tồn kho:**")
            if df_chart is not None and len(df_chart) > 0:
                df_chart = df_chart.sort_values('TongKg', ascending=False)
                df_chart['Label'] = df_chart['Vật nuôi'].map(VAT_NUOI_LABELS)
                df_chart['Color'] = df_chart['Vật nuôi'].map(VAT_NUOI_COLORS)
                
                # Tạo bảng tóm tắt
                total_kg = df_chart['TongKg'].sum()
                for _, row in df_chart.iterrows():
                    pct = (row['TongKg'] / total_kg * 100) if total_kg > 0 else 0
                    st.markdown(f"**{row['Label']}**: {row['TongKg']:,.0f} kg ({pct:.1f}%)")
                st.markdown("---")
                st.markdown(f"**TỔNG CỘNG: {total_kg:,.0f} kg**")
            else:
                st.warning("Không có dữ liệu")
        
        with col_chart:
            if df_chart is not None and len(df_chart) > 0:
                # Tạo pie chart với số kg - labels bên ngoài
                fig = go.Figure(data=[go.Pie(
                    labels=df_chart['Label'],
                    values=df_chart['TongKg'],
                    textinfo='percent',
                    texttemplate='%{percent:.1%}',
                    textposition='inside',
                    hovertemplate='<b>%{label}</b><br>%{value:,.0f} kg<br>%{percent}<extra></extra>',
                    marker_colors=df_chart['Color'].tolist(),
                    pull=[0.02] * len(df_chart)
                )])
                
                fig.update_layout(
                    title=f"📊 Tồn kho ngày {day:02d}/{month:02d}/{year}",
                    title_x=0.5,
                    height=350,
                    margin=dict(t=50, b=20, l=20, r=20),
                    showlegend=False
                )
                
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning("Không có dữ liệu tồn kho cho ngày này")
    else:
        # Không có filter - hiển thị biểu đồ theo ngày gần nhất
        latest_date = get_latest_stock_date()
        col_title, col_chart = st.columns([1, 2])
        
        with col_title:
            st.markdown("##### 📊 Biểu đồ tồn kho theo Vật nuôi")
            if latest_date:
                # Format ngày dd/mm/yyyy
                parts = str(latest_date).split('-')
                if len(parts) == 3:
                    st.markdown(f"*(Ngày gần nhất: **{parts[2]}/{parts[1]}/{parts[0]}**)*")
                else:
                    st.markdown(f"*(Ngày gần nhất: **{latest_date}**)*")
            else:
                st.markdown("*(Chưa có dữ liệu)*")
        
        with col_chart:
            df_chart = get_stock_by_vatnuoi(latest_date)
            if df_chart is not None and len(df_chart) > 0:
                # Sắp xếp theo số lượng giảm dần
                df_chart = df_chart.sort_values('TongKg', ascending=False)
                df_chart['Label'] = df_chart['Vật nuôi'].map(VAT_NUOI_LABELS)
                df_chart['Color'] = df_chart['Vật nuôi'].map(VAT_NUOI_COLORS)
                
                # Tạo text hiển thị đẹp hơn
                df_chart['DisplayText'] = df_chart.apply(
                    lambda row: f"{row['Label']}<br>{row['TongKg']:,.0f} kg", axis=1
                )
                
                fig = go.Figure(data=[go.Pie(
                    labels=df_chart['Label'],
                    values=df_chart['TongKg'],
                    textinfo='text',
                    text=df_chart['DisplayText'],
                    textposition='inside',  # Hiển thị bên trong
                    insidetextorientation='horizontal',  # Chữ nằm ngang
                    hovertemplate='<b>%{label}</b><br>%{value:,.0f} kg<br>%{percent}<extra></extra>',
                    marker_colors=df_chart['Color'].tolist(),
                    hole=0.3,  # Tạo donut chart dễ đọc hơn
                    pull=[0.02] * len(df_chart)  # Nhấn mạnh các phần
                )])
                
                fig.update_layout(
                    title=dict(
                        text="📊 Tổng tồn kho theo Vật nuôi",
                        x=0.5,
                        font=dict(size=16)
                    ),
                    height=400,
                    margin=dict(t=60, b=60, l=20, r=20),
                    showlegend=True,
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12)
                    ),
                    uniformtext_minsize=10,
                    uniformtext_mode='hide'
                )
                
                st.plotly_chart(fig, width="stretch")
    
    # Expander cho Import Excel (thu gọn)
    with st.expander("📁 Import Excel", expanded=False):
        st.subheader("Import Stock Old từ Excel")
        
        st.markdown("""
        **Yêu cầu file Excel:**
        - Cột A: Code cám
        - Cột F: Tồn kho (Kg)
        - Cột G: Day On Hand
        - Dữ liệu bắt đầu từ hàng 2 (hàng 1 là header)
        """)
        
        uploaded_file = st.file_uploader(
            "Chọn file Excel", 
            type=['xlsx', 'xls'],
            help="Hỗ trợ định dạng .xlsx và .xls"
        )
        
        if uploaded_file is not None:
            try:
                # Đọc file Excel
                df_excel = pd.read_excel(uploaded_file)
                
                st.success(f"✅ Đã tải file: {uploaded_file.name} ({len(df_excel)} dòng)")
                
                # Hiển thị preview
                with st.expander("👁️ Xem trước dữ liệu (10 dòng đầu)"):
                    st.dataframe(df_excel.head(10), width="stretch")
                
                # Mapping columns
                st.subheader("Cấu hình cột dữ liệu")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    col_code_cam = st.selectbox(
                        "Cột Code cám",
                        options=df_excel.columns.tolist(),
                        index=0 if len(df_excel.columns) > 0 else None
                    )
                
                with col2:
                    col_ton_kho = st.selectbox(
                        "Cột Tồn kho (Kg)",
                        options=df_excel.columns.tolist(),
                        index=5 if len(df_excel.columns) > 5 else None
                    )
                
                with col3:
                    col_day_on_hand = st.selectbox(
                        "Cột Day On Hand",
                        options=df_excel.columns.tolist(),
                        index=6 if len(df_excel.columns) > 6 else None
                    )
                
                # Button import
                if st.button("🚀 Import vào Database", type="primary"):
                    import sqlite3
                    from datetime import datetime
                    
                    # Xử lý dữ liệu
                    data_to_import = []
                    for idx, row in df_excel.iterrows():
                        code_cam = row[col_code_cam]
                        ton_kho = row[col_ton_kho]
                        day_on_hand = row[col_day_on_hand]
                        
                        # Bỏ qua dòng trống
                        if pd.isna(code_cam) or pd.isna(ton_kho):
                            continue
                        
                        code_cam = str(code_cam).strip()
                        
                        try:
                            ton_kho = int(float(ton_kho))
                        except:
                            ton_kho = 0
                        
                        try:
                            day_on_hand = float(day_on_hand) if not pd.isna(day_on_hand) else 0
                        except:
                            day_on_hand = 0
                        
                        if ton_kho > 0:
                            data_to_import.append({
                                'code_cam': code_cam,
                                'ton_kho': ton_kho,
                                'day_on_hand': day_on_hand
                            })
                    
                    # Kết nối database
                    conn = ss.connect_db()
                    cursor = conn.cursor()
                    
                    # Tạo mã Stock Old
                    cursor.execute("""
                        SELECT MAX([Mã stock old]) 
                        FROM StockOld 
                        WHERE [Mã stock old] LIKE 'SO%'
                    """)
                    result = cursor.fetchone()[0]
                    if result:
                        last_num = int(result[2:])
                        next_num = last_num + 1
                    else:
                        next_num = 1
                    ma_stock_old = f"SO{next_num:05d}"
                    
                    ngay_stock_old = datetime.now().strftime('%Y-%m-%d')
                    thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Insert dữ liệu
                    success_count = 0
                    not_found = []
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, item in enumerate(data_to_import):
                        # Tìm ID sản phẩm
                        cursor.execute("""
                            SELECT ID 
                            FROM SanPham 
                            WHERE TRIM([Code cám]) = ? AND [Đã xóa] = 0
                        """, (item['code_cam'],))
                        
                        result = cursor.fetchone()
                        
                        if not result:
                            not_found.append(item['code_cam'])
                            continue
                        
                        id_sanpham = result[0]
                        
                        # Insert
                        cursor.execute("""
                            INSERT INTO StockOld 
                            ([ID sản phẩm], [Mã stock old], [Số lượng], [Ngày stock old], 
                             [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa])
                            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                        """, (
                            id_sanpham,
                            ma_stock_old,
                            item['ton_kho'],
                            ngay_stock_old,
                            f"Day On Hand: {item['day_on_hand']:.1f}",
                            st.session_state.username,
                            thoi_gian_tao
                        ))
                        
                        success_count += 1
                        
                        # Update progress
                        progress = (idx + 1) / len(data_to_import)
                        progress_bar.progress(progress)
                        status_text.text(f"Đang import: {idx + 1}/{len(data_to_import)}")
                    
                    conn.commit()
                    conn.close()
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Báo cáo kết quả
                    st.success(f"✅ Import thành công: **{success_count}** sản phẩm")
                    st.info(f"📦 Mã Stock Old: **{ma_stock_old}**")
                    
                    if not_found:
                        with st.expander(f"⚠️ Không tìm thấy: {len(not_found)} sản phẩm"):
                            for code in not_found[:20]:
                                st.text(f"- {code}")
                            if len(not_found) > 20:
                                st.text(f"... và {len(not_found) - 20} mã khác")
                        
                        # Gửi email thông báo
                        email_sent = send_import_notification(
                            not_found_codes=not_found,
                            filename=uploaded_file.name,
                            import_type='STOCK',
                            ngay_import=ngay_stock_old,
                            nguoi_import=st.session_state.username
                        )
                        if email_sent:
                            st.info(f"📧 Đã gửi email thông báo về {len(not_found)} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                    
                    st.balloons()
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())
    
    # Expander cho Nhập thủ công (thu gọn)
    with st.expander("📝 Nhập thủ công", expanded=False):
        st.subheader("Nhập Stock Old thủ công")
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
        
        
        mastockold = ss.generate_next_code(tablename='StockOld', column_name='Mã stock old', prefix='SO',num_char=5)
        st.write(f'Mã stock old tự động: **{mastockold}**')
        
        df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)

        df_insert['Mã stock old'] = mastockold
        df_insert['Ngày stock old'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_insert['Người tạo'] = st.session_state.username
        df_insert['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.dataframe(df_insert, width='content')
        
        disabled = not (len(df_insert) > 0)
        
        if st.button("Thêm sản phẩm", disabled=disabled, type="primary"):
            result = ss.insert_data_to_sql_server(table_name='StockOld',dataframe=df_insert)
            show_notification("Lỗi:", result)
    
    
    st.header("2. Danh sách stock old hiện tại")
    
    # Khởi tạo session state cho filter vật nuôi
    if 'filter_vatnuoi_stockold' not in st.session_state:
        st.session_state.filter_vatnuoi_stockold = None
    
    # Tạo các nút lọc theo vật nuôi
    filter_cols = st.columns(7)
    with filter_cols[0]:
        btn_style = "primary" if st.session_state.filter_vatnuoi_stockold is None else "secondary"
        if st.button("📦 Tất cả", width="stretch", type=btn_style, key="stockold_filter_all"):
            st.session_state.filter_vatnuoi_stockold = None
            st.rerun()
    
    for idx, (code, label) in enumerate(VAT_NUOI_LABELS.items()):
        with filter_cols[idx + 1]:
            btn_style = "primary" if st.session_state.filter_vatnuoi_stockold == code else "secondary"
            if st.button(label, width="stretch", type=btn_style, key=f"stockold_filter_{code}"):
                st.session_state.filter_vatnuoi_stockold = code
                st.rerun()
    
    # Filter theo ngày
    col_date, col_search = st.columns([1, 3])
    with col_date:
        # Lấy ngày mặc định từ filter_date nếu có
        default_date = None
        if filter_date:
            parts = filter_date.split('-')
            if len(parts) == 3:
                from datetime import date as dt_date
                default_date = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
        
        selected_date = st.date_input(
            "Lọc theo ngày",
            value=default_date,
            format="YYYY/MM/DD",
            key="stockold_date_filter"
        )
        
        # Kiểm tra nếu ngày thay đổi
        new_date_str = selected_date.strftime('%Y-%m-%d') if selected_date else None
        current_filter = st.session_state.get('filter_date')
        
        if new_date_str != current_filter:
            st.session_state.filter_date = new_date_str
            st.session_state.page_size = 'All'
            st.session_state.df_key += 1  # Buộc refresh dataframe
            st.rerun()
    
    # Xây dựng điều kiện lọc
    col_where = {'Đã xóa': ('=', 0)}
    
    # Nếu có filter_date từ Lịch tháng, thêm điều kiện lọc theo ngày
    if 'filter_date' in st.session_state and st.session_state.filter_date:
        col_where['Ngày stock old'] = ('=', st.session_state.filter_date)
    
    # Thêm điều kiện lọc theo vật nuôi nếu có
    if st.session_state.filter_vatnuoi_stockold:
        col_where['SanPham.Vật nuôi'] = ('=', st.session_state.filter_vatnuoi_stockold)
    
    # Xây dựng joins
    join_config = {
        'table': 'SanPham',
        'on': {'ID sản phẩm': 'ID'},
        'columns': ['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên'],
        'replace_multi':{'ID sản phẩm':['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên']}
    }
    
    dataframe_with_selections(
        table_name="StockOld",
        columns=[
            'ID', 'ID sản phẩm', 'Mã stock old', 'Số lượng', 'Ngày lấy', 'Khách vãng lai', 'Ghi chú',
            'Người tạo', 'Thời gian tạo'
        ],
        colums_disable=['ID','Mã stock old','Người tạo','Thời gian tạo'],
        col_where=col_where,
        col_order={'ID': 'DESC'},
        joins = [join_config],
        # column_config=column_config,
        key=f'StockOld_{st.session_state.df_key}',
        join_user_info=False)

