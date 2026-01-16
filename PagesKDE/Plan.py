import streamlit as st
from admin.sys_kde_components import *
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

def process_import_plan(df):
    """Xử lý import Excel cho kế hoạch - tự động tìm ID sản phẩm từ tên"""
    if 'Tên sản phẩm' not in df.columns:
        st.error("❌ File Excel phải có cột 'Tên sản phẩm'")
        return None
    
    if 'Số lượng' not in df.columns:
        st.error("❌ File Excel phải có cột 'Số lượng'")
        return None
    
    conn = sqlite3.connect('database_new.db')
    result_data = []
    not_found = []
    
    for idx, row in df.iterrows():
        ten_sanpham = str(row['Tên sản phẩm']).strip()
        so_luong = row['Số lượng']
        
        cursor = conn.cursor()
        cursor.execute("SELECT ID, [Code cám], [Tên cám] FROM SanPham WHERE [Tên cám] = ? AND [Đã xóa] = 0", (ten_sanpham,))
        result = cursor.fetchone()
        
        if result:
            id_sanpham, code_cam, ten_cam = result
            item = {
                'ID sản phẩm': id_sanpham,
                'Số lượng': so_luong,
                'Ngày plan': row.get('Ngày plan (tùy chọn)', row.get('Ngày plan', None)),
                'Ghi chú': row.get('Ghi chú (tùy chọn)', row.get('Ghi chú', None)),
                'Code cám được tạo': code_cam,
                'Tên sản phẩm': ten_cam
            }
            result_data.append(item)
        else:
            not_found.append(ten_sanpham)
    
    conn.close()
    
    if not_found:
        st.warning(f"⚠️ Không tìm thấy {len(not_found)} sản phẩm: {', '.join(not_found)}")
    
    if result_data:
        df_result = pd.DataFrame(result_data)
        maplan = ss.generate_next_code(tablename='Plan', column_name='Mã plan', prefix='PL', num_char=5)
        df_result['Mã plan'] = maplan
        df_result['Người tạo'] = st.session_state.username
        df_result['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.success(f"✅ Đã xử lý thành công {len(result_data)} sản phẩm với mã: **{maplan}**")
        
        with st.expander("📋 Xem trước dữ liệu được import"):
            display_cols = ['Tên sản phẩm', 'Code cám được tạo', 'Số lượng', 'Ngày plan', 'Ghi chú']
            preview_df = df_result[display_cols].copy()
            st.dataframe(preview_df, width='stretch')
        
        db_cols = ['ID sản phẩm', 'Số lượng', 'Ngày plan', 'Ghi chú', 'Mã plan', 'Người tạo', 'Thời gian tạo']
        return df_result[db_cols]
    
    return None

def app(selected):
    tab1, tab2, tab3 = st.tabs(["📊 Tổng hợp kế hoạch", "✍️ Nhập kế hoạch thủ công", "📋 Danh sách plan"])
    
    with tab1:
        st.header("📊 Tổng hợp Kế hoạch Sản xuất")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            ngay_ke_hoach = st.date_input("Ngày kế hoạch", value=fn.get_vietnam_time().date() + timedelta(days=1))
        with col2:
            khong_sx_chunhat = st.checkbox("✅ Không sản xuất Chủ nhật/Ngày lễ", value=True)
        with col3:
            st.metric("Công suất tối thiểu", "2,100,000 Kg")
        
        ngay_ke_hoach_goc = ngay_ke_hoach
        if khong_sx_chunhat:
            while ngay_ke_hoach.weekday() == 6:
                ngay_ke_hoach = ngay_ke_hoach + timedelta(days=1)
            if ngay_ke_hoach != ngay_ke_hoach_goc:
                st.warning(f"⚠️ Ngày {ngay_ke_hoach_goc.strftime('%d/%m/%Y')} là Chủ nhật. Đã chuyển sang Thứ 2 ngày {ngay_ke_hoach.strftime('%d/%m/%Y')}")
        
        if st.button("🔄 Tính toán Kế hoạch", type="primary", use_container_width=True):
            with st.spinner("Đang tính toán kế hoạch..."):
                ke_hoach = tinh_toan_ke_hoach(ngay_ke_hoach)
                if ke_hoach:
                    st.session_state['ke_hoach_data'] = ke_hoach
                    st.success(f"✅ Đã tính toán xong! Chọn {ke_hoach['so_san_pham']} sản phẩm - Tổng: {ke_hoach['tong_san_luong']:,.0f} Kg")
                else:
                    st.warning("⚠️ Không có dữ liệu để lên kế hoạch")
        
        if 'ke_hoach_data' in st.session_state and st.session_state['ke_hoach_data']:
            hien_thi_ke_hoach(st.session_state['ke_hoach_data'], ngay_ke_hoach)
    
    with tab2:
        st.header("✍️ Nhập kế hoạch thủ công")
        subtab1, subtab2 = st.tabs(["✍️ Nhập tay", "📁 Import Excel"])
        
        with subtab1:
            ds_sanpham = ss.get_columns_data(table_name='SanPham', columns=['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên', 'ID'], data_type='list', col_where={'Đã xóa':('=',0)})
            data = {'ID sản phẩm': [None], 'Số lượng': [0], 'Ngày plan': [None], 'Ghi chú': [None]}
            df = pd.DataFrame(data)
            column_config = {
                'ID sản phẩm': st.column_config.SelectboxColumn('ID sản phẩm',options=ds_sanpham,format_func=lambda x: x,width='large'),
                'Số lượng': st.column_config.NumberColumn('Số lượng',min_value=0,step=1,format="%d",width='small'),
                'Ngày plan': st.column_config.DateColumn('Ngày plan', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='plan_manual')
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            maplan = ss.generate_next_code(tablename='Plan', column_name='Mã plan', prefix='PL',num_char=5)
            st.write(f'Mã plan tự động: **{maplan}**')
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã plan'] = maplan
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            st.dataframe(df_insert, width='content')
            disabled = not (len(df_insert) > 0)
            if st.button("Thêm kế hoạch", disabled=disabled, type="primary", key='btn_add_manual'):
                result = ss.insert_data_to_sql_server(table_name='Plan',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        with subtab2:
            st.info("📋 File Excel cần có các cột: **Tên sản phẩm**, **Số lượng**, **Ngày plan** (tùy chọn), **Ghi chú** (tùy chọn)")
            sample_data = {'Tên sản phẩm': ['510KM', '511ANF', '512BM'], 'Số lượng': [120000, 85000, 50000], 'Ngày plan (tùy chọn)': ['08/12/2025', '08/12/2025', '09/12/2025'], 'Ghi chú (tùy chọn)': ['', '', 'Ưu tiên cao']}
            sample_df = pd.DataFrame(sample_data)
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                sample_df.to_excel(writer, index=False, sheet_name='Mẫu kế hoạch')
            excel_data = output.getvalue()
            col1, col2 = st.columns([1, 3])
            with col1:
                st.download_button(label="📥 Tải file mẫu", data=excel_data, file_name="mau_nhap_ke_hoach.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="secondary")
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_plan')
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                df_processed = process_import_plan(df)
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_plan'):
                        result = ss.insert_data_to_sql_server(table_name='Plan', dataframe=df_processed)
                        show_notification("Lỗi:", result)
    
    with tab3:
        st.header("📋 Danh sách plan hiện tại")
        column_config = {
            'Ngày plan': st.column_config.DateColumn('Ngày plan', format='DD/MM/YYYY'),
            'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
            'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss')
        }
        dataframe_with_selections(table_name="Plan", columns=['ID', 'ID sản phẩm', 'Mã plan', 'Số lượng', 'Ngày plan', 'Ghi chú', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'], colums_disable=['ID','Mã plan','Người tạo','Thời gian tạo','Người sửa','Thời gian sửa','Fullname'], col_where={'Đã xóa': ('=', 0)}, col_order={'ID': 'DESC'}, joins=[{'table': 'SanPham', 'on': {'ID sản phẩm': 'ID'}, 'columns': ['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên'], 'replace_multi':{'ID sản phẩm':['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên']}}], column_config=column_config, key=f'Plan_{st.session_state.df_key}', join_user_info=True)
        
        st.markdown("---")
        st.markdown("### 🗑️ Xóa kế hoạch theo ngày")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            ngay_xoa = st.date_input("Chọn ngày cần xóa", value=fn.get_vietnam_time().date(), help="Chọn ngày để xóa TẤT CẢ plan cho ngày đó", key="date_delete_plan")
        with col2:
            if st.button("🗑️ Xóa tất cả", type="secondary", key="btn_delete_all_plan"):
                conn = sqlite3.connect('database_new.db')
                cursor = conn.cursor()
                ngay_str = ngay_xoa.strftime('%Y-%m-%d')
                ngay_str_alt = ngay_xoa.strftime('%d/%m/%Y')
                cursor.execute("SELECT COUNT(*) FROM Plan WHERE ([Ngày plan] = ? OR [Ngày plan] = ?) AND [Đã xóa] = 0", (ngay_str, ngay_str_alt))
                count = cursor.fetchone()[0]
                conn.close()
                if count > 0:
                    st.session_state['confirm_delete_date'] = ngay_xoa
                    st.session_state['confirm_delete_count'] = count
                else:
                    st.warning(f"⚠️ Không có plan nào cho ngày {ngay_xoa.strftime('%d/%m/%Y')}")
        
        if 'confirm_delete_date' in st.session_state:
            ngay = st.session_state['confirm_delete_date']
            count = st.session_state['confirm_delete_count']
            st.error(f"⚠️ **XÁC NHẬN XÓA**\n\nBạn có chắc muốn xóa **{count} plan** cho ngày **{ngay.strftime('%d/%m/%Y')}**?\n\nHành động này KHÔNG thể hoàn tác!")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Xác nhận XÓA", type="primary", key="confirm_yes"):
                    conn = sqlite3.connect('database_new.db')
                    cursor = conn.cursor()
                    ngay_str = ngay.strftime('%Y-%m-%d')
                    ngay_str_alt = ngay.strftime('%d/%m/%Y')
                    cursor.execute("UPDATE Plan SET [Đã xóa] = 1, [Người sửa] = ?, [Thời gian sửa] = ? WHERE ([Ngày plan] = ? OR [Ngày plan] = ?) AND [Đã xóa] = 0", (st.session_state.username, fn.get_vietnam_time(), ngay_str, ngay_str_alt))
                    conn.commit()
                    deleted = cursor.rowcount
                    conn.close()
                    st.success(f"✅ Đã xóa {deleted} plan cho ngày {ngay.strftime('%d/%m/%Y')}")
                    del st.session_state['confirm_delete_date']
                    del st.session_state['confirm_delete_count']
                    st.rerun()
            with col_no:
                if st.button("❌ Hủy", key="confirm_no"):
                    del st.session_state['confirm_delete_date']
                    del st.session_state['confirm_delete_count']
                    st.rerun()

def tinh_toan_ke_hoach(ngay_ke_hoach):
    try:
        conn = sqlite3.connect('database_new.db')
        cursor = conn.cursor()
        ngay_str = ngay_ke_hoach.strftime('%Y-%m-%d')
        ngay_str_alt = ngay_ke_hoach.strftime('%d/%m/%Y')
        
        cursor.execute("""
            SELECT p.[ID sản phẩm], sp.[Code cám], sp.[Tên cám], p.[Số lượng], p.[Ghi chú], p.[Mã plan], COALESCE(sh.[Số lượng], 0) as stock
            FROM Plan p
            JOIN SanPham sp ON p.[ID sản phẩm] = sp.ID
            LEFT JOIN StockHomNay sh ON sp.ID = sh.[ID sản phẩm] AND sh.[Đã xóa] = 0
            WHERE (p.[Ngày plan] = ? OR p.[Ngày plan] = ?) AND p.[Đã xóa] = 0
            ORDER BY p.[ID] ASC
        """, (ngay_str, ngay_str_alt))
        
        manual_plans = cursor.fetchall()
        
        if manual_plans:
            danh_sach = []
            tong_san_luong = 0
            ma_plan_list = set()
            for row in manual_plans:
                id_sp, code, ten, so_luong, ghi_chu, ma_plan, stock = row
                danh_sach.append({'id_sanpham': id_sp, 'code': code, 'ten': ten, 'so_luong': so_luong, 'stock': stock, 'doh': 999, 'ghi_chu': ghi_chu if ghi_chu else 'Kế hoạch thủ công', 'uu_tien': 0, 'loai': 'Thủ công'})
                tong_san_luong += so_luong
                ma_plan_list.add(ma_plan)
            conn.close()
            return {'ngay': ngay_ke_hoach, 'danh_sach': danh_sach, 'tong_san_luong': tong_san_luong, 'so_san_pham': len(danh_sach), 'loai': 'manual', 'debug': {'ngay_str': ngay_str, 'ngay_str_alt': ngay_str_alt, 'manual_count': len(manual_plans), 'ma_plan': ', '.join(ma_plan_list)}}
        
        GIOI_HAN_CONG_SUAT = 2100000 * 1.05
        MAX_SAN_PHAM = 25
        danh_sach_uu_tien = []
        ngay_thu = ngay_ke_hoach.weekday()
        
        if ngay_thu < 5:
            cursor.execute("""
                SELECT sp.ID, sp.[Code cám], sp.[Tên cám], fc.[Số lượng], COALESCE(sh.[Số lượng], 0) as stock
                FROM SanPham sp
                JOIN (SELECT [ID sản phẩm], SUM([Số lượng]) as [Số lượng] FROM DatHang WHERE [Loại đặt hàng] = 'Forecast tuần' AND [Đã xóa] = 0 GROUP BY [ID sản phẩm]) fc ON sp.ID = fc.[ID sản phẩm]
                LEFT JOIN StockHomNay sh ON sp.ID = sh.[ID sản phẩm] AND sh.[Đã xóa] = 0
                WHERE sp.[Đã xóa] = 0 AND sp.[Kích cỡ đóng bao] = 50
            """)
            for row in cursor.fetchall():
                id_sp, code, ten, forecast_tuan, stock = row
                so_luong = forecast_tuan / 5
                forecast_ngay = forecast_tuan / 7
                doh = stock / forecast_ngay if forecast_ngay > 0 else 999
                ghi_chu = f"Bao 50kg - Chia đều 5 ngày (ngày {ngay_thu + 1}/5)" if ngay_thu != 4 else "Bao 50kg - Thứ 6: Kiểm tra và SX đủ Forecast"
                danh_sach_uu_tien.append({'id_sanpham': id_sp, 'code': code, 'ten': ten, 'so_luong': so_luong, 'stock': stock, 'doh': doh, 'ghi_chu': ghi_chu, 'uu_tien': 1, 'loai': 'Bao 50kg'})
        
        cursor.execute("SELECT dh.[ID sản phẩm], sp.[Code cám], sp.[Tên cám], SUM(dh.[Số lượng]) as tong, COALESCE(sh.[Số lượng], 0) as stock FROM DatHang dh JOIN SanPham sp ON dh.[ID sản phẩm] = sp.ID LEFT JOIN StockHomNay sh ON sp.ID = sh.[ID sản phẩm] AND sh.[Đã xóa] = 0 WHERE dh.[Loại đặt hàng] = 'Đại lý Bá Cang' AND dh.[Ngày lấy] = ? AND dh.[Đã xóa] = 0 GROUP BY dh.[ID sản phẩm], sp.[Code cám], sp.[Tên cám]", (ngay_str,))
        for row in cursor.fetchall():
            id_sp, code, ten, so_luong, stock = row
            danh_sach_uu_tien.append({'id_sanpham': id_sp, 'code': code, 'ten': ten, 'so_luong': so_luong, 'stock': stock, 'doh': 0, 'ghi_chu': 'Đơn Bá Cang - SX hôm nay → Giao ngày mai', 'uu_tien': 2, 'loai': 'Đơn hàng'})
        
        cursor.execute("SELECT dh.[ID sản phẩm], sp.[Code cám], sp.[Tên cám], SUM(dh.[Số lượng]) as tong, COALESCE(sh.[Số lượng], 0) as stock FROM DatHang dh JOIN SanPham sp ON dh.[ID sản phẩm] = sp.ID LEFT JOIN StockHomNay sh ON sp.ID = sh.[ID sản phẩm] AND sh.[Đã xóa] = 0 WHERE dh.[Loại đặt hàng] = 'Xe bồn Silo' AND dh.[Ngày lấy] = ? AND dh.[Đã xóa] = 0 GROUP BY dh.[ID sản phẩm], sp.[Code cám], sp.[Tên cám]", (ngay_str,))
        for row in cursor.fetchall():
            id_sp, code, ten, so_luong, stock = row
            danh_sach_uu_tien.append({'id_sanpham': id_sp, 'code': code, 'ten': ten, 'so_luong': so_luong, 'stock': stock, 'doh': 0, 'ghi_chu': 'Đơn Xe Silo - SX → Chứa Silo → Xe lấy ngày mai', 'uu_tien': 2, 'loai': 'Đơn hàng'})
        
        cursor.execute("SELECT sp.ID, sp.[Code cám], sp.[Tên cám], COALESCE(sh.[Số lượng], 0) as stock, COALESCE(fc.[Số lượng], 0) as forecast FROM SanPham sp LEFT JOIN StockHomNay sh ON sp.ID = sh.[ID sản phẩm] AND sh.[Đã xóa] = 0 LEFT JOIN (SELECT [ID sản phẩm], SUM([Số lượng]) as [Số lượng] FROM DatHang WHERE [Loại đặt hàng] = 'Forecast tuần' AND [Đã xóa] = 0 GROUP BY [ID sản phẩm]) fc ON sp.ID = fc.[ID sản phẩm] WHERE sp.[Đã xóa] = 0")
        for row in cursor.fetchall():
            id_sp, code, ten, stock, forecast = row
            if forecast > 0:
                forecast_ngay = forecast / 7
                doh = stock / forecast_ngay if forecast_ngay > 0 else 999
                if doh < 3:
                    if forecast < 50000:
                        so_luong_sx = forecast
                        ghi_chu = f"DoH={doh:.1f}, Forecast<50tấn → Chạy 1 lần"
                    else:
                        so_luong_sx = forecast_ngay * 3
                        ghi_chu = f"DoH={doh:.1f} → SX 3 ngày"
                    danh_sach_uu_tien.append({'id_sanpham': id_sp, 'code': code, 'ten': ten, 'so_luong': so_luong_sx, 'stock': stock, 'doh': doh, 'ghi_chu': ghi_chu, 'uu_tien': 3, 'loai': 'Forecast'})
        
        conn.close()
        danh_sach_uu_tien.sort(key=lambda x: (x['uu_tien'], x['doh'], -x['so_luong']))
        ke_hoach_final = []
        tong_san_luong = 0
        
        for item in danh_sach_uu_tien:
            if len(ke_hoach_final) >= MAX_SAN_PHAM or tong_san_luong >= GIOI_HAN_CONG_SUAT:
                break
            so_luong_them = item['so_luong']
            if tong_san_luong + so_luong_them > GIOI_HAN_CONG_SUAT:
                so_luong_them = GIOI_HAN_CONG_SUAT - tong_san_luong
                if so_luong_them < 1000:
                    break
                item['ghi_chu'] += f" (Điều chỉnh: {item['so_luong']:,.0f} → {so_luong_them:,.0f} Kg)"
                item['so_luong'] = so_luong_them
            ke_hoach_final.append(item)
            tong_san_luong += so_luong_them
        
        return {'ngay': ngay_ke_hoach, 'danh_sach': ke_hoach_final, 'tong_san_luong': tong_san_luong, 'so_san_pham': len(ke_hoach_final), 'loai': 'auto', 'debug': {'ngay_str': ngay_str, 'ngay_str_alt': ngay_str_alt, 'manual_count': 0}} if len(ke_hoach_final) > 0 else None
    except Exception as e:
        st.error(f"Lỗi: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None

def hien_thi_ke_hoach(ke_hoach, ngay):
    st.markdown("---")
    st.subheader(f"📅 Kế hoạch Sản xuất: {ngay.strftime('%d/%m/%Y')}")
    CONG_SUAT_TOI_DA = 2100000
    CONG_SUAT_CHO_PHEP = CONG_SUAT_TOI_DA * 1.05
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng sản lượng", f"{ke_hoach['tong_san_luong']:,.0f} Kg")
    with col2:
        ty_le = (ke_hoach['tong_san_luong'] / CONG_SUAT_TOI_DA) * 100
        if ty_le > 105:
            st.metric("Tỷ lệ công suất", f"{ty_le:.1f}%", delta="⚠️ Vượt quá giới hạn!", delta_color="inverse")
        elif ty_le > 100:
            st.metric("Tỷ lệ công suất", f"{ty_le:.1f}%", delta=f"+{ty_le-100:.1f}%", delta_color="inverse")
        else:
            st.metric("Tỷ lệ công suất", f"{ty_le:.1f}%")
    with col3:
        st.metric("Số sản phẩm", ke_hoach['so_san_pham'])
    
    if ke_hoach['tong_san_luong'] > CONG_SUAT_CHO_PHEP:
        vuot_qua = ke_hoach['tong_san_luong'] - CONG_SUAT_CHO_PHEP
        st.error(f"🚨 **VƯỢT CÔNG SUẤT CHO PHÉP!**\n\n- Tổng sản lượng: **{ke_hoach['tong_san_luong']:,.0f} Kg**\n- Giới hạn tối đa (105%): **{CONG_SUAT_CHO_PHEP:,.0f} Kg**\n- Vượt quá: **{vuot_qua:,.0f} Kg**")
    elif ke_hoach['tong_san_luong'] > CONG_SUAT_TOI_DA:
        st.warning(f"⚠️ **Vượt công suất chuẩn**\n\n- Tổng sản lượng: **{ke_hoach['tong_san_luong']:,.0f} Kg**\n- Công suất chuẩn: **{CONG_SUAT_TOI_DA:,.0f} Kg**\n- Còn trong giới hạn cho phép (105%): **{CONG_SUAT_CHO_PHEP:,.0f} Kg**")
    else:
        con_lai = CONG_SUAT_TOI_DA - ke_hoach['tong_san_luong']
        st.success(f"✅ **Trong giới hạn công suất**\n\n- Tổng sản lượng: **{ke_hoach['tong_san_luong']:,.0f} Kg** ({ty_le:.1f}%)\n- Còn trống: **{con_lai:,.0f} Kg**")
    
    st.markdown(f"### 📋 Danh sách {ke_hoach['so_san_pham']} sản phẩm ưu tiên")
    df = pd.DataFrame(ke_hoach['danh_sach'])
    df_display = df[['code', 'ten', 'stock', 'doh', 'so_luong', 'loai', 'ghi_chu']].copy()
    df_display.columns = ['Code', 'Tên', 'Stock (Kg)', 'DoH', 'SX (Kg)', 'Loại', 'Ghi chú']
    df_display['DoH'] = df_display['DoH'].round(1)
    df_display['Stock (Kg)'] = df_display['Stock (Kg)'].apply(lambda x: f"{x:,.0f}")
    df_display['SX (Kg)'] = df_display['SX (Kg)'].apply(lambda x: f"{x:,.0f}")
    st.dataframe(df_display, hide_index=False, width='stretch', height=600)
    
    st.markdown("---")
    if st.button("💾 Lưu Kế hoạch vào Database", type="primary", use_container_width=True):
        luu_ke_hoach(ke_hoach, ngay)
    
    if 'debug' in ke_hoach:
        debug = ke_hoach['debug']
        with st.expander("🔍 Debug Info", expanded=False):
            st.write(f"Tìm {debug['ngay_str']} hoặc {debug['ngay_str_alt']} → Tìm thấy {debug['manual_count']} kế hoạch")
        
        if debug['manual_count'] > 0:
            with st.expander("🔍 Debug Info - Xử lý", expanded=False):
                st.success(f"✅ ĐANG XỬ LÝ {debug['manual_count']} kế hoạch thủ công...")
            
            with st.expander("ℹ️ Thông tin kế hoạch thủ công", expanded=False):
                st.info(f"📌 **Đã có kế hoạch thủ công** cho ngày {ngay.strftime('%d/%m/%Y')}\n\nMã plan: **{debug['ma_plan']}** - Không cần tính toán tự động!")

def luu_ke_hoach(ke_hoach, ngay):
    try:
        conn = sqlite3.connect('database_new.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX([Mã plan]) FROM Plan WHERE [Mã plan] LIKE 'PL%'")
        result = cursor.fetchone()[0]
        next_num = int(result[2:]) + 1 if result else 1
        ma_plan = f"PL{next_num:05d}"
        ngay_plan = ngay.strftime('%Y-%m-%d')
        thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        count = 0
        for item in ke_hoach['danh_sach']:
            cursor.execute("INSERT INTO Plan ([ID sản phẩm], [Mã plan], [Số lượng], [Ngày plan], [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa]) VALUES (?, ?, ?, ?, ?, ?, ?, 0)", (item['id_sanpham'], ma_plan, item['so_luong'], ngay_plan, item['ghi_chu'], st.session_state.username, thoi_gian_tao))
            count += 1
        conn.commit()
        conn.close()
        st.success(f"🎉 Đã lưu {count} sản phẩm vào kế hoạch với mã: **{ma_plan}**")
        st.balloons()
        if 'ke_hoach_data' in st.session_state:
            del st.session_state['ke_hoach_data']
        st.rerun()
    except Exception as e:
        st.error(f"❌ Lỗi khi lưu: {e}")
        import traceback
        with st.expander("Chi tiết lỗi"):
            st.code(traceback.format_exc())
