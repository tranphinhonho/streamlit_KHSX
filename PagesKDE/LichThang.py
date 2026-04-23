import streamlit as st
from admin.sys_kde_components import *
import admin.sys_sqlite as ss
from datetime import datetime, date
import calendar


def get_daily_counts(year: int, month: int):
    """
    Lấy số record và tổng kg theo ngày cho Stock Old, Packing, Sale trong tháng
    Returns: dict với key là ngày (1-31), value là dict {stockold, stockold_kg, packing, packing_kg, sale, sale_kg}
    """
    # Format ngày cho query: YYYY-MM-DD
    start_date = f"{year}-{month:02d}-01"
    _, last_day = calendar.monthrange(year, month)
    end_date = f"{year}-{month:02d}-{last_day:02d}"
    
    daily_data = {}
    
    # Initialize với 0
    for day in range(1, last_day + 1):
        daily_data[day] = {
            'stockold': 0, 'stockold_kg': 0,
            'packing': 0, 'packing_kg': 0,
            'sale': 0, 'sale_kg': 0
        }
    
    # Query Stock Old - lấy cả count và sum
    sql_stockold = f"""
        SELECT CAST(strftime('%d', [Ngày stock old]) AS INTEGER) as ngay, 
               COUNT(*) as count,
               SUM([Số lượng]) as total_kg
        FROM StockOld
        WHERE [Đã xóa] = 0 
          AND [Ngày stock old] >= '{start_date}'
          AND [Ngày stock old] <= '{end_date}'
        GROUP BY ngay
    """
    df_stockold = ss.query_database_sqlite(sql_string=sql_stockold, data_type='dataframe')
    if df_stockold is not None and len(df_stockold) > 0:
        for _, row in df_stockold.iterrows():
            day = int(row['ngay'])
            if day in daily_data:
                daily_data[day]['stockold'] = int(row['count'])
                daily_data[day]['stockold_kg'] = int(row['total_kg']) if row['total_kg'] else 0
    
    # Query Packing
    sql_packing = f"""
        SELECT CAST(strftime('%d', [Ngày packing]) AS INTEGER) as ngay, 
               COUNT(*) as count,
               SUM([Số lượng]) as total_kg
        FROM Packing
        WHERE [Đã xóa] = 0 
          AND [Ngày packing] >= '{start_date}'
          AND [Ngày packing] <= '{end_date}'
        GROUP BY ngay
    """
    df_packing = ss.query_database_sqlite(sql_string=sql_packing, data_type='dataframe')
    if df_packing is not None and len(df_packing) > 0:
        for _, row in df_packing.iterrows():
            day = int(row['ngay'])
            if day in daily_data:
                daily_data[day]['packing'] = int(row['count'])
                daily_data[day]['packing_kg'] = int(row['total_kg']) if row['total_kg'] else 0
    
    # Query Sale
    sql_sale = f"""
        SELECT CAST(strftime('%d', [Ngày sale]) AS INTEGER) as ngay, 
               COUNT(*) as count,
               SUM([Số lượng]) as total_kg
        FROM Sale
        WHERE [Đã xóa] = 0 
          AND [Ngày sale] >= '{start_date}'
          AND [Ngày sale] <= '{end_date}'
        GROUP BY ngay
    """
    df_sale = ss.query_database_sqlite(sql_string=sql_sale, data_type='dataframe')
    if df_sale is not None and len(df_sale) > 0:
        for _, row in df_sale.iterrows():
            day = int(row['ngay'])
            if day in daily_data:
                daily_data[day]['sale'] = int(row['count'])
                daily_data[day]['sale_kg'] = int(row['total_kg']) if row['total_kg'] else 0
    
    return daily_data


