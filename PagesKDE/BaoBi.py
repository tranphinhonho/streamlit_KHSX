import streamlit as st
from admin.sys_kde_components import *
import sqlite3
from datetime import datetime, timedelta, date
import pandas as pd

def app(selected):
    
    # Kích cỡ bao phổ biến
    BAG_SIZES = [50, 40, 25, 20, 10, 5]  # kg
    LOAI_BAO = ['Bao PP', 'Bao PE', 'Bao Kraft', 'Bao Jumbo']
    
    # Tạo tabs - Tồn kho từ Email luôn ở đầu
    tab4, tab1, tab2, tab3 = st.tabs([
        "📦 Tồn kho từ Email",
        "🚨 Cảnh báo tồn kho", 
        "✍️ Cập nhật tồn kho",
        "📋 Lịch sử tồn kho"
    ])
    
    # TAB 1: Cảnh báo
    with tab1:
        st.header("🚨 Cảnh báo tồn kho bao bì")
        
        # Chọn ngày kiểm tra
        ngay_kiem_tra = st.date_input(
            "Ngày kiểm tra", 
            value=fn.get_vietnam_time().date(),
            help="Chọn ngày cần kiểm tra tồn kho"
        )
        
        if st.button("🔍 Kiểm tra tồn kho", type="primary", width="stretch"):
            with st.spinner("Đang kiểm tra..."):
                kiem_tra = kiem_tra_ton_kho(ngay_kiem_tra)
                
                if kiem_tra:
                    st.session_state['kiem_tra_baobj'] = kiem_tra
                else:
                    st.warning("⚠️ Chưa có dữ liệu tồn kho")
        
        # Hiển thị cảnh báo
        if 'kiem_tra_baobj' in st.session_state and st.session_state['kiem_tra_baobj']:
            hien_thi_canh_bao(st.session_state['kiem_tra_baobj'], ngay_kiem_tra)
    
    # TAB 2: Cập nhật tồn kho
    with tab2:
        st.header("✍️ Cập nhật tồn kho bao bì")
        
        col1, col2 = st.columns(2)
        with col1:
            ngay_cap_nhat = st.date_input(
                "Ngày cập nhật", 
                value=fn.get_vietnam_time().date()
            )
        
        with col2:
            # Nút tính nhu cầu tự động
            if st.button("🤖 Tính nhu cầu từ Packing", help="Tự động tính nhu cầu dựa trên kế hoạch đóng bao"):
                nhu_cau = tinh_nhu_cau_tu_packing(ngay_cap_nhat)
                if nhu_cau:
                    st.session_state['nhu_cau_bao'] = nhu_cau
                    st.success(f"✅ Đã tính xong! Tổng nhu cầu: {sum(nhu_cau.values()):,} bao")
                else:
                    st.info("ℹ️ Chưa có kế hoạch đóng bao")
        
        # Hiển thị nhu cầu tính được
        if 'nhu_cau_bao' in st.session_state:
            st.subheader("📊 Nhu cầu dự kiến")
            for key, value in st.session_state['nhu_cau_bao'].items():
                st.write(f"- {key}: **{value:,} bao**")
        
        # Form nhập liệu
        data = {
            'Loại bao': ['Bao PP'],
            'Kích cỡ (kg)': [50],
            'Tồn kho hiện tại': [0],
            'Nhu cầu dự kiến': [0],
            'Ghi chú': [None]
        }
        
        df = pd.DataFrame(data)
        
        column_config = {
            'Loại bao': st.column_config.SelectboxColumn(
                'Loại bao', 
                options=LOAI_BAO, 
                width='medium'
            ),
            'Kích cỡ (kg)': st.column_config.SelectboxColumn(
                'Kích cỡ (kg)', 
                options=BAG_SIZES, 
                width='small'
            ),
            'Tồn kho hiện tại': st.column_config.NumberColumn(
                'Tồn kho hiện tại', 
                min_value=0, 
                step=1, 
                format="%d bao", 
                width='medium'
            ),
            'Nhu cầu dự kiến': st.column_config.NumberColumn(
                'Nhu cầu dự kiến', 
                min_value=0, 
                step=1, 
                format="%d bao", 
                width='medium',
                help="Số bao cần sử dụng trong thời gian tới"
            ),
            'Ghi chú': st.column_config.TextColumn('Ghi chú', width='large')
        }
        
        df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='baobj_manual')
        
        df_insert = df_insert.dropna(subset=['Loại bao'])
        
        # Tính toán cảnh báo và số lượng thiếu
        if len(df_insert) > 0:
            df_insert['Ngày kiểm tra'] = ngay_cap_nhat
            
            # Tính số lượng thiếu
            df_insert['Số lượng thiếu'] = df_insert.apply(
                lambda row: max(0, row['Nhu cầu dự kiến'] - row['Tồn kho hiện tại']),
                axis=1
            )
            
            # Xác định mức cảnh báo
            df_insert['Mức cảnh báo'] = df_insert.apply(
                lambda row: xac_dinh_muc_canh_bao(row['Tồn kho hiện tại'], row['Nhu cầu dự kiến']),
                axis=1
            )
            
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
        
        # Hiển thị preview với màu cảnh báo
        if len(df_insert) > 0:
            st.subheader("👀 Preview")
            
            for idx, row in df_insert.iterrows():
                icon = get_warning_icon(row['Mức cảnh báo'])
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"{icon} **{row['Loại bao']} {row['Kích cỡ (kg)']}kg**")
                with col2:
                    st.metric("Tồn kho", f"{row['Tồn kho hiện tại']:,}")
                with col3:
                    st.metric("Nhu cầu", f"{row['Nhu cầu dự kiến']:,}")
                with col4:
                    if row['Số lượng thiếu'] > 0:
                        st.metric("Thiếu", f"{row['Số lượng thiếu']:,}", delta=f"-{row['Số lượng thiếu']}", delta_color="inverse")
                    else:
                        st.metric("Trạng thái", "OK", delta=f"+{row['Tồn kho hiện tại'] - row['Nhu cầu dự kiến']}", delta_color="normal")
        
        disabled = not (len(df_insert) > 0)
        
        if st.button("💾 Lưu tồn kho", disabled=disabled, type="primary", key='btn_save_baobj'):
            result = ss.insert_data_to_sql_server(table_name='BaoBi', dataframe=df_insert)
            show_notification("Lỗi:", result)
            if result[0]:
                st.session_state.pop('kiem_tra_baobj', None)  # Xóa cache
                st.session_state.pop('nhu_cau_bao', None)
    
    # TAB 3: Lịch sử
    with tab3:
        st.header("📋 Lịch sử tồn kho bao bì")
        
        column_config = {
            'Ngày kiểm tra': st.column_config.DateColumn('Ngày kiểm tra', format='DD/MM/YYYY'),
            'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss')
        }
        
        dataframe_with_selections(
            table_name="BaoBi",
            columns=[
                'ID', 'Ngày kiểm tra', 'Loại bao', 'Kích cỡ (kg)',
                'Tồn kho hiện tại', 'Nhu cầu dự kiến', 'Mức cảnh báo',
                'Số lượng thiếu', 'Ghi chú', 'Người tạo', 'Thời gian tạo'
            ],
            colums_disable=['ID', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'],
            col_where={'Đã xóa': ('=', 0)},
            col_order={'ID': 'DESC'},
            column_config=column_config,
            key=f'BaoBi_{st.session_state.df_key}',
            join_user_info=True
        )
    
    # TAB 4: Tồn kho từ Email (BagStock)
    with tab4:
        st.header("📦 Tồn kho bao bì từ Email")
        st.caption("Dữ liệu import từ file DAILY STOCK EMPTY BAG REPORT")
        
        # Kiểm tra nếu có ngày được truyền từ Lịch tháng
        if 'bagstock_filter_date' in st.session_state and st.session_state.bagstock_filter_date:
            filter_date_str = st.session_state.bagstock_filter_date
            parts = filter_date_str.split('-')
            default_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            st.info(f"📅 Đang lọc theo ngày từ Lịch tháng: {parts[2]}/{parts[1]}/{parts[0]}")
            
            # Nút xóa filter
            if st.button("❌ Xóa lọc ngày", key="clear_bagstock_filter"):
                st.session_state.bagstock_filter_date = None
                st.rerun()
        else:
            # Lấy ngày gần nhất có dữ liệu trong BagStock
            try:
                conn_check = ss.connect_db()
                cursor = conn_check.cursor()
                cursor.execute("SELECT MAX([NgayStock]) FROM BagStock WHERE [DaXoa] = 0")
                latest = cursor.fetchone()[0]
                conn_check.close()
                
                if latest:
                    parts = latest.split('-')
                    default_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    default_date = fn.get_vietnam_time().date()
            except:
                default_date = fn.get_vietnam_time().date()
        
        # Chọn ngày và tìm kiếm
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            ngay_xem = st.date_input(
                "Chọn ngày xem",
                value=default_date,
                key="ngay_bagstock"
            )
        
        with col2:
            search_term = st.text_input(
                "🔍 Tìm kiếm tên cám",
                placeholder="Nhập tên cám cần tìm...",
                key="search_tencam"
            )
        
        with col3:
            st.write("")
            btn_refresh = st.button("🔄 Làm mới", type="secondary", width="stretch")
        
        # Auto-load dữ liệu mặc định (luôn hiển thị)
        from_lichthang = 'bagstock_filter_date' in st.session_state and st.session_state.bagstock_filter_date
        # Luôn load dữ liệu - True by default
        if True:
            conn = ss.connect_db()
            
            # Query với điều kiện tìm kiếm
            if search_term:
                query = """
                SELECT 
                    [TenCam] as [Tên cám],
                    [KichCoDongBao] as [Kích cỡ],
                    [SoLuongBaoBi] as [Số lượng bao],
                    [NgayStock] as [Ngày stock],
                    [TenFile] as [File nguồn],
                    [ThoiGianTao] as [Thời gian import]
                FROM BagStock
                WHERE [NgayStock] = ?
                AND [DaXoa] = 0
                AND [TenCam] LIKE ?
                ORDER BY [TenCam]
                """
                params = (ngay_xem, f"%{search_term}%")
            else:
                query = """
                SELECT 
                    [TenCam] as [Tên cám],
                    [KichCoDongBao] as [Kích cỡ],
                    [SoLuongBaoBi] as [Số lượng bao],
                    [NgayStock] as [Ngày stock],
                    [TenFile] as [File nguồn],
                    [ThoiGianTao] as [Thời gian import]
                FROM BagStock
                WHERE [NgayStock] = ?
                AND [DaXoa] = 0
                ORDER BY [TenCam]
                """
                params = (ngay_xem,)
            
            try:
                df_bagstock = pd.read_sql_query(query, conn, params=params)
                conn.close()
                
                if len(df_bagstock) > 0:
                    if search_term:
                        st.success(f"✅ Tìm thấy {len(df_bagstock)} dòng cho '{search_term}'")
                    else:
                        st.success(f"✅ Tìm thấy {len(df_bagstock)} dòng dữ liệu")
                    
                    # Metrics tổng quan
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📦 Tổng số dòng", len(df_bagstock))
                    with col2:
                        st.metric("🏷️ Tổng số bao", f"{df_bagstock['Số lượng bao'].sum():,}")
                    with col3:
                        st.metric("📐 Số kích cỡ", df_bagstock['Kích cỡ'].nunique())
                    
                    # Bảng dữ liệu
                    st.dataframe(
                        df_bagstock,
                        width="stretch",
                        hide_index=True,
                        column_config={
                            'Số lượng bao': st.column_config.NumberColumn(
                                'Số lượng bao',
                                format="%d"
                            )
                        }
                    )
                    
                    # Biểu đồ theo kích cỡ (chỉ hiển thị khi không tìm kiếm)
                    if not search_term:
                        st.subheader("📊 Tồn kho theo kích cỡ đóng bao")
                        chart_data = df_bagstock.groupby('Kích cỡ')['Số lượng bao'].sum()
                        st.bar_chart(chart_data)
                else:
                    if search_term:
                        st.warning(f"⚠️ Không tìm thấy '{search_term}' trong ngày {ngay_xem.strftime('%d/%m/%Y')}")
                    else:
                        st.warning(f"⚠️ Không có dữ liệu cho ngày {ngay_xem.strftime('%d/%m/%Y')}")
                    st.info("💡 Hãy import file BAG REPORT từ trang 'Nhận email'")
            except Exception as e:
                conn.close()
                if "no such table" in str(e).lower():
                    st.info("📭 Chưa có dữ liệu. Hãy import file BAG REPORT từ trang 'Nhận email'")
                else:
                    st.error(f"Lỗi: {e}")


def xac_dinh_muc_canh_bao(ton_kho, nhu_cau):
    """
    Xác định mức cảnh báo:
    - Mức 1 🚨: Thiếu hàng (tồn kho < nhu cầu)
    - Mức 2 ⚠️: Tồn kho thấp (1-500 bao)
    - Mức 3 🟡: Tồn kho trung bình (501-2,000 bao)
    - Mức 4 ✅: An toàn (>2,000 bao)
    """
    chenh_lech = ton_kho - nhu_cau
    
    if chenh_lech < 0:
        return "Mức 1 🚨 Thiếu hàng"
    elif ton_kho <= 500:
        return "Mức 2 ⚠️ Tồn kho thấp"
    elif ton_kho <= 2000:
        return "Mức 3 🟡 Tồn kho trung bình"
    else:
        return "Mức 4 ✅ An toàn"


def get_warning_icon(muc_canh_bao):
    """Lấy icon tương ứng với mức cảnh báo"""
    if 'Mức 1' in muc_canh_bao:
        return '🚨'
    elif 'Mức 2' in muc_canh_bao:
        return '⚠️'
    elif 'Mức 3' in muc_canh_bao:
        return '🟡'
    else:
        return '✅'


def tinh_nhu_cau_tu_packing(ngay):
    """Tính nhu cầu bao bì từ kế hoạch đóng bao"""
    conn = ss.connect_db()
    
    query = """
    SELECT 
        [Kích cỡ bao (kg)],
        SUM([Số bao]) as tong_so_bao
    FROM PackingPlan
    WHERE [Ngày đóng bao] = ?
    AND [Đã xóa] = 0
    GROUP BY [Kích cỡ bao (kg)]
    """
    
    df = pd.read_sql_query(query, conn, params=(ngay,))
    conn.close()
    
    if len(df) == 0:
        return None
    
    nhu_cau = {}
    for _, row in df.iterrows():
        key = f"Bao {int(row['Kích cỡ bao (kg)'])}kg"
        nhu_cau[key] = int(row['tong_so_bao'])
    
    return nhu_cau


def kiem_tra_ton_kho(ngay):
    """Kiểm tra tồn kho từ BagStock và so sánh với nhu cầu từ Packing Plan"""
    conn = ss.connect_db()
    
    # Lấy tồn kho từ BagStock (dữ liệu import từ email)
    # Lấy dữ liệu gần nhất với ngày được chọn
    query_stock = """
    SELECT 
        [TenCam] as [Tên cám],
        [KichCoDongBao] as [Kích cỡ (kg)],
        [SoLuongBaoBi] as [Tồn kho hiện tại],
        [NgayStock] as [Ngày stock]
    FROM BagStock
    WHERE [NgayStock] <= ?
    AND [DaXoa] = 0
    ORDER BY [NgayStock] DESC
    """
    
    try:
        df_stock = pd.read_sql_query(query_stock, conn, params=(ngay,))
    except:
        conn.close()
        return None
    
    if len(df_stock) == 0:
        conn.close()
        return None
    
    # Lấy ngày stock gần nhất
    ngay_stock_gan_nhat = df_stock['Ngày stock'].iloc[0]
    df_stock = df_stock[df_stock['Ngày stock'] == ngay_stock_gan_nhat]
    
    # Lấy nhu cầu từ Packing Plan cho ngày đó hoặc các ngày tới
    query_packing = """
    SELECT 
        sp.[Tên cám],
        p.[Kích cỡ bao (kg)] as 'Kích cỡ (kg)',
        SUM(p.[Số bao]) as 'Nhu cầu dự kiến'
    FROM PackingPlan p
    LEFT JOIN SanPham sp ON p.[ID sản phẩm] = sp.ID
    WHERE p.[Ngày đóng bao] >= ?
    AND p.[Đã xóa] = 0
    GROUP BY sp.[Tên cám], p.[Kích cỡ bao (kg)]
    """
    
    try:
        df_packing = pd.read_sql_query(query_packing, conn, params=(ngay,))
    except:
        df_packing = pd.DataFrame()
    
    conn.close()
    
    # Group tồn kho theo kích cỡ
    df_stock_grouped = df_stock.groupby('Kích cỡ (kg)')['Tồn kho hiện tại'].sum().reset_index()
    
    # Group nhu cầu theo kích cỡ
    if len(df_packing) > 0:
        df_packing_grouped = df_packing.groupby('Kích cỡ (kg)')['Nhu cầu dự kiến'].sum().reset_index()
    else:
        df_packing_grouped = pd.DataFrame(columns=['Kích cỡ (kg)', 'Nhu cầu dự kiến'])
    
    # Merge để so sánh
    df_merged = df_stock_grouped.merge(
        df_packing_grouped, 
        on='Kích cỡ (kg)', 
        how='left'
    )
    df_merged['Nhu cầu dự kiến'] = df_merged['Nhu cầu dự kiến'].fillna(0).astype(int)
    df_merged['Tồn kho hiện tại'] = df_merged['Tồn kho hiện tại'].astype(int)
    
    # Tính số lượng thiếu và mức cảnh báo
    df_merged['Số lượng thiếu'] = df_merged.apply(
        lambda row: max(0, row['Nhu cầu dự kiến'] - row['Tồn kho hiện tại']),
        axis=1
    )
    
    df_merged['Mức cảnh báo'] = df_merged.apply(
        lambda row: xac_dinh_muc_canh_bao(row['Tồn kho hiện tại'], row['Nhu cầu dự kiến']),
        axis=1
    )
    
    df_merged['Ngày stock'] = ngay_stock_gan_nhat
    
    # Phân loại theo mức cảnh báo
    muc_1 = df_merged[df_merged['Mức cảnh báo'].str.contains('Mức 1', na=False)]
    muc_2 = df_merged[df_merged['Mức cảnh báo'].str.contains('Mức 2', na=False)]
    muc_3 = df_merged[df_merged['Mức cảnh báo'].str.contains('Mức 3', na=False)]
    muc_4 = df_merged[df_merged['Mức cảnh báo'].str.contains('Mức 4', na=False)]
    
    return {
        'all': df_merged,
        'muc_1': muc_1,
        'muc_2': muc_2,
        'muc_3': muc_3,
        'muc_4': muc_4,
        'ngay_stock': ngay_stock_gan_nhat
    }


def hien_thi_canh_bao(data, ngay):
    """Hiển thị cảnh báo tồn kho từ BagStock"""
    
    # Hiển thị ngày stock thực tế
    ngay_stock = data.get('ngay_stock', ngay)
    st.subheader(f"📅 Tình trạng tồn kho (Dữ liệu ngày {ngay_stock})")
    st.caption(f"So sánh với nhu cầu từ Packing Plan từ ngày {ngay.strftime('%d/%m/%Y')}")
    
    # Metrics tổng quan
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚨 Thiếu hàng", len(data['muc_1']))
    with col2:
        st.metric("⚠️ Tồn kho thấp", len(data['muc_2']))
    with col3:
        st.metric("🟡 Tồn kho TB", len(data['muc_3']))
    with col4:
        st.metric("✅ An toàn", len(data['muc_4']))
    
    # Hiển thị chi tiết theo mức cảnh báo
    if len(data['muc_1']) > 0:
        with st.expander("🚨 MỨC 1: THIẾU HÀNG - CẦN ĐẶT NGAY", expanded=True):
            st.error("⚠️ **CẢNH BÁO KHẨN CẤP**: Các loại bao sau đang thiếu!")
            
            for _, row in data['muc_1'].iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**Bao {int(row['Kích cỡ (kg)'])}kg**")
                with col2:
                    st.metric("Tồn kho", f"{row['Tồn kho hiện tại']:,}")
                with col3:
                    st.metric("Nhu cầu", f"{row['Nhu cầu dự kiến']:,}")
                with col4:
                    st.metric("Thiếu", f"{row['Số lượng thiếu']:,}", delta=f"-{row['Số lượng thiếu']}", delta_color="inverse")
    
    if len(data['muc_2']) > 0:
        with st.expander("⚠️ MỨC 2: TỒN KHO THẤP (1-500 bao)", expanded=True):
            st.warning("Cần theo dõi và chuẩn bị đặt hàng")
            df_display = data['muc_2'].copy()
            df_display['Loại bao'] = df_display['Kích cỡ (kg)'].apply(lambda x: f"Bao {int(x)}kg")
            st.dataframe(df_display[['Loại bao', 'Tồn kho hiện tại', 'Nhu cầu dự kiến', 'Số lượng thiếu']], 
                        width="stretch", hide_index=True)
    
    if len(data['muc_3']) > 0:
        with st.expander("🟡 MỨC 3: TỒN KHO TRUNG BÌNH (501-2,000 bao)", expanded=False):
            st.info("Tồn kho ở mức trung bình")
            df_display = data['muc_3'].copy()
            df_display['Loại bao'] = df_display['Kích cỡ (kg)'].apply(lambda x: f"Bao {int(x)}kg")
            st.dataframe(df_display[['Loại bao', 'Tồn kho hiện tại', 'Nhu cầu dự kiến']], 
                        width="stretch", hide_index=True)
    
    if len(data['muc_4']) > 0:
        with st.expander("✅ MỨC 4: TỒN KHO AN TOÀN (>2,000 bao)", expanded=False):
            st.success("Tồn kho đầy đủ")
            df_display = data['muc_4'].copy()
            df_display['Loại bao'] = df_display['Kích cỡ (kg)'].apply(lambda x: f"Bao {int(x)}kg")
            st.dataframe(df_display[['Loại bao', 'Tồn kho hiện tại', 'Nhu cầu dự kiến']], 
                        width="stretch", hide_index=True)
    
    # Biểu đồ tổng quan
    st.subheader("📊 Biểu đồ tồn kho theo kích cỡ")
    
    chart_data = data['all'][['Kích cỡ (kg)', 'Tồn kho hiện tại', 'Nhu cầu dự kiến']].copy()
    chart_data['Label'] = chart_data['Kích cỡ (kg)'].apply(lambda x: f"Bao {int(x)}kg")
    chart_data = chart_data.set_index('Label')[['Tồn kho hiện tại', 'Nhu cầu dự kiến']]
    
    st.bar_chart(chart_data)
