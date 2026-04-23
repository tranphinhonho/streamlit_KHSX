import streamlit as st
from admin.sys_kde_components import *

def app(selected):
    """
    Trang chọn sản phẩm từ Stock và chuyển sang Plan
    - Chỉ hiển thị bảng stock với checkbox và form chuyển Plan
    - Không có các section khác để tối đa không gian làm việc
    """
    
    st.header("📋 Chọn Stock → Plan", divider='rainbow')
    
    # Khởi tạo session state
    if 'df_key' not in st.session_state:
        st.session_state.df_key = 0
    if 'selected_stock_day_plan' not in st.session_state:
        st.session_state.selected_stock_day_plan = fn.get_vietnam_time().date().day
    if 'selected_animal_filter_plan' not in st.session_state:
        st.session_state.selected_animal_filter_plan = None
        
    # === IMPORTS ===
    import sqlite3
    import calendar
    from datetime import timedelta
    
    conn = ss.connect_db()
    cursor = conn.cursor()
    
    # Lấy năm và tháng hiện tại
    current_date = fn.get_vietnam_time().date()
    current_year = current_date.year
    current_month = current_date.month
    
    # Lấy các ngày có stock trong tháng hiện tại
    cursor.execute("""
        SELECT DISTINCT CAST(strftime('%d', [Ngày stock]) AS INTEGER) as day
        FROM StockHomNay
        WHERE strftime('%Y-%m', [Ngày stock]) = ?
        AND [Đã xóa] = 0
        ORDER BY day
    """, (f"{current_year}-{current_month:02d}",))
    days_with_stock = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Kiểm tra xem có items đang được chọn không (để quyết định thu gọn hay không)
    selection_key_check = f"dws_selection_state_ChonStockPlan_{st.session_state.df_key}_{st.session_state.selected_stock_day_plan}_{st.session_state.selected_animal_filter_plan}"
    has_selected_items = selection_key_check in st.session_state and len(st.session_state.get(selection_key_check, set())) > 0
    
    # Xác định selected_date và col_where trước
    if st.session_state.selected_stock_day_plan:
        selected_date = f"{current_year}-{current_month:02d}-{st.session_state.selected_stock_day_plan:02d}"
        col_where = {'Đã xóa': ('=', 0), 'Ngày stock': ('=', selected_date)}
    else:
        col_where = {'Đã xóa': ('=', 0)}
    
    # Animal mapping
    animal_mapping = {
        'TẤT CẢ': None,
        'HEO': 'H',
        'GÀ': 'G', 
        'BÒ': 'B',
        'VỊT': 'V',
        'CÚT': 'C',
        'DÊ': 'D'
    }
    
    # === FILTER SECTION - Thu gọn khi có items được chọn ===
    if has_selected_items:
        # Hiển thị thông tin ngắn gọn và expander để mở rộng
        selected_animal_name = [k for k, v in animal_mapping.items() if v == st.session_state.selected_animal_filter_plan]
        animal_display = selected_animal_name[0] if selected_animal_name else 'TẤT CẢ'
        
        st.info(f"📆 **Ngày {st.session_state.selected_stock_day_plan:02d}/{current_month:02d}/{current_year}** | 🐾 **{animal_display}** | ✅ **Đang chọn sản phẩm** (nhấn để thay đổi bộ lọc ↓)")
        
        with st.expander("📅 Thay đổi ngày / Bộ lọc vật nuôi", expanded=False):
            # Date picker
            st.markdown(f"**📅 Tháng {current_month}/{current_year}** - 🟢 Đã có stock | 🟠 Chưa có stock")
            num_days = calendar.monthrange(current_year, current_month)[1]
            days_per_row = 16
            
            for row_start in range(1, num_days + 1, days_per_row):
                row_end = min(row_start + days_per_row - 1, num_days)
                cols = st.columns(days_per_row)
                for col_idx, day in enumerate(range(row_start, row_end + 1)):
                    with cols[col_idx]:
                        is_selected = st.session_state.selected_stock_day_plan == day
                        if is_selected:
                            btn_type = "primary"
                        elif day in days_with_stock:
                            btn_type = "primary"
                        else:
                            btn_type = "secondary"
                            
                        if st.button(
                            f"{'✓ ' if is_selected else ''}{day}", 
                            key=f"plan_day_btn_{day}",
                            type=btn_type if day in days_with_stock else "secondary",
                            width="stretch"
                        ):
                            st.session_state.selected_stock_day_plan = day
                            st.rerun()
            
            # Animal filter
            st.markdown("**🐾 Lọc theo vật nuôi:**")
            animal_types = ['TẤT CẢ', 'HEO', 'GÀ', 'BÒ', 'VỊT', 'CÚT', 'DÊ']
            animal_cols = st.columns(len(animal_types))
            
            for idx, animal in enumerate(animal_types):
                with animal_cols[idx]:
                    is_selected = (animal == 'TẤT CẢ' and st.session_state.selected_animal_filter_plan is None) or \
                                  (st.session_state.selected_animal_filter_plan == animal_mapping.get(animal))
                    btn_label = f"{'✓ ' if is_selected else ''}{animal}"
                    
                    if st.button(btn_label, key=f"plan_animal_btn_{animal}", width="stretch",
                                type="primary" if is_selected else "secondary"):
                        if animal == 'TẤT CẢ':
                            st.session_state.selected_animal_filter_plan = None
                        else:
                            st.session_state.selected_animal_filter_plan = animal_mapping.get(animal)
                        st.rerun()
    else:
        # Hiển thị đầy đủ khi chưa chọn items
        st.markdown(f"**📅 Tháng {current_month}/{current_year}** - 🟢 Đã có stock | 🟠 Chưa có stock")
        
        num_days = calendar.monthrange(current_year, current_month)[1]
        days_per_row = 16
        
        for row_start in range(1, num_days + 1, days_per_row):
            row_end = min(row_start + days_per_row - 1, num_days)
            cols = st.columns(days_per_row)
            for col_idx, day in enumerate(range(row_start, row_end + 1)):
                with cols[col_idx]:
                    is_selected = st.session_state.selected_stock_day_plan == day
                    if is_selected:
                        btn_type = "primary"
                    elif day in days_with_stock:
                        btn_type = "primary"
                    else:
                        btn_type = "secondary"
                        
                    if st.button(
                        f"{'✓ ' if is_selected else ''}{day}", 
                        key=f"plan_day_btn_{day}",
                        type=btn_type if day in days_with_stock else "secondary",
                        width="stretch"
                    ):
                        st.session_state.selected_stock_day_plan = day
                        st.rerun()
        
        # Hiển thị ngày đang chọn
        if st.session_state.selected_stock_day_plan:
            st.info(f"📆 Stock đầu ngày: **{st.session_state.selected_stock_day_plan:02d}/{current_month:02d}/{current_year}**")
        
        # === BỘ LỌC VẬT NUÔI ===
        st.markdown("**🐾 Lọc theo vật nuôi:**")
        animal_types = ['TẤT CẢ', 'HEO', 'GÀ', 'BÒ', 'VỊT', 'CÚT', 'DÊ']
        animal_cols = st.columns(len(animal_types))
        
        for idx, animal in enumerate(animal_types):
            with animal_cols[idx]:
                is_selected = (animal == 'TẤT CẢ' and st.session_state.selected_animal_filter_plan is None) or \
                              (st.session_state.selected_animal_filter_plan == animal_mapping.get(animal))
                btn_label = f"{'✓ ' if is_selected else ''}{animal}"
                
                if st.button(btn_label, key=f"plan_animal_btn_{animal}", width="stretch",
                            type="primary" if is_selected else "secondary"):
                    if animal == 'TẤT CẢ':
                        st.session_state.selected_animal_filter_plan = None
                    else:
                        st.session_state.selected_animal_filter_plan = animal_mapping.get(animal)
                    st.rerun()
    
    # Thêm điều kiện lọc vật nuôi vào col_where
    joins_config = [
        {
            "table": "SanPham",
            "alias": "p",
            "on": {"ID sản phẩm": "ID"},
            "columns": ["Vật nuôi"]
        }
    ]
    
    if st.session_state.selected_animal_filter_plan:
        col_where['p.[Vật nuôi]'] = ('=', st.session_state.selected_animal_filter_plan)
    
    # Column config
    column_config = {
        'ID sản phẩm': st.column_config.TextColumn(width="medium"),
        'Số lượng': st.column_config.NumberColumn(width="small", format="%d"),
        'Ghi chú 2': st.column_config.TextColumn(width="large"),
        'Kết quả GC2': st.column_config.NumberColumn(width="small", format="%d"),
        'Aver': st.column_config.NumberColumn(width="small", format="%d"),
        'DOH': st.column_config.NumberColumn(width="small", format="%.1f"),
        'Plan': st.column_config.NumberColumn(width="small", format="%d"),
        'Day5': st.column_config.NumberColumn(width="small", format="%d"),
        'Vật nuôi': st.column_config.TextColumn(width="small")
    }
    
    # Post-process function để tính thêm các cột
    def format_numeric_columns(df):
        if df.empty:
            return df
            
        # Parse Ghi chú 2 để lấy Kết quả GC2
        if 'Ghi chú 2' in df.columns and 'Kết quả GC2' not in df.columns:
            import re
            def extract_gc2_result(gc2_text):
                if not gc2_text or pd.isna(gc2_text):
                    return 0
                gc2_str = str(gc2_text)
                match = re.search(r'=(-?[\d,]+(?:\.\d+)?)\s*$', gc2_str)
                if match:
                    try:
                        return int(float(match.group(1).replace(',', '')))
                    except:
                        return 0
                return 0
            df['Kết quả GC2'] = df['Ghi chú 2'].apply(extract_gc2_result)
        
        # Đảm bảo Kết quả GC2 là số nguyên
        if 'Kết quả GC2' in df.columns:
            df['Kết quả GC2'] = pd.to_numeric(df['Kết quả GC2'], errors='coerce').fillna(0).astype(int)
        
        # Tính Aver, DOH, Plan, Day5
        if 'ID sản phẩm' in df.columns:
            import sqlite3
            from datetime import datetime, timedelta
            
            conn = ss.connect_db()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            five_days_ago = today - timedelta(days=5)
            
            # Lấy tất cả ID sản phẩm
            all_ids = df['ID sản phẩm'].apply(lambda x: int(str(x).split('|')[0].strip()) if '|' in str(x) else int(x) if str(x).isdigit() else None).dropna().unique().tolist()
            
            if all_ids:
                placeholders = ','.join(['?' for _ in all_ids])
                
                # Tính Aver
                cursor.execute(f"""
                    SELECT [ID sản phẩm], SUM([Số lượng]) as total, COUNT(DISTINCT [Ngày sale]) as days
                    FROM Sale WHERE [ID sản phẩm] IN ({placeholders}) AND [Đã xóa] = 0
                    GROUP BY [ID sản phẩm]
                """, all_ids)
                aver_data = cursor.fetchall()
                aver_dict = {row[0]: int(row[1] / row[2]) if row[2] > 0 else 0 for row in aver_data}
                
                # Tính Day5
                cursor.execute(f"""
                    SELECT [ID sản phẩm], SUM([Số lượng]) as total
                    FROM Packing
                    WHERE [ID sản phẩm] IN ({placeholders})
                    AND [Đã xóa] = 0
                    AND [Ngày packing] >= ?
                    GROUP BY [ID sản phẩm]
                """, all_ids + [five_days_ago.strftime('%Y-%m-%d')])
                day5_data = cursor.fetchall()
                day5_dict = {row[0]: int(row[1]) for row in day5_data}
                
                # Lấy batch size
                cursor.execute(f"SELECT ID, [Batch size] FROM SanPham WHERE ID IN ({placeholders})", all_ids)
                batch_size_dict = {row[0]: row[1] or 2800 for row in cursor.fetchall()}
            else:
                aver_dict = {}
                day5_dict = {}
                batch_size_dict = {}
            
            conn.close()
            
            def extract_pid(id_sanpham):
                id_str = str(id_sanpham)
                if '|' in id_str:
                    try:
                        return int(id_str.split('|')[0].strip())
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
            
            # Tính DOH
            df['DOH'] = df.apply(
                lambda row: round(row['Số lượng'] / row['Aver'], 1) if row['Aver'] > 0 else 0.0,
                axis=1
            )
            
            # Tính Plan
            def calculate_plan(row):
                aver = row['Aver']
                kq = row.get('Kết quả GC2', 0)
                batch_size = get_batch_size(row['ID sản phẩm'])
                
                if kq >= 0:
                    return 0
                
                plan_raw = min(aver * 3, abs(kq))
                
                if plan_raw <= 0 or batch_size <= 0:
                    return 0
                
                import math
                plan_rounded = math.ceil(plan_raw / batch_size) * batch_size
                return int(plan_rounded)
            
            df['Plan'] = df.apply(calculate_plan, axis=1)
            
            # Tính Day5
            def calculate_day5(row):
                stock = row['Số lượng']
                packing_5days = get_day5(row['ID sản phẩm'])
                return min(stock, packing_5days)
            
            df['Day5'] = df.apply(calculate_day5, axis=1).astype(int)
        
        # Sắp xếp theo Vật nuôi: H → G → V → B → C → D
        if 'Vật nuôi' in df.columns:
            pet_order = {'H': 1, 'G': 2, 'V': 3, 'B': 4, 'C': 5, 'D': 6}
            df['_pet_order'] = df['Vật nuôi'].map(pet_order).fillna(99)
            df = df.sort_values(['_pet_order', 'Kết quả GC2'] if 'Kết quả GC2' in df.columns else ['_pet_order'])
            df = df.drop(columns=['_pet_order'])
        
        return df
    
    # Output columns for the table
    output_columns = ['ID', 'ID sản phẩm', 'Số lượng', 'Ghi chú 2', 'Kết quả GC2', 'Aver', 'DOH', 'Plan', 'Day5', 'Vật nuôi']
    
    st.markdown("---")
    
    # Hiển thị bảng với selection
    dataframe_with_selections(
        table_name="StockHomNay",
        columns=[
            'ID sản phẩm', 'Số lượng', 'Ghi chú', 'Ghi chú 2', 'Kết quả GC2', 'Ngày stock', 'ID',
            'Người tạo'
        ],
        output_columns=output_columns,
        colums_disable=['ID', 'Người tạo', 'Kết quả GC2', 'Aver', 'DOH'],
        col_where=col_where,
        col_order={'Kết quả GC2': 'ASC'},
        joins=joins_config,
        column_config=column_config,
        key=f'ChonStockPlan_{st.session_state.df_key}_{st.session_state.selected_stock_day_plan}_{st.session_state.selected_animal_filter_plan}',
        join_user_info=False,
        post_process_func=format_numeric_columns,
        return_selected_rows=True,
        add_select=True)
    
    # === XỬ LÝ CHỌN SẢN PHẨM VÀ CHUYỂN PLAN ===
    selection_key = f"dws_selection_state_ChonStockPlan_{st.session_state.df_key}_{st.session_state.selected_stock_day_plan}_{st.session_state.selected_animal_filter_plan}"
    
    if selection_key in st.session_state and st.session_state[selection_key]:
        selected_ids = list(st.session_state[selection_key])
        
        if len(selected_ids) > 0:
            st.markdown("---")
            st.subheader("📤 Chuyển sang Plan")
            
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
                    kq_gc2 = row[6] or 0
                    
                    # Tính Aver
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0), COUNT(DISTINCT [Ngày sale])
                        FROM Sale WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                    """, (id_sanpham,))
                    sale_result = cursor.fetchone()
                    total_sale = sale_result[0] if sale_result and sale_result[0] else 0
                    num_days = sale_result[1] if sale_result and sale_result[1] else 0
                    aver = total_sale / num_days if num_days > 0 else 0
                    
                    # Tính Plan
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
                
                ngay_plan = fn.get_vietnam_time().date()
                
                # Khởi tạo session state
                if 'stock_to_plan_qty_2' not in st.session_state:
                    st.session_state.stock_to_plan_qty_2 = {}
                
                if 'plan_initialized_ids_2' not in st.session_state:
                    st.session_state.plan_initialized_ids_2 = set()
                
                # Cập nhật giá trị mặc định
                need_rerun = False
                for item in plan_data:
                    if item['stock_id'] not in st.session_state.plan_initialized_ids_2:
                        st.session_state.stock_to_plan_qty_2[item['stock_id']] = item['plan_value']
                        st.session_state.plan_initialized_ids_2.add(item['stock_id'])
                        need_rerun = True
                
                if need_rerun:
                    st.rerun()
                
                # Header
                col_header = st.columns([2, 3, 2, 2])
                col_header[0].markdown("**Code cám**")
                col_header[1].markdown("**Tên cám**")
                col_header[2].markdown("**Tồn kho (kg)**")
                col_header[3].markdown("**SL sản xuất (kg)**")
                
                # Rows
                for item in plan_data:
                    col_row = st.columns([2, 3, 2, 2])
                    col_row[0].write(item['code_cam'])
                    col_row[1].write(item['ten_cam'])
                    col_row[2].write(f"{item['stock_qty']:,.0f}")
                    
                    qty_key = f"plan_qty_2_{item['stock_id']}"
                    default_value = st.session_state.stock_to_plan_qty_2.get(item['stock_id'], item['plan_value'])
                    qty = col_row[3].number_input(
                        "SL",
                        min_value=0,
                        value=default_value,
                        step=1000,
                        key=qty_key,
                        label_visibility="collapsed"
                    )
                    st.session_state.stock_to_plan_qty_2[item['stock_id']] = qty
                
                # Buttons
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📤 Gửi qua Plan", type="primary", key="btn_send_to_plan_stock_2"):
                        transfer_data = []
                        for item in plan_data:
                            qty = st.session_state.stock_to_plan_qty_2.get(item['stock_id'], 0)
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
                                'source': f'Chọn Stock Plan - {st.session_state.selected_stock_day_plan}',
                                'ngay_lay': ngay_plan.strftime('%Y-%m-%d'),
                                'sheet': ''
                            }
                            st.success(f"✅ Đã gửi **{len(transfer_data)}** sản phẩm sang Plan!")
                            st.info("👉 Vào **Plan > Nhập kế hoạch thủ công** để xem và lưu.")
                            
                            st.session_state.stock_to_plan_qty_2 = {}
                        else:
                            st.warning("⚠️ Chưa nhập số lượng cho sản phẩm nào!")
                
                with col_btn2:
                    if st.button("❌ Hủy chọn", key="btn_cancel_plan_stock_2"):
                        st.session_state[selection_key] = set()
                        st.session_state.stock_to_plan_qty_2 = {}
                        st.rerun()