def get_detail_data(selected_date: str, data_type: str):
    """
    Lấy chi tiết dữ liệu theo ngày và loại
    """
    if data_type == 'stockold':
        sql = f"""
            SELECT 
                s.ID,
                sp.[Code cám],
                sp.[Tên cám],
                s.[Số lượng],
                s.[Mã stock old],
                s.[Ngày stock old],
                s.[Ghi chú],
                s.[Người tạo],
                s.[Thời gian tạo]
            FROM StockOld s
            LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
            WHERE s.[Đã xóa] = 0 AND s.[Ngày stock old] = '{selected_date}'
            ORDER BY s.ID DESC
        """
    elif data_type == 'packing':
        sql = f"""
            SELECT 
                p.ID,
                sp.[Code cám],
                sp.[Tên cám],
                p.[Số lượng],
                p.[Mã packing],
                p.[Ngày packing],
                p.[Ghi chú],
                p.[Người tạo],
                p.[Thời gian tạo]
            FROM Packing p
            LEFT JOIN SanPham sp ON p.[ID sản phẩm] = sp.ID
            WHERE p.[Đã xóa] = 0 AND p.[Ngày packing] = '{selected_date}'
            ORDER BY p.ID DESC
        """
    else:  # sale
        sql = f"""
            SELECT 
                s.ID,
                sp.[Code cám],
                sp.[Tên cám],
                s.[Số lượng],
                s.[Mã sale],
                s.[Ngày sale],
                s.[Ghi chú],
                s.[Người tạo],
                s.[Thời gian tạo]
            FROM Sale s
            LEFT JOIN SanPham sp ON s.[ID sản phẩm] = sp.ID
            WHERE s.[Đã xóa] = 0 AND s.[Ngày sale] = '{selected_date}'
            ORDER BY s.ID DESC
        """
    
    return ss.query_database_sqlite(sql_string=sql, data_type='dataframe')


