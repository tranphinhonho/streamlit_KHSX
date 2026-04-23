import streamlit as st
from admin.sys_kde_components import *
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

def app(selected):
    
    # Ma trận ánh xạ Pellet → Packing Line
    PACKING_MAPPING = {
        'Cám bột': 'Packing 3',
        'Pellet 1': 'Packing 5',
        'Pellet 2': 'Packing 1',
        'Pellet 3': 'Packing 2',
        'Pellet 4': 'Packing 4',
        'Pellet 5': 'Packing 6',
        'Pellet 6': 'Packing 7',
        'Pellet 7': 'Packing 8'
    }
    
    # Kích cỡ bao phổ biến
    BAG_SIZES = [50, 40, 25, 20, 10, 5]  # kg
    
    # Tạo tabs
    tab1, tab2, tab3 = st.tabs([
        "🤖 Tạo kế hoạch từ Pellet", 
        "✍️ Nhập thủ công",
        "📋 Danh sách Packing"
    ])
    
    # TAB 1: Tạo từ Pellet
    with tab1:
        st.header("🤖 Tạo kế hoạch đóng bao từ Pellet")
        
        # Chọn ngày
        col1, col2 = st.columns(2)
        with col1:
            ngay_packing = st.date_input(
                "Ngày đóng bao", 
                value=fn.get_vietnam_time().date(),
                help="Chọn ngày cần lên kế hoạch đóng bao"
            )
        
        with col2:
            st.metric("Số line đóng bao", "8 lines", help="Packing 1-8")
        
        if st.button("🔄 Tạo kế hoạch đóng bao", type="primary", width="stretch"):
            with st.spinner("Đang tạo kế hoạch..."):
                ke_hoach = tao_ke_hoach_packing(ngay_packing)
                
                if ke_hoach:
                    st.session_state['ke_hoach_packing'] = ke_hoach
                    st.success(f"✅ Đã tạo xong! Tổng: {ke_hoach['tong_san_luong']:.1f} tấn")
                else:
                    st.warning("⚠️ Không có dữ liệu Pellet cho ngày này")
        
        # Hiển thị kế hoạch đã tính
        if 'ke_hoach_packing' in st.session_state and st.session_state['ke_hoach_packing']:
            hien_thi_ke_hoach_packing(st.session_state['ke_hoach_packing'], ngay_packing)
    
    # TAB 2: Nhập thủ công
    with tab2:
        st.header("✍️ Nhập kế hoạch đóng bao thủ công")
        
        # Lấy danh sách sản phẩm
        ds_sanpham = ss.get_columns_data(
            table_name='SanPham',
            columns=['Code cám', 'Tên cám', 'Dạng ép viên', 'Kích cỡ ép viên', 'ID'],
            data_type='list',
            col_where={'Đã xóa': ('=', 0)}
        )
        
        data = {
            'Ngày đóng bao': [None],
            'ID sản phẩm': [None],
            'Số lượng (tấn)': [0],
            'Kích cỡ bao (kg)': [50],
            'Line đóng bao': ['Packing 1'],
            'Thời gian bắt đầu': [None],
            'Ghi chú': [None]
        }
        
        df = pd.DataFrame(data)
        
        column_config = {
            'Ngày đóng bao': st.column_config.DateColumn('Ngày đóng bao', format='DD/MM/YYYY', width='medium'),
            'ID sản phẩm': st.column_config.SelectboxColumn(
                'ID sản phẩm', 
                options=ds_sanpham, 
                format_func=lambda x: x, 
                width='large',
                help="Chọn sản phẩm cần đóng bao"
            ),
            'Số lượng (tấn)': st.column_config.NumberColumn('Số lượng (tấn)', min_value=0, step=0.1, format="%.1f", width='small'),
            'Kích cỡ bao (kg)': st.column_config.SelectboxColumn(
                'Kích cỡ bao (kg)', 
                options=BAG_SIZES, 
                width='small'
            ),
            'Line đóng bao': st.column_config.SelectboxColumn(
                'Line đóng bao', 
                options=[f'Packing {i}' for i in range(1, 9)], 
                width='medium'
            ),
            'Thời gian bắt đầu': st.column_config.DatetimeColumn('Thời gian bắt đầu', format='DD/MM/YYYY HH:mm', width='medium'),
            'Ghi chú': st.column_config.TextColumn('Ghi chú', width='large')
        }
        
        df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='packing_manual')
        
        df_insert = df_insert.dropna(subset=['ID sản phẩm'])
        df_insert = df_insert[df_insert['Số lượng (tấn)'] > 0]
        
        # Tính toán số bao
        if len(df_insert) > 0:
            df_insert = fn.tachma_df(df_insert, column_names=['ID sản phẩm'], delimiter='|', index=-1)
            
            # Tính số bao = (tấn × 1000) / kích cỡ bao
            df_insert['Số bao'] = df_insert.apply(
                lambda row: int((row['Số lượng (tấn)'] * 1000) / row['Kích cỡ bao (kg)']),
                axis=1
            )
            
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.dataframe(df_insert, width='content')
        
        disabled = not (len(df_insert) > 0)
        
        if st.button("Thêm Packing", disabled=disabled, type="primary", key='btn_add_packing'):
            result = ss.insert_data_to_sql_server(table_name='PackingPlan', dataframe=df_insert)
            show_notification("Lỗi:", result)
            if result[0]:
                st.session_state.pop('ke_hoach_packing', None)  # Xóa cache
    
    # TAB 3: Danh sách Packing
    with tab3:
        st.header("📋 Danh sách kế hoạch đóng bao")
        
        column_config = {
            'Ngày đóng bao': st.column_config.DateColumn('Ngày đóng bao', format='DD/MM/YYYY'),
            'Thời gian bắt đầu': st.column_config.DatetimeColumn('Thời gian bắt đầu', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian kết thúc': st.column_config.DatetimeColumn('Thời gian kết thúc', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss')
        }
        
        dataframe_with_selections(
            table_name="PackingPlan",
            columns=[
                'ID', 'Ngày đóng bao', 'ID sản phẩm', 'Số lượng (tấn)',
                'Kích cỡ bao (kg)', 'Số bao', 'Line đóng bao',
                'Thời gian bắt đầu', 'Thời gian kết thúc', 'Ghi chú',
                'Người tạo', 'Thời gian tạo'
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
            key=f'PackingPlan_{st.session_state.df_key}',
            join_user_info=True
        )


def tao_ke_hoach_packing(ngay_packing):
    """
    Tạo kế hoạch đóng bao từ dữ liệu Pellet
    Ánh xạ Pellet machine → Packing line
    """
    conn = sqlite3.connect('database_new.db')
    
    # Lấy dữ liệu Pellet
    query = """
    SELECT 
        p.ID,
        p.[Ngày sản xuất],
        sp.[Tên cám] as [Tên sản phẩm],
        p.[Số lượng],
        p.[Số máy],
        sp.[Kích cỡ ép viên]
    FROM Pellet p
    LEFT JOIN SanPham sp ON p.[ID sản phẩm] = sp.ID
    WHERE p.[Ngày sản xuất] = ? 
    AND p.[Đã xóa] = 0
    ORDER BY p.[Số máy]
    """
    
    df = pd.read_sql_query(query, conn, params=(ngay_packing,))
    conn.close()
    
    if len(df) == 0:
        return None
    
    # Ma trận ánh xạ
    MAPPING = {
        'Cám bột': 'Packing 3',
        'Pellet 1': 'Packing 5',
        'Pellet 2': 'Packing 1',
        'Pellet 3': 'Packing 2',
        'Pellet 4': 'Packing 4',
        'Pellet 5': 'Packing 6',
        'Pellet 6': 'Packing 7',
        'Pellet 7': 'Packing 8'
    }
    
    # Tạo kế hoạch đóng bao
    ke_hoach = []
    
    for _, row in df.iterrows():
        # Ánh xạ sang line đóng bao
        line_packing = MAPPING.get(row['Số máy'], 'Packing 1')
        
        # Xác định kích cỡ bao (mặc định 50kg)
        kich_co_bao = 50
        if pd.notna(row['Kích cỡ ép viên']):
            # Lấy số từ chuỗi "Viên 5mm" → 5
            try:
                size_str = str(row['Kích cỡ ép viên']).split()[1].replace('mm', '')
                # Ánh xạ kích cỡ viên → kích cỡ bao
                # Có thể tùy chỉnh logic này
                kich_co_bao = 50  # Mặc định
            except:
                kich_co_bao = 50
        
        # Tính số bao = (tấn × 1000) / kích cỡ bao
        so_bao = int((row['Số lượng'] * 1000) / kich_co_bao)
        
        ke_hoach.append({
            'ID Pellet': row['ID'],
            'Tên sản phẩm': row['Tên sản phẩm'],
            'Số lượng (tấn)': row['Số lượng'],
            'Kích cỡ bao (kg)': kich_co_bao,
            'Số bao': so_bao,
            'Line đóng bao': line_packing
        })
    
    tong_san_luong = sum(item['Số lượng (tấn)'] for item in ke_hoach)
    tong_so_bao = sum(item['Số bao'] for item in ke_hoach)
    
    return {
        'ke_hoach': ke_hoach,
        'tong_san_luong': tong_san_luong,
        'tong_so_bao': tong_so_bao
    }


def hien_thi_ke_hoach_packing(data, ngay_packing):
    """Hiển thị kế hoạch đóng bao"""
    
    st.subheader(f"📅 Kế hoạch đóng bao ngày {ngay_packing.strftime('%d/%m/%Y')}")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng sản lượng", f"{data['tong_san_luong']:.1f} tấn")
    with col2:
        st.metric("Tổng số bao", f"{data['tong_so_bao']:,} bao")
    with col3:
        lines_used = len(set(item['Line đóng bao'] for item in data['ke_hoach']))
        st.metric("Số line sử dụng", f"{lines_used}/8 lines")
    
    # Bảng chi tiết
    st.subheader("📊 Chi tiết theo Line")
    
    df_display = pd.DataFrame(data['ke_hoach'])
    
    # Nhóm theo Line đóng bao
    lines = df_display['Line đóng bao'].unique()
    
    for line in sorted(lines):
        df_line = df_display[df_display['Line đóng bao'] == line]
        
        with st.expander(f"📦 {line} ({len(df_line)} sản phẩm)", expanded=True):
            # Tổng kết line
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tổng sản lượng", f"{df_line['Số lượng (tấn)'].sum():.1f} tấn")
            with col2:
                st.metric("Tổng số bao", f"{df_line['Số bao'].sum():,} bao")
            
            # Bảng chi tiết
            st.dataframe(df_line, width="stretch", hide_index=True)
    
    # Biểu đồ phân bố
    st.subheader("📈 Phân bố sản lượng theo Line")
    
    # Tạo dữ liệu cho biểu đồ
    line_summary = df_display.groupby('Line đóng bao').agg({
        'Số lượng (tấn)': 'sum',
        'Số bao': 'sum'
    }).reset_index()
    
    st.bar_chart(line_summary.set_index('Line đóng bao')['Số lượng (tấn)'])
    
    # Nút lưu
    if st.button("💾 Lưu kế hoạch đóng bao", type="primary", width="stretch"):
        luu_ke_hoach_packing(data['ke_hoach'], ngay_packing)


def luu_ke_hoach_packing(ke_hoach, ngay_packing):
    """Lưu kế hoạch đóng bao vào database"""
    df = pd.DataFrame(ke_hoach)
    df['Ngày đóng bao'] = ngay_packing
    df['Người tạo'] = st.session_state.username
    df['Thời gian tạo'] = fn.get_vietnam_time()
    
    # Tính thời gian bắt đầu (giả định bắt đầu từ 8:00)
    start_time = datetime.combine(ngay_packing, datetime.min.time()).replace(hour=8)
    
    for idx, row in df.iterrows():
        df.at[idx, 'Thời gian bắt đầu'] = start_time
        # Giả định mỗi line đóng ~2 giờ
        df.at[idx, 'Thời gian kết thúc'] = start_time + timedelta(hours=2)
    
    result = ss.insert_data_to_sql_server(table_name='PackingPlan', dataframe=df)
    show_notification("Lỗi:", result)
    
    if result[0]:
        st.session_state.pop('ke_hoach_packing', None)  # Xóa cache
        st.rerun()
