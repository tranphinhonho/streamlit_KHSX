import streamlit as st
from admin.sys_kde_components import *
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

def app(selected):
    
    # Thông tin 7 máy ép viên
    MACHINES = {
        'Pellet 1': 10,  # tấn/giờ
        'Pellet 2': 10,
        'Pellet 3': 9,
        'Pellet 4': 9,
        'Pellet 5': 8,
        'Pellet 6': 8,
        'Pellet 7': 8
    }
    
    MAX_HOURS = 24  # Giới hạn 24 giờ/ngày
    
    # Tạo tabs
    tab1, tab2, tab3 = st.tabs([
        "🤖 Phân bổ tự động", 
        "✍️ Nhập thủ công",
        "📋 Danh sách Pellet"
    ])
    
    # TAB 1: Phân bổ tự động
    with tab1:
        st.header("🤖 Phân bổ Pellet tự động")
        
        # Chọn ngày
        col1, col2 = st.columns(2)
        with col1:
            ngay_sx = st.date_input(
                "Ngày sản xuất", 
                value=fn.get_vietnam_time().date(),
                help="Chọn ngày cần phân bổ sản xuất Pellet"
            )
        
        with col2:
            st.metric("Tổng công suất", "62 tấn/giờ", help="7 máy: 10+10+9+9+8+8+8 tấn/giờ")
        
        if st.button("🔄 Phân bổ tự động", type="primary", use_container_width=True):
            with st.spinner("Đang tính toán phân bổ..."):
                phan_bo = tinh_toan_phan_bo_pellet(ngay_sx)
                
                if phan_bo:
                    st.session_state['phan_bo_pellet'] = phan_bo
                    st.success(f"✅ Đã phân bổ xong! Tổng: {phan_bo['tong_san_luong']:.1f} tấn")
                else:
                    st.warning("⚠️ Không có kế hoạch cho ngày này")
        
        # Hiển thị kế hoạch đã tính
        if 'phan_bo_pellet' in st.session_state and st.session_state['phan_bo_pellet']:
            hien_thi_phan_bo(st.session_state['phan_bo_pellet'], ngay_sx, MACHINES)
    
    # TAB 2: Nhập thủ công
    with tab2:
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
                options=list(MACHINES.keys()), 
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
            
            # Tính thời gian chạy
            df_insert['Công suất máy (tấn/giờ)'] = df_insert['Số máy'].map(MACHINES)
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
    
    # TAB 3: Danh sách Pellet
    with tab3:
        st.header("📋 Danh sách Pellet hiện tại")
        
        column_config = {
            'Ngày sản xuất': st.column_config.DateColumn('Ngày sản xuất', format='DD/MM/YYYY'),
            'Thời gian bắt đầu': st.column_config.DatetimeColumn('Thời gian bắt đầu', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian kết thúc': st.column_config.DatetimeColumn('Thời gian kết thúc', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss')
        }
        
        dataframe_with_selections(
            table_name="Pellet",
            columns=[
                'ID', 'Ngày sản xuất', 'ID sản phẩm', 'Số lượng', 'Số máy',
                'Thời gian bắt đầu', 'Thời gian kết thúc', 'Thời gian chạy (giờ)',
                'Công suất máy (tấn/giờ)', 'Ghi chú', 'Người tạo', 'Thời gian tạo'
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


def tinh_toan_phan_bo_pellet(ngay_sx):
    """
    Tính toán phân bổ tự động cho 7 máy Pellet
    Dựa trên kế hoạch Plan của ngày đó
    """
    conn = sqlite3.connect('database_new.db')
    
    # Lấy kế hoạch từ bảng Plan
    query = """
    SELECT 
        p.ID,
        p.[Mã plan],
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
    
    # Thuật toán phân bổ: Load Balancing
    # Sắp xếp máy theo công suất giảm dần
    machines = {
        'Pellet 1': {'capacity': 10, 'hours_used': 0, 'jobs': []},
        'Pellet 2': {'capacity': 10, 'hours_used': 0, 'jobs': []},
        'Pellet 3': {'capacity': 9, 'hours_used': 0, 'jobs': []},
        'Pellet 4': {'capacity': 9, 'hours_used': 0, 'jobs': []},
        'Pellet 5': {'capacity': 8, 'hours_used': 0, 'jobs': []},
        'Pellet 6': {'capacity': 8, 'hours_used': 0, 'jobs': []},
        'Pellet 7': {'capacity': 8, 'hours_used': 0, 'jobs': []}
    }
    
    # Phân bổ từng công việc
    phan_bo = []
    for _, job in df.iterrows():
        so_luong = job['Số lượng']
        
        # Tìm máy có thời gian chạy ít nhất
        best_machine = min(machines.items(), key=lambda x: x[1]['hours_used'])
        machine_name = best_machine[0]
        machine_info = best_machine[1]
        
        # Tính thời gian cần thiết
        hours_needed = so_luong / machine_info['capacity']
        
        # Kiểm tra giới hạn 24 giờ
        if machine_info['hours_used'] + hours_needed > 24:
            # Nếu vượt quá, tìm máy khác hoặc chia nhỏ công việc
            remaining = so_luong
            while remaining > 0:
                # Tìm máy có thời gian trống
                available_machine = min(
                    ((name, info) for name, info in machines.items() if info['hours_used'] < 24),
                    key=lambda x: x[1]['hours_used'],
                    default=None
                )
                
                if not available_machine:
                    break  # Không còn máy trống
                
                m_name, m_info = available_machine
                available_hours = 24 - m_info['hours_used']
                can_produce = available_hours * m_info['capacity']
                
                assign_quantity = min(remaining, can_produce)
                assign_hours = assign_quantity / m_info['capacity']
                
                phan_bo.append({
                    'ID Kế hoạch': job['ID'],
                    'Mã plan': job['Mã plan'],
                    'Tên sản phẩm': job['Tên sản phẩm'],
                    'Số lượng': assign_quantity,
                    'Số máy': m_name,
                    'Công suất máy (tấn/giờ)': m_info['capacity'],
                    'Thời gian chạy (giờ)': round(assign_hours, 2)
                })
                
                m_info['hours_used'] += assign_hours
                m_info['jobs'].append(job['Tên sản phẩm'])
                remaining -= assign_quantity
        else:
            # Phân bổ bình thường
            phan_bo.append({
                'ID Kế hoạch': job['ID'],
                'Mã plan': job['Mã plan'],
                'Tên sản phẩm': job['Tên sản phẩm'],
                'Số lượng': so_luong,
                'Số máy': machine_name,
                'Công suất máy (tấn/giờ)': machine_info['capacity'],
                'Thời gian chạy (giờ)': round(hours_needed, 2)
            })
            
            machine_info['hours_used'] += hours_needed
            machine_info['jobs'].append(job['Tên sản phẩm'])
    
    tong_san_luong = sum(item['Số lượng'] for item in phan_bo)
    
    return {
        'phan_bo': phan_bo,
        'machines': machines,
        'tong_san_luong': tong_san_luong
    }


def hien_thi_phan_bo(data, ngay_sx, MACHINES):
    """Hiển thị kết quả phân bổ"""
    
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
    
    # Hiển thị từng máy
    for machine_name, machine_info in data['machines'].items():
        if machine_info['hours_used'] > 0:
            with st.expander(f"🔧 {machine_name} - {machine_info['capacity']} tấn/giờ", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Danh sách công việc
                    machine_jobs = [job for job in data['phan_bo'] if job['Số máy'] == machine_name]
                    df_jobs = pd.DataFrame(machine_jobs)
                    st.dataframe(df_jobs, use_container_width=True, hide_index=True)
                
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
    if st.button("💾 Lưu phân bổ vào Database", type="primary", use_container_width=True):
        luu_phan_bo(data['phan_bo'], ngay_sx)


def luu_phan_bo(phan_bo, ngay_sx):
    """Lưu phân bổ vào database"""
    df = pd.DataFrame(phan_bo)
    df['Ngày sản xuất'] = ngay_sx
    df['Người tạo'] = st.session_state.username
    df['Thời gian tạo'] = fn.get_vietnam_time()
    
    # Tính thời gian bắt đầu và kết thúc (giả định bắt đầu từ 7:00)
    start_time = datetime.combine(ngay_sx, datetime.min.time()).replace(hour=7)
    
    for idx, row in df.iterrows():
        df.at[idx, 'Thời gian bắt đầu'] = start_time
        df.at[idx, 'Thời gian kết thúc'] = start_time + timedelta(hours=row['Thời gian chạy (giờ)'])
        start_time = df.at[idx, 'Thời gian kết thúc']  # Máy tiếp theo bắt đầu sau máy trước
    
    result = ss.insert_data_to_sql_server(table_name='Pellet', dataframe=df)
    show_notification("Lỗi:", result)
    
    if result[0]:
        st.session_state.pop('phan_bo_pellet', None)  # Xóa cache
        st.rerun()