def render_calendar_cell(day: int, data: dict, year: int, month: int, today: date):
    """Render một ô ngày trong lịch"""
    if day == 0:
        st.markdown("&nbsp;")
        return None
    
    current_date = date(year, month, day)
    is_today = current_date == today
    
    stockold = data.get('stockold', 0)
    packing = data.get('packing', 0)
    sale = data.get('sale', 0)
    
    has_data = stockold > 0 or packing > 0 or sale > 0
    
    # Styling
    if is_today:
        bg_color = "#e3f2fd"
        border = "2px solid #1976d2"
    elif has_data:
        bg_color = "#e8f5e9"
        border = "1px solid #4caf50"
    else:
        bg_color = "#fafafa"
        border = "1px solid #e0e0e0"
    
    # Create styled card
    card_html = f"""
    <div style="
        background: {bg_color};
        border: {border};
        border-radius: 8px;
        padding: 8px;
        margin: 2px;
        min-height: 80px;
        cursor: pointer;
    ">
        <div style="font-weight: bold; font-size: 16px; color: #333;">{day}</div>
        <div style="font-size: 11px; color: {'#2e7d32' if stockold > 0 else '#999'};">
            S: {stockold if stockold > 0 else '-'}
        </div>
        <div style="font-size: 11px; color: {'#1565c0' if packing > 0 else '#999'};">
            P: {packing if packing > 0 else '-'}
        </div>
        <div style="font-size: 11px; color: {'#c62828' if sale > 0 else '#999'};">
            L: {sale if sale > 0 else '-'}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    
    return has_data


def app(selected):
    st.header("📅 Lịch tháng - Theo dõi dữ liệu hàng ngày")
    
    # Khởi tạo session state
    if 'selected_calendar_date' not in st.session_state:
        st.session_state.selected_calendar_date = None
    
    # Controls: Chọn tháng và năm
    col1, col2, col3 = st.columns([1, 1, 2])
    
    today = date.today()
    
    with col1:
        month = st.selectbox(
            "📆 Tháng",
            options=list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda x: f"Tháng {x}"
        )
    
    with col2:
        year = st.selectbox(
            "📅 Năm",
            options=list(range(2024, 2031)),
            index=list(range(2024, 2031)).index(today.year) if today.year in range(2024, 2031) else 0
        )
    
    with col3:
        st.markdown("&nbsp;")
        if st.button("🔄 Làm mới dữ liệu", type="secondary"):
            st.rerun()
    
    # Lấy dữ liệu TRƯỚC để dùng cho cả detail và calendar
    daily_data = get_daily_counts(year, month)
    _, last_day = calendar.monthrange(year, month)
    
    # ========== HIỂN THỊ CHI TIẾT NGÀY ĐÃ CHỌN (TRÊN LỊCH) ==========
    if st.session_state.selected_calendar_date:
        selected_date = st.session_state.selected_calendar_date
        selected_day = int(selected_date.split('-')[2])
        selected_month = int(selected_date.split('-')[1])
        selected_year = int(selected_date.split('-')[0])
        
        st.markdown("---")
        
        # Header với nút đóng
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.subheader(f"📋 Chi tiết ngày {selected_day:02d}/{selected_month:02d}/{selected_year}")
        with header_col2:
            if st.button("❌ Đóng", key="close_detail_top", width="stretch"):
                st.session_state.selected_calendar_date = None
                st.rerun()
        
        data = daily_data.get(selected_day, {
            'stockold': 0, 'stockold_kg': 0,
            'packing': 0, 'packing_kg': 0,
            'sale': 0, 'sale_kg': 0
        })
        
        # Summary metrics - 2 hàng: records và kg
        st.markdown("**📊 Thống kê:**")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("📦 Stock Old", f"{data['stockold']} records")
            st.caption(f"💰 {data['stockold_kg']:,} kg")
        with metric_col2:
            st.metric("📋 Packing", f"{data['packing']} records")
            st.caption(f"💰 {data['packing_kg']:,} kg")
        with metric_col3:
            st.metric("💰 Sale", f"{data['sale']} records")
            st.caption(f"💰 {data['sale_kg']:,} kg")
        with metric_col4:
            total_records = data['stockold'] + data['packing'] + data['sale']
            total_kg = data['stockold_kg'] + data['packing_kg'] + data['sale_kg']
            st.metric("📊 Tổng cộng", f"{total_records} records")
            st.caption(f"💰 {total_kg:,} kg")
        
        # Navigation buttons
        st.markdown("##### 🔗 Chuyển đến trang nhập liệu (click rồi chọn tab ở menu trên):")
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
        
        with nav_col1:
            if st.button("📦 Đi tới Stock Old", key="nav_stockold", width="stretch", type="primary"):
                st.session_state.filter_date = selected_date
                st.success(f"✅ Đã lưu ngày {selected_day:02d}/{selected_month:02d}/{selected_year}. Bây giờ click vào tab **'Stock Old'** ở thanh menu trên!")
        
        with nav_col2:
            if st.button("📋 Đi tới Packing", key="nav_packing", width="stretch", type="primary"):
                st.session_state.filter_date = selected_date
                st.success(f"✅ Đã lưu ngày {selected_day:02d}/{selected_month:02d}/{selected_year}. Bây giờ click vào tab **'Packing'** ở thanh menu trên!")
        
        with nav_col3:
            if st.button("💰 Đi tới Sale", key="nav_sale", width="stretch", type="primary"):
                st.session_state.filter_date = selected_date
                st.success(f"✅ Đã lưu ngày {selected_day:02d}/{selected_month:02d}/{selected_year}. Bây giờ click vào tab **'Sale'** ở thanh menu trên!")
        
        with nav_col4:
            if st.button("📦 Đi tới Bao bì", key="nav_baobi", width="stretch", type="secondary"):
                st.session_state.bagstock_filter_date = selected_date
                st.success(f"✅ Đã lưu ngày {selected_day:02d}/{selected_month:02d}/{selected_year}. Bây giờ click vào tab **'Bao bì'** ở thanh menu trên!")
        
        # Tabs for detail data
        st.markdown("##### 📊 Dữ liệu chi tiết:")
        tab1, tab2, tab3 = st.tabs([
            f"📦 Stock Old ({data['stockold']})",
            f"📋 Packing ({data['packing']})",
            f"💰 Sale ({data['sale']})"
        ])
        
        with tab1:
            if data['stockold'] > 0:
                df = get_detail_data(selected_date, 'stockold')
                if df is not None and len(df) > 0:
                    st.dataframe(df, width="stretch", hide_index=True)
                else:
                    st.info("Không có dữ liệu Stock Old")
            else:
                st.info("Không có dữ liệu Stock Old cho ngày này")
        
        with tab2:
            if data['packing'] > 0:
                df = get_detail_data(selected_date, 'packing')
                if df is not None and len(df) > 0:
                    st.dataframe(df, width="stretch", hide_index=True)
                else:
                    st.info("Không có dữ liệu Packing")
            else:
                st.info("Không có dữ liệu Packing cho ngày này")
        
        with tab3:
            if data['sale'] > 0:
                df = get_detail_data(selected_date, 'sale')
                if df is not None and len(df) > 0:
                    st.dataframe(df, width="stretch", hide_index=True)
                else:
                    st.info("Không có dữ liệu Sale")
            else:
                st.info("Không có dữ liệu Sale cho ngày này")
        
        st.markdown("---")
    
    # Legend
    st.markdown("""
    <div style="display: flex; gap: 20px; margin-bottom: 15px; font-size: 12px;">
        <span><strong style="color: #2e7d32;">S</strong> = Stock Old</span>
        <span><strong style="color: #1565c0;">P</strong> = Packing</span>
        <span><strong style="color: #c62828;">L</strong> = Sale</span>
        <span style="margin-left: 20px;">
            <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 4px;">Hôm nay</span>
            <span style="background: #e8f5e9; padding: 2px 8px; border-radius: 4px; margin-left: 5px;">Có dữ liệu</span>
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Tạo calendar grid (daily_data và last_day đã được lấy trước đó)
    first_weekday = calendar.monthrange(year, month)[0]  # 0=Monday, 6=Sunday
    
    # Header: Thứ trong tuần
    weekdays = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    cols = st.columns(7)
    for i, wd in enumerate(weekdays):
        with cols[i]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: #666;'>{wd}</div>", unsafe_allow_html=True)
    
    # Calendar rows
    day = 1
    for week in range(6):  # Max 6 weeks in a month view
        if day > last_day:
            break
        
        cols = st.columns(7)
        for weekday in range(7):
            with cols[weekday]:
                if week == 0 and weekday < first_weekday:
                    # Empty cells before first day
                    render_calendar_cell(0, {}, year, month, today)
                elif day <= last_day:
                    # Create button for each day
                    data = daily_data.get(day, {'stockold': 0, 'packing': 0, 'sale': 0})
                    has_data = data['stockold'] > 0 or data['packing'] > 0 or data['sale'] > 0
                    
                    # Use button for interaction
                    button_label = f"{day}"
                    if has_data:
                        button_label = f"📊 {day}"
                    
                    current_date = date(year, month, day)
                    is_today = current_date == today
                    
                    # Show mini stats
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 10px; color: #666;">
                        S:{data['stockold']} P:{data['packing']} L:{data['sale']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    btn_type = "primary" if is_today else ("secondary" if has_data else "secondary")
                    if st.button(
                        button_label,
                        key=f"day_{year}_{month}_{day}",
                        width="stretch",
                        type=btn_type if has_data or is_today else "secondary"
                    ):
                        st.session_state.selected_calendar_date = f"{year}-{month:02d}-{day:02d}"
                    
                    day += 1
                else:
                    render_calendar_cell(0, {}, year, month, today)
    
    # Statistics section
    st.markdown("---")
    st.subheader(f"📊 Thống kê tháng {month}/{year}")
    
    total_stockold = sum(d['stockold'] for d in daily_data.values())
    total_packing = sum(d['packing'] for d in daily_data.values())
    total_sale = sum(d['sale'] for d in daily_data.values())
    days_with_data = sum(1 for d in daily_data.values() if d['stockold'] > 0 or d['packing'] > 0 or d['sale'] > 0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng Stock Old", f"{total_stockold:,}")
    with col2:
        st.metric("Tổng Packing", f"{total_packing:,}")
    with col3:
        st.metric("Tổng Sale", f"{total_sale:,}")
    with col4:
        st.metric("Số ngày có dữ liệu", f"{days_with_data}/{last_day}")
