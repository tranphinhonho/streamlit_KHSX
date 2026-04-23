import streamlit as st
from admin.sys_kde_components import *
import sqlite3
import datetime as dt
import pandas as pd
from utils.import_notification import send_import_notification

def process_import_dathang(df, loai_dathang, khach_vang_lai=0):
    """Xử lý import Excel cho đặt hàng"""
    # Kiểm tra cột bắt buộc - hỗ trợ cả 2 định dạng
    if 'Tên sản phẩm' in df.columns:
        # Định dạng mới: chỉ cần Tên sản phẩm và Số lượng
        return process_import_by_product_name(df, loai_dathang, khach_vang_lai)
    elif 'Code cám' in df.columns:
        # Định dạng cũ: cần Code cám đầy đủ
        return process_import_by_code_cam(df, loai_dathang, khach_vang_lai)
    else:
        st.error("❌ File Excel phải có cột 'Tên sản phẩm' hoặc 'Code cám' và 'Số lượng'")
        return None

def process_import_by_product_name(df, loai_dathang, khach_vang_lai=0):
    """Xử lý import Excel từ tên sản phẩm - tự động tìm thông tin từ database"""
    if 'Số lượng' not in df.columns:
        st.error("❌ File Excel phải có cột 'Số lượng'")
        return None
    
    conn = sqlite3.connect('database_new.db')
    result_data = []
    not_found = []
    
    for idx, row in df.iterrows():
        ten_sanpham = str(row['Tên sản phẩm']).strip()
        so_luong = row['Số lượng']
        
        # Tìm sản phẩm từ tên
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, [Code cám], [Tên cám], [Kích cỡ ép viên] 
            FROM SanPham 
            WHERE [Tên cám] = ? AND [Đã xóa] = 0
        """, (ten_sanpham,))
        result = cursor.fetchone()
        
        if result:
            id_sanpham, code_cam, ten_cam, kich_co = result
            
            item = {
                'ID sản phẩm': id_sanpham,
                'Số lượng': so_luong,
                'Ngày lấy': row.get('Ngày lấy (tùy chọn)', row.get('Ngày lấy', None)),
                'Ghi chú': row.get('Ghi chú (tùy chọn)', row.get('Ghi chú', None)),
                'Loại đặt hàng': loai_dathang,
                'Khách vãng lai': khach_vang_lai,
                'Code cám được tạo': code_cam,  # Hiển thị cho user biết
                'Tên sản phẩm': ten_cam
            }
            result_data.append(item)
        else:
            not_found.append(ten_sanpham)
    
    conn.close()
    
    # Hiển thị thông báo
    if not_found:
        st.warning(f"⚠️ Không tìm thấy {len(not_found)} sản phẩm: {', '.join(not_found)}")
    
    if result_data:
        df_result = pd.DataFrame(result_data)
        
        # Thêm các trường bắt buộc cho database
        madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH', num_char=5)
        df_result['Mã đặt hàng'] = madathang
        df_result['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_result['Người tạo'] = st.session_state.username
        df_result['Thời gian tạo'] = fn.get_vietnam_time()
        
        # Hiển thị thông tin code cám được tạo
        st.success(f"✅ Đã xử lý thành công {len(result_data)} sản phẩm với mã: **{madathang}**")
        
        # Hiển thị preview
        with st.expander("📋 Xem trước dữ liệu được import"):
            display_cols = ['Tên sản phẩm', 'Code cám được tạo', 'Số lượng', 'Ngày lấy', 'Ghi chú']
            preview_df = df_result[display_cols].copy()
            st.dataframe(preview_df, width="stretch")
        
        # Chỉ return các cột cần thiết cho database (loại bỏ cột hiển thị)
        db_cols = ['ID sản phẩm', 'Số lượng', 'Ngày lấy', 'Ghi chú', 
                   'Loại đặt hàng', 'Khách vãng lai', 'Mã đặt hàng', 
                   'Ngày đặt', 'Người tạo', 'Thời gian tạo']
        return df_result[db_cols]
    
    return None

def process_import_by_code_cam(df, loai_dathang, khach_vang_lai=0):
    """Xử lý import Excel từ Code cám đầy đủ - định dạng cũ"""
    if 'Số lượng' not in df.columns:
        st.error("❌ File Excel phải có cột 'Số lượng'")
        return None
        
    # Lấy ID sản phẩm từ Code cám
    conn = sqlite3.connect('database_new.db')
    
    result_data = []
    not_found = []
    
    for idx, row in df.iterrows():
        code_cam = str(row['Code cám']).strip()
        so_luong = row['Số lượng']
        
        # Tìm ID sản phẩm
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM SanPham WHERE [Code cám] = ? AND [Đã xóa] = 0", (code_cam,))
        result = cursor.fetchone()
        
        if result:
            id_sanpham = result[0]
            
            item = {
                'ID sản phẩm': id_sanpham,
                'Số lượng': so_luong,
                'Ngày lấy': row.get('Ngày lấy', None),
                'Ghi chú': row.get('Ghi chú', None),
                'Loại đặt hàng': loai_dathang,
                'Khách vãng lai': khach_vang_lai
            }
            result_data.append(item)
        else:
            not_found.append(code_cam)
    
    conn.close()
    
    # Hiển thị thông báo
    if not_found:
        st.warning(f"⚠️ Không tìm thấy {len(not_found)} sản phẩm: {', '.join(not_found)}")
    
    if result_data:
        df_result = pd.DataFrame(result_data)
        
        # Tạo mã đặt hàng
        madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH', num_char=5)
        df_result['Mã đặt hàng'] = madathang
        df_result['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
        df_result['Người tạo'] = st.session_state.username
        df_result['Thời gian tạo'] = fn.get_vietnam_time()
        
        st.success(f"✅ Đã import {len(result_data)} sản phẩm với mã: **{madathang}**")
        return df_result
    
    return None

def app(selected):
    
    # Hướng dẫn các loại đặt hàng
    with st.expander("ℹ️ Hướng dẫn các loại đặt hàng", expanded=False):
        st.markdown("""
### Mối quan hệ giữa các loại đặt hàng

| Loại | Mô tả | File nguồn |
|------|-------|------------|
| **👤 Khách vãng lai** | Đơn hàng phát sinh thêm, không có trong forecast tuần | Nhập tay hoặc Excel |
| **🏪 Đại lý Bá Cang** | Khách đặt trước, cố định ngày lấy. Bao gồm **Xe tải (bao 25kg)** và **Xe bồn (Silo)** | `KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG 2026.xlsx` |
| **🚛 Xe bồn Silo** | Tổng hợp Silo của Bá Cang + Silo của các khách hàng còn lại | `SILO W*.xlsx` |
| **📅 Forecast hàng tuần** | Tổng hợp tất cả: Xe tải Bá Cang + Silo Bá Cang + Silo khách khác + Đại lý khác + Cám trại nội bộ | `SALEFORECAST 2026.xlsx` |

> **Lưu ý**: Forecast hàng tuần là nguồn dữ liệu chính bao gồm toàn bộ kế hoạch. Các loại khác dùng để bổ sung hoặc chi tiết hóa.
        """)
    
    # Tạo 4 tabs cho các loại đặt hàng khác nhau
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Khách vãng lai",
        "🏪 Đại lý Bá Cang", 
        "🚛 Xe bồn Silo", 
        "📅 Forecast hàng tuần"
    ])
    
    # Lấy danh sách sản phẩm
    ds_sanpham = ss.get_columns_data(table_name='SanPham',
                                     columns=['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên', 'ID'],
                                     data_type='list',
                                     col_where={'Đã xóa':('=',0)})
    
    # TAB 1: Khách vãng lai
    with tab1:
        st.header("Đặt hàng Khách vãng lai")
        
        subtab1, subtab2 = st.tabs(["✍️ Nhập tay", "📁 Import Excel"])
        
        # Sub-tab: Nhập tay
        with subtab1:
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
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='khach_vang_lai_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Khách vãng lai'
            df_insert['Khách vãng lai'] = 1
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm đơn hàng Khách vãng lai", disabled=disabled, type="primary", key='btn_khach_vang_lai_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab: Import Excel
        with subtab2:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_khach_vang_lai')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Khách vãng lai', khach_vang_lai=1)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_kvl'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
    
    # TAB 2: Đại lý Bá Cang
    with tab2:
        st.header("Đặt hàng Đại lý Bá Cang")
        st.info("🏪 Dữ liệu được lấy từ Forecast hàng tuần")
        
        # Nút xóa tất cả dữ liệu Bá Cang
        with st.expander("⚠️ Xóa tất cả dữ liệu Đại lý Bá Cang", expanded=False):
            st.warning("⚠️ Hành động này sẽ xóa **TẤT CẢ** dữ liệu Đại lý Bá Cang. Bạn có chắc chắn?")
            col_del1, col_del2 = st.columns([1, 3])
            with col_del1:
                if st.button("🗑️ Xóa tất cả", type="secondary", key="btn_delete_all_bacang"):
                    try:
                        from utils.bacang_importer import BaCangImporter
                        importer = BaCangImporter()
                        result = importer.delete_all_bacang_data()
                        
                        if result['success']:
                            st.success(f"✅ {result['message']}")
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi: {result['message']}")
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")
            with col_del2:
                st.caption("💡 Khi import tuần 3, dữ liệu tuần 3 cũ sẽ tự động bị ghi đè")
        
        subtab1, subtab2, subtab3 = st.tabs(["📁 Import từ Bá Cang", "✍️ Nhập tay", "📂 Import Excel khác"])
        
        # Sub-tab 1: Import từ file Bá Cang
        with subtab1:
            st.subheader("Import từ file KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG")
            st.caption("Đọc dữ liệu từ 2 bảng: Bảng 1 (K/L/M/N) và Bảng 2 (R/S/T)")
            
            try:
                from utils.bacang_importer import BaCangImporter
                
                importer = BaCangImporter()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    import os
                    import json
                    file_path = None
                    
                    # === Load config từ file JSON (persist qua browser refresh) ===
                    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
                    os.makedirs(config_dir, exist_ok=True)
                    config_file = os.path.join(config_dir, 'last_files.json')
                    
                    # Load config nếu chưa có trong session state
                    if 'bacang_last_file_path' not in st.session_state:
                        if os.path.exists(config_file):
                            try:
                                with open(config_file, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                                if 'bacang_last_file_path' in config and os.path.exists(config.get('bacang_last_file_path', '')):
                                    st.session_state.bacang_last_file_path = config['bacang_last_file_path']
                                    st.session_state.bacang_last_file_name = config.get('bacang_last_file_name', 'N/A')
                            except:
                                pass
                    
                    # === Hiển thị file đang sử dụng ===
                    if 'bacang_last_file_path' in st.session_state:
                        last_path = st.session_state.bacang_last_file_path
                        last_name = st.session_state.get('bacang_last_file_name', 'N/A')
                        
                        if os.path.exists(last_path):
                            st.success(f"📁 File đang dùng: **{last_name}**")
                            file_path = last_path
                    
                    # === File uploader ===
                    st.write("**Chọn file Excel Bá Cang**")
                    uploaded = st.file_uploader(
                        "Chọn file Excel Bá Cang",
                        type=['xlsx', 'xlsm'],
                        key="bacang_upload",
                        label_visibility="collapsed"
                    )
                    
                    # Nếu có file mới upload, ưu tiên dùng file mới
                    if uploaded:
                        import tempfile
                        
                        # Giữ nguyên extension gốc của file (.xlsx hoặc .xlsm)
                        original_ext = os.path.splitext(uploaded.name)[1].lower()
                        
                        # Lưu file vào thư mục EXCEL để sử dụng lại
                        excel_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'EXCEL')
                        os.makedirs(excel_dir, exist_ok=True)
                        saved_path = os.path.join(excel_dir, uploaded.name)
                        
                        try:
                            with open(saved_path, 'wb') as f:
                                f.write(uploaded.read())
                            file_path = saved_path
                        except PermissionError:
                            # Nếu file đang được sử dụng, tạo file tạm
                            uploaded.seek(0)  # Reset file pointer
                            with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as f:
                                f.write(uploaded.read())
                                file_path = f.name
                        
                        # Lưu đường dẫn file vào session state
                        st.session_state.bacang_last_file_path = file_path
                        st.session_state.bacang_last_file_name = uploaded.name
                        
                        # === Lưu vào config file để persist qua browser refresh ===
                        try:
                            config = {}
                            if os.path.exists(config_file):
                                with open(config_file, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                            config['bacang_last_file_path'] = file_path
                            config['bacang_last_file_name'] = uploaded.name
                            with open(config_file, 'w', encoding='utf-8') as f:
                                json.dump(config, f, ensure_ascii=False, indent=2)
                        except:
                            pass
                        
                        # Xóa cache danh sách sheets để buộc refresh
                        if 'bacang_sheet_select' in st.session_state:
                            del st.session_state['bacang_sheet_select']
                        st.rerun()
                
                if file_path:
                    try:
                        sheets = importer.get_available_sheets(file_path)
                        
                        with col2:
                            # Mặc định chọn sheet cuối cùng (tuần mới nhất)
                            default_index = len(sheets) - 1 if sheets else 0
                            
                            selected_sheet = st.selectbox(
                                "📅 Chọn tuần",
                                options=sheets,
                                index=default_index,
                                help="Mỗi sheet tương ứng với một tuần",
                                key="bacang_sheet_select"
                            )
                        
                        if selected_sheet:
                            st.subheader(f"📋 Preview dữ liệu {selected_sheet}")
                            
                            with st.spinner("Đang đọc dữ liệu..."):
                                preview_df1, preview_df2 = importer.preview_data(
                                    file_path=file_path,
                                    sheet_name=selected_sheet,
                                    limit=500
                                )
                            
                            # === NÚT LỌC THEO NGÀY TRONG TUẦN ===
                            def get_day_of_week_bacang(date_val):
                                """Chuyển đổi ngày thành thứ trong tuần (0=T2, 6=CN)"""
                                try:
                                    if pd.isna(date_val):
                                        return -1
                                    # Xử lý nhiều định dạng ngày
                                    if isinstance(date_val, str):
                                        # Định dạng dd/mm/yyyy hoặc yyyy-mm-dd
                                        if '/' in date_val:
                                            date_obj = pd.to_datetime(date_val, format='%d/%m/%Y', dayfirst=True)
                                        else:
                                            date_obj = pd.to_datetime(date_val)
                                    else:
                                        date_obj = pd.to_datetime(date_val)
                                    return date_obj.dayofweek  # 0=Monday(T2), 6=Sunday(CN)
                                except:
                                    return -1
                            
                            DAY_LABELS_BC = {0: 'T2', 1: 'T3', 2: 'T4', 3: 'T5', 4: 'T6', 5: 'T7', 6: 'CN'}
                            
                            # Thêm cột ngày trong tuần cho cả 2 bảng
                            if len(preview_df1) > 0 and 'Ngày lấy' in preview_df1.columns:
                                preview_df1['_day_of_week'] = preview_df1['Ngày lấy'].apply(get_day_of_week_bacang)
                            else:
                                preview_df1['_day_of_week'] = -1
                                
                            if len(preview_df2) > 0 and 'Ngày lấy' in preview_df2.columns:
                                preview_df2['_day_of_week'] = preview_df2['Ngày lấy'].apply(get_day_of_week_bacang)
                            else:
                                preview_df2['_day_of_week'] = -1
                            
                            # Tính tổng sản lượng theo ngày trong tuần cho mỗi bảng
                            available_days_bc = ['ALL']
                            for day_idx in range(7):
                                has_data_df1 = len(preview_df1) > 0 and 'Số lượng (kg)' in preview_df1.columns and \
                                              len(preview_df1[preview_df1['_day_of_week'] == day_idx]) > 0 and \
                                              preview_df1[preview_df1['_day_of_week'] == day_idx]['Số lượng (kg)'].sum() > 0
                                has_data_df2 = len(preview_df2) > 0 and 'Số lượng (kg)' in preview_df2.columns and \
                                              len(preview_df2[preview_df2['_day_of_week'] == day_idx]) > 0 and \
                                              preview_df2[preview_df2['_day_of_week'] == day_idx]['Số lượng (kg)'].sum() > 0
                                if has_data_df1 or has_data_df2:
                                    available_days_bc.append(DAY_LABELS_BC[day_idx])
                            
                            # Tạo các nút lọc
                            btn_cols_bc = st.columns(8)  # 8 cột cho ALL + 7 ngày
                            
                            # Lấy filter hiện tại từ session state
                            if 'bacang_day_filter' not in st.session_state:
                                st.session_state.bacang_day_filter = 'ALL'
                            
                            all_day_labels = ['ALL', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
                            for i, day_label in enumerate(all_day_labels):
                                with btn_cols_bc[i]:
                                    is_available = day_label in available_days_bc
                                    is_selected = st.session_state.bacang_day_filter == day_label
                                    btn_type = "primary" if is_selected else "secondary"
                                    
                                    if is_available:
                                        if st.button(day_label, key=f"bacang_day_{day_label}", type=btn_type):
                                            st.session_state.bacang_day_filter = day_label
                                            st.rerun()
                                    else:
                                        # Nút bị disable (không có dữ liệu)
                                        st.button(day_label, key=f"bacang_day_{day_label}", disabled=True)
                            
                            # Lọc dữ liệu theo ngày được chọn
                            current_filter = st.session_state.bacang_day_filter
                            if current_filter == 'ALL':
                                filtered_df1 = preview_df1
                                filtered_df2 = preview_df2
                            else:
                                # Tìm day index từ label
                                day_idx_filter = None
                                for k, v in DAY_LABELS_BC.items():
                                    if v == current_filter:
                                        day_idx_filter = k
                                        break
                                if day_idx_filter is not None:
                                    filtered_df1 = preview_df1[preview_df1['_day_of_week'] == day_idx_filter]
                                    filtered_df2 = preview_df2[preview_df2['_day_of_week'] == day_idx_filter]
                                else:
                                    filtered_df1 = preview_df1
                                    filtered_df2 = preview_df2
                            
                            # Xóa cột tạm trước khi hiển thị
                            display_df1 = filtered_df1.drop(columns=['_day_of_week'], errors='ignore')
                            display_df2 = filtered_df2.drop(columns=['_day_of_week'], errors='ignore')
                            
                            # Kiểm tra có dữ liệu hay không để hiển thị bảng
                            show_table1 = len(display_df1) > 0 and 'Số lượng (kg)' in display_df1.columns and display_df1['Số lượng (kg)'].sum() > 0
                            show_table2 = len(display_df2) > 0 and 'Số lượng (kg)' in display_df2.columns and display_df2['Số lượng (kg)'].sum() > 0
                            
                            if show_table1 and show_table2:
                                # Hiển thị cả 2 bảng cạnh nhau
                                col_preview1, col_preview2 = st.columns(2)
                                
                                with col_preview1:
                                    st.markdown("**Bảng 1** - 🚛 Xe tải (bao 25kg)")
                                    st.dataframe(display_df1, width="stretch")
                                
                                with col_preview2:
                                    st.markdown("**Bảng 2** - 🚛 Xe bồn (Silo)")
                                    st.dataframe(display_df2, width="stretch")
                            elif show_table1:
                                # Chỉ hiển thị bảng 1
                                st.markdown("**Bảng 1** - 🚛 Xe tải (bao 25kg)")
                                st.dataframe(display_df1, width="stretch")
                            elif show_table2:
                                # Chỉ hiển thị bảng 2
                                st.markdown("**Bảng 2** - 🚛 Xe bồn (Silo)")
                                st.dataframe(display_df2, width="stretch")
                            else:
                                st.info(f"📅 Ngày {current_filter} không có dữ liệu")
                            
                            if show_table1 or show_table2:
                                st.caption(f"Hiển thị {len(display_df1)} dòng bảng 1 và {len(display_df2)} dòng bảng 2")
                                
                                # Tính tổng sản lượng dựa trên dữ liệu đã lọc
                                total_xetai = display_df1['Số lượng (kg)'].sum() if show_table1 else 0
                                total_xebon = display_df2['Số lượng (kg)'].sum() if show_table2 else 0
                                
                                col_total1, col_total2 = st.columns(2)
                                if show_table1:
                                    with col_total1:
                                        st.success(f"🚛 **Tổng Xe tải (bao 25kg):** {total_xetai:,.0f} kg ({total_xetai/1000:,.1f} tấn)")
                                if show_table2:
                                    with col_total2:
                                        st.info(f"🛢️ **Tổng Xe bồn (Silo):** {total_xebon:,.0f} kg ({total_xebon/1000:,.1f} tấn)")
                                
                                col_btn1, col_btn2 = st.columns([1, 1])
                                
                                with col_btn1:
                                    if st.button("🚀 Import vào Database", type="primary", key="btn_import_bacang"):
                                        with st.spinner(f"Đang import dữ liệu {selected_sheet}..."):
                                            result = importer.import_bacang_data(
                                                file_path=file_path,
                                                sheet_name=selected_sheet,
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                        
                                        if result['success'] > 0:
                                            deleted_msg = ""
                                            if result.get('deleted', 0) > 0:
                                                deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                            
                                            st.success(
                                                f"{deleted_msg}"
                                                f"✅ Import thành công **{result['success']}** sản phẩm!\n\n"
                                                f"📦 Mã đặt hàng: **{result['ma_dathang']}**\n\n"
                                                f"📅 Sheet: **{result['sheet_name']}**"
                                            )
                                            st.balloons()
                                            
                                            if result['not_found']:
                                                with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã cám"):
                                                    for code in result['not_found'][:20]:
                                                        st.text(f"- {code}")
                                                    if len(result['not_found']) > 20:
                                                        st.text(f"... và {len(result['not_found']) - 20} mã khác")
                                                
                                                # Gửi email thông báo
                                                email_sent = send_import_notification(
                                                    not_found_codes=result['not_found'],
                                                    filename=file_path,
                                                    import_type='BACANG',
                                                    ngay_import=selected_sheet,
                                                    nguoi_import=st.session_state.get('username', 'system')
                                                )
                                                if email_sent:
                                                    st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                        else:
                                            st.error("❌ Không import được sản phẩm nào!")
                                            if result['errors']:
                                                for err in result['errors']:
                                                    st.error(err)
                                            if result['not_found']:
                                                st.warning(f"Không tìm thấy {len(result['not_found'])} mã cám trong database")
                                                # Gửi email thông báo
                                                email_sent = send_import_notification(
                                                    not_found_codes=result['not_found'],
                                                    filename=file_path,
                                                    import_type='BACANG',
                                                    ngay_import=selected_sheet,
                                                    nguoi_import=st.session_state.get('username', 'system')
                                                )
                                                if email_sent:
                                                    st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                
                                with col_btn2:
                                    # Chỉ hiển thị nút "Chuyển qua Plan" khi chọn 1 ngày cụ thể (không phải ALL)
                                    if current_filter != 'ALL' and (show_table1 or show_table2):
                                        if st.button("📤 Chuyển qua Plan", type="secondary", key="btn_transfer_bacang"):
                                            # Chuẩn bị dữ liệu để chuyển sang Plan
                                            new_data = []
                                            
                                            # Lấy ngày lấy từ dữ liệu (ngày plan = ngày lấy - 1 vì SX trước 1 ngày)
                                            ngay_lay = None
                                            
                                            if show_table1 and len(display_df1) > 0:
                                                for _, row in display_df1.iterrows():
                                                    new_data.append({
                                                        'Tên cám': row.get('Tên cám', ''),
                                                        'Số lượng': row.get('Số lượng (kg)', 0),
                                                        'Ngày lấy': row.get('Ngày lấy', ''),
                                                        'Nguồn': 'Bá Cang - Xe tải'
                                                    })
                                                    if ngay_lay is None and row.get('Ngày lấy'):
                                                        ngay_lay = row.get('Ngày lấy')
                                            
                                            if show_table2 and len(display_df2) > 0:
                                                for _, row in display_df2.iterrows():
                                                    new_data.append({
                                                        'Tên cám': row.get('Tên cám', ''),
                                                        'Số lượng': row.get('Số lượng (kg)', 0),
                                                        'Ngày lấy': row.get('Ngày lấy', ''),
                                                        'Nguồn': 'Bá Cang - Silo'
                                                    })
                                                    if ngay_lay is None and row.get('Ngày lấy'):
                                                        ngay_lay = row.get('Ngày lấy')
                                            
                                            if new_data:
                                                # === MERGE LOGIC: Gộp với dữ liệu có sẵn ===
                                                existing_data = []
                                                existing_sources = []
                                                if 'plan_transfer_data' in st.session_state and st.session_state['plan_transfer_data']:
                                                    existing_data = st.session_state['plan_transfer_data'].get('data', [])
                                                    existing_sources = [st.session_state['plan_transfer_data'].get('source', '')]
                                                
                                                # Gộp dữ liệu: Nếu trùng Tên cám, giữ số lượng lớn hơn
                                                merged_dict = {}
                                                
                                                # Thêm dữ liệu cũ vào dict
                                                for item in existing_data:
                                                    ten_cam = item.get('Tên cám', '')
                                                    if ten_cam:
                                                        if ten_cam not in merged_dict or item.get('Số lượng', 0) > merged_dict[ten_cam].get('Số lượng', 0):
                                                            merged_dict[ten_cam] = item
                                                
                                                # Thêm dữ liệu mới: nếu trùng, giữ số lượng lớn hơn
                                                for item in new_data:
                                                    ten_cam = item.get('Tên cám', '')
                                                    if ten_cam:
                                                        if ten_cam not in merged_dict or item.get('Số lượng', 0) > merged_dict[ten_cam].get('Số lượng', 0):
                                                            merged_dict[ten_cam] = item
                                                
                                                merged_data = list(merged_dict.values())
                                                
                                                # Cập nhật sources
                                                new_source = f'Đại lý Bá Cang - {current_filter}'
                                                if new_source not in existing_sources:
                                                    existing_sources.append(new_source)
                                                combined_source = ' + '.join([s for s in existing_sources if s])
                                                
                                                st.session_state['plan_transfer_data'] = {
                                                    'data': merged_data,
                                                    'source': combined_source,
                                                    'ngay_lay': ngay_lay,
                                                    'sheet': selected_sheet
                                                }
                                                
                                                st.success(f"✅ Đã gộp **{len(new_data)}** sản phẩm mới → Tổng: **{len(merged_data)}** sản phẩm!\n\n👉 Vào **Plan > Nhập kế hoạch thủ công** để xử lý.")
                                                st.info(f"📅 Ngày lấy: **{ngay_lay}** → SX trước 1 ngày")
                                            else:
                                                st.warning("Không có dữ liệu để chuyển!")
                            else:
                                st.info("📅 Tuần này không có dữ liệu Bá Cang")
                                
                    except Exception as e:
                        st.error(f"❌ Lỗi đọc file: {e}")
                        import traceback
                        with st.expander("Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                            
            except ImportError as e:
                st.error(f"❌ Không thể import module: {e}")
        
        # Sub-tab 2: Nhập tay
        with subtab2:
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
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='ba_cang_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Đại lý Bá Cang'
            df_insert['Khách vãng lai'] = 0
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm đơn hàng Bá Cang", disabled=disabled, type="primary", key='btn_ba_cang_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab 3: Import Excel khác
        with subtab3:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_ba_cang')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Đại lý Bá Cang', khach_vang_lai=0)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_bc'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
    
    # TAB 3: Xe bồn Silo
    with tab3:
        st.header("Đặt hàng Xe bồn Silo")
        st.info("🚛 Dữ liệu được lấy từ Forecast hàng tuần")
        
        subtab1, subtab2, subtab3 = st.tabs(["📁 Import từ SILO", "✍️ Nhập tay", "📂 Import Excel khác"])
        
        # Sub-tab 1: Import từ file SILO
        with subtab1:
            st.subheader("Import từ file SILO hàng tuần")
            
            try:
                from utils.silo_importer import SiloImporter
                
                importer = SiloImporter()
                
                # === Hiển thị bảng tóm tắt import gần nhất (nếu có) ===
                if 'silo_last_import' in st.session_state and st.session_state.silo_last_import:
                    last_import = st.session_state.silo_last_import
                    with st.expander(f"📋 Tóm tắt import gần nhất: {last_import.get('sheet_name', 'N/A')}", expanded=True):
                        st.success(f"✅ Import thành công **{last_import.get('success', 0)}** sản phẩm | Mã: **{last_import.get('ma_dathang', 'N/A')}**")
                        
                        # Hiển thị bảng tóm tắt đã lưu
                        if 'summary_df' in last_import and last_import['summary_df'] is not None:
                            st.dataframe(
                                last_import['summary_df'],
                                width="stretch",
                                column_config={
                                    'Ngày lấy cám': st.column_config.TextColumn('Ngày lấy cám', width='small'),
                                    'Xe cám đại lý': st.column_config.NumberColumn('Xe cám đại lý', width='small', format='%d'),
                                    'Xe cám trại': st.column_config.NumberColumn('Xe cám trại', width='small', format='%d'),
                                    'Số lượng (kg)': st.column_config.NumberColumn('Số lượng (kg)', width='medium', format='%,.0f')
                                },
                                hide_index=True
                            )
                    
                    st.divider()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    import os
                    import json
                    file_path = None
                    
                    # === Load config từ file JSON (persist qua browser refresh) ===
                    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
                    os.makedirs(config_dir, exist_ok=True)
                    config_file = os.path.join(config_dir, 'last_files.json')
                    
                    # Load config nếu chưa có trong session state
                    if 'silo_last_file_path' not in st.session_state:
                        if os.path.exists(config_file):
                            try:
                                with open(config_file, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                                if 'silo_last_file_path' in config and os.path.exists(config.get('silo_last_file_path', '')):
                                    st.session_state.silo_last_file_path = config['silo_last_file_path']
                                    st.session_state.silo_last_file_name = config.get('silo_last_file_name', 'N/A')
                            except:
                                pass
                    
                    # === Checkbox sử dụng file mặc định (hiển thị trước) ===
                    if 'silo_last_file_path' in st.session_state:
                        last_path = st.session_state.silo_last_file_path
                        last_name = st.session_state.get('silo_last_file_name', 'N/A')
                        
                        if os.path.exists(last_path):
                            # Khởi tạo session state cho checkbox nếu chưa có
                            if 'silo_use_default_file' not in st.session_state:
                                st.session_state.silo_use_default_file = True
                            
                            use_default = st.checkbox(
                                f"📁 Sử dụng file mặc định: **{last_name}**",
                                key="silo_use_default_file"
                            )
                            if use_default:
                                file_path = last_path
                                st.caption(f"📂 Đường dẫn: `{last_path}`")
                    
                    # === File uploader (hiển thị sau) ===
                    st.write("**Chọn file Excel SILO**")
                    uploaded = st.file_uploader(
                        "Chọn file Excel SILO",
                        type=['xlsx', 'xlsm'],
                        key="silo_upload",
                        label_visibility="collapsed"
                    )
                    
                    # Nếu có file mới upload, ưu tiên dùng file mới
                    if uploaded:
                        import tempfile
                        import shutil
                        
                        # Giữ nguyên extension gốc của file (.xlsx hoặc .xlsm)
                        original_ext = os.path.splitext(uploaded.name)[1].lower()
                        
                        # Lưu file vào thư mục EXCEL để sử dụng lại
                        excel_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'EXCEL')
                        os.makedirs(excel_dir, exist_ok=True)
                        saved_path = os.path.join(excel_dir, uploaded.name)
                        
                        try:
                            with open(saved_path, 'wb') as f:
                                f.write(uploaded.read())
                            file_path = saved_path
                        except PermissionError:
                            # Nếu file đang được sử dụng, tạo file tạm
                            uploaded.seek(0)  # Reset file pointer
                            with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as f:
                                f.write(uploaded.read())
                                file_path = f.name
                        
                        # Lưu đường dẫn file vào session state
                        st.session_state.silo_last_file_path = file_path
                        st.session_state.silo_last_file_name = uploaded.name
                        
                        # === Lưu vào config file để persist qua browser refresh ===
                        try:
                            config = {}
                            if os.path.exists(config_file):
                                with open(config_file, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                            config['silo_last_file_path'] = file_path
                            config['silo_last_file_name'] = uploaded.name
                            with open(config_file, 'w', encoding='utf-8') as f:
                                json.dump(config, f, ensure_ascii=False, indent=2)
                        except:
                            pass
                
                if file_path:
                    try:
                        sheets = importer.get_available_sheets(file_path)
                        
                        with col2:
                            selected_sheet = st.selectbox(
                                "📅 Chọn tuần",
                                options=sheets,
                                index=len(sheets)-1 if sheets else 0,
                                help="Mỗi sheet tương ứng với một tuần",
                                key="silo_sheet_select"
                            )
                        
                        if selected_sheet:
                            st.subheader(f"📋 Preview dữ liệu {selected_sheet}")
                            
                            with st.spinner("Đang đọc dữ liệu..."):
                                preview_df = importer.preview_data(
                                    file_path=file_path,
                                    sheet_name=selected_sheet,
                                    limit=500
                                )
                            
                            if len(preview_df) > 0:
                                # === NÚT LỌC THEO NGÀY ===
                                # Chuyển đổi ngày lấy thành thứ trong tuần
                                
                                def get_day_of_week(date_str):
                                    """Chuyển đổi ngày dd/mm/yyyy thành thứ trong tuần"""
                                    try:
                                        date_obj = pd.to_datetime(date_str, format='%d/%m/%Y')
                                        return date_obj.dayofweek  # 0=Thứ 2, 1=Thứ 3, ..., 6=Chủ nhật
                                    except:
                                        return -1
                                
                                # Thêm cột ngày trong tuần
                                preview_df['_day_of_week'] = preview_df['Ngày lấy'].apply(get_day_of_week)
                                
                                # Tính tổng sản lượng theo ngày trong tuần
                                day_totals = preview_df.groupby('_day_of_week')['Số lượng (kg)'].sum()
                                
                                # Danh sách các ngày có dữ liệu (kg > 0)
                                DAY_LABELS = {0: 'T2', 1: 'T3', 2: 'T4', 3: 'T5', 4: 'T6', 5: 'T7', 6: 'CN'}
                                available_days = ['ALL']
                                for day_idx in range(7):
                                    if day_idx in day_totals and day_totals[day_idx] > 0:
                                        available_days.append(DAY_LABELS[day_idx])
                                
                                # Tạo các nút lọc
                                btn_cols = st.columns(len(available_days))
                                
                                # Lấy filter hiện tại từ session state
                                if 'silo_day_filter' not in st.session_state:
                                    st.session_state.silo_day_filter = 'ALL'
                                
                                for i, day_label in enumerate(available_days):
                                    with btn_cols[i]:
                                        # Đánh dấu nút đang được chọn
                                        is_selected = st.session_state.silo_day_filter == day_label
                                        btn_type = "primary" if is_selected else "secondary"
                                        if st.button(day_label, key=f"silo_day_{day_label}", type=btn_type):
                                            st.session_state.silo_day_filter = day_label
                                            st.rerun()
                                
                                # Lọc dữ liệu theo ngày được chọn
                                if st.session_state.silo_day_filter == 'ALL':
                                    filtered_df = preview_df
                                else:
                                    # Tìm day index từ label
                                    day_idx = None
                                    for k, v in DAY_LABELS.items():
                                        if v == st.session_state.silo_day_filter:
                                            day_idx = k
                                            break
                                    if day_idx is not None:
                                        filtered_df = preview_df[preview_df['_day_of_week'] == day_idx]
                                    else:
                                        filtered_df = preview_df
                                
                                # Xóa cột tạm trước khi hiển thị
                                display_df = filtered_df.drop(columns=['_day_of_week'], errors='ignore')
                                
                                st.dataframe(
                                    display_df,
                                    width="stretch",
                                    column_config={
                                        'Ngày lấy': st.column_config.TextColumn('Ngày lấy', width='small'),
                                        'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                        'Số lượng (kg)': st.column_config.NumberColumn('Số lượng (kg)', format='%.0f')
                                    }
                                )
                                
                                st.caption(f"Hiển thị {len(display_df)} sản phẩm")
                                
                                # Tính và hiển thị tổng sản lượng
                                tong_san_luong = display_df['Số lượng (kg)'].sum() if 'Số lượng (kg)' in display_df.columns else 0
                                st.write(f"📊 **Tổng sản lượng:** {tong_san_luong:,.0f} kg")
                                
                                col_btn1, col_btn2 = st.columns([1, 1])
                                
                                with col_btn1:
                                    if st.button("🚀 Import vào Database", type="primary", key="btn_import_silo"):
                                        with st.spinner(f"Đang import dữ liệu {selected_sheet}..."):
                                            result = importer.import_silo_data(
                                                file_path=file_path,
                                                sheet_name=selected_sheet,
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                        
                                        if result['success'] > 0:
                                            deleted_msg = ""
                                            if result.get('deleted', 0) > 0:
                                                deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                            
                                            st.success(
                                                f"{deleted_msg}"
                                                f"✅ Import thành công **{result['success']}** sản phẩm!\n\n"
                                                f"📦 Mã đặt hàng: **{result['ma_dathang']}**\n\n"
                                                f"📅 {result['week_info']}"
                                            )
                                            st.balloons()
                                            
                                            # === BẢNG TÓM TẮT TUẦN ===
                                            st.subheader("📋 Tóm tắt tuần")
                                            
                                            # Tạo bảng tóm tắt từ preview_df
                                            summary_data = []
                                            grouped = preview_df.groupby('Ngày lấy')
                                            
                                            for ngay, group in grouped:
                                                # Phân loại: có chữ F = cám trại, không có F = cám đại lý
                                                # Tính tổng sản lượng theo loại
                                                dai_ly_filter = ~group['Tên cám'].str.contains('F', case=False, na=False)
                                                trai_filter = group['Tên cám'].str.contains('F', case=False, na=False)
                                                
                                                sl_dai_ly = group.loc[dai_ly_filter, 'Số lượng (kg)'].sum() if 'Số lượng (kg)' in group.columns else 0
                                                sl_trai = group.loc[trai_filter, 'Số lượng (kg)'].sum() if 'Số lượng (kg)' in group.columns else 0
                                                
                                                # Số xe = tổng sản lượng / 15000, làm tròn
                                                xe_dai_ly = round(sl_dai_ly / 15000) if sl_dai_ly > 0 else 0
                                                xe_trai = round(sl_trai / 15000) if sl_trai > 0 else 0
                                                so_luong_kg = sl_dai_ly + sl_trai
                                                
                                                summary_data.append({
                                                    'Ngày lấy cám': ngay,
                                                    'Xe cám đại lý': xe_dai_ly,
                                                    'Xe cám trại': xe_trai,
                                                    'Số lượng (kg)': so_luong_kg
                                                })
                                            
                                            summary_df = pd.DataFrame(summary_data)
                                            
                                            # Thêm dòng tổng cộng
                                            tong_xe_dai_ly = summary_df['Xe cám đại lý'].sum()
                                            tong_xe_trai = summary_df['Xe cám trại'].sum()
                                            tong_kg = summary_df['Số lượng (kg)'].sum()
                                            
                                            tong_row = pd.DataFrame([{
                                                'Ngày lấy cám': '**TỔNG CỘNG**',
                                                'Xe cám đại lý': tong_xe_dai_ly,
                                                'Xe cám trại': tong_xe_trai,
                                                'Số lượng (kg)': tong_kg
                                            }])
                                            
                                            summary_df = pd.concat([summary_df, tong_row], ignore_index=True)
                                            
                                            st.dataframe(
                                                summary_df,
                                                width="stretch",
                                                column_config={
                                                    'Ngày lấy cám': st.column_config.TextColumn('Ngày lấy cám', width='small'),
                                                    'Xe cám đại lý': st.column_config.NumberColumn('Xe cám đại lý', width='small', format='%d'),
                                                    'Xe cám trại': st.column_config.NumberColumn('Xe cám trại', width='small', format='%d'),
                                                    'Số lượng (kg)': st.column_config.NumberColumn('Số lượng (kg)', width='medium', format='%,.0f')
                                                },
                                                hide_index=True
                                            )
                                            
                                            # === LƯU VÀO SESSION STATE ===
                                            st.session_state.silo_last_import = {
                                                'sheet_name': selected_sheet,
                                                'success': result['success'],
                                                'ma_dathang': result['ma_dathang'],
                                                'week_info': result['week_info'],
                                                'summary_df': summary_df,
                                                'import_time': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            }
                                            
                                            if result['not_found']:
                                                with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã cám"):
                                                    for code in result['not_found'][:20]:
                                                        st.text(f"- {code}")
                                                    if len(result['not_found']) > 20:
                                                        st.text(f"... và {len(result['not_found']) - 20} mã khác")
                                                
                                                # Gửi email thông báo
                                                email_sent = send_import_notification(
                                                    not_found_codes=result['not_found'],
                                                    filename=file_path,
                                                    import_type='SILO',
                                                    ngay_import=selected_sheet,
                                                    nguoi_import=st.session_state.get('username', 'system')
                                                )
                                                if email_sent:
                                                    st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                        else:
                                            st.error("❌ Không import được sản phẩm nào!")
                                            if result['errors']:
                                                for err in result['errors']:
                                                    st.error(err)
                                            if result['not_found']:
                                                st.warning(f"Không tìm thấy {len(result['not_found'])} mã cám trong database")
                                                # Gửi email thông báo
                                                email_sent = send_import_notification(
                                                    not_found_codes=result['not_found'],
                                                    filename=file_path,
                                                    import_type='SILO',
                                                    ngay_import=selected_sheet,
                                                    nguoi_import=st.session_state.get('username', 'system')
                                                )
                                                if email_sent:
                                                    st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                
                                with col_btn2:
                                    # Chỉ hiển thị nút "Chuyển qua Plan" khi chọn 1 ngày cụ thể (không phải ALL)
                                    silo_current_filter = st.session_state.get('silo_day_filter', 'ALL')
                                    if silo_current_filter != 'ALL' and len(display_df) > 0:
                                        if st.button("📤 Chuyển qua Plan", type="secondary", key="btn_transfer_silo"):
                                            # Chuẩn bị dữ liệu để chuyển sang Plan
                                            new_data = []
                                            ngay_lay = None
                                            
                                            for _, row in display_df.iterrows():
                                                new_data.append({
                                                    'Tên cám': row.get('Tên cám', ''),
                                                    'Số lượng': row.get('Số lượng (kg)', 0),
                                                    'Ngày lấy': row.get('Ngày lấy', ''),
                                                    'Nguồn': 'Xe bồn Silo'
                                                })
                                                if ngay_lay is None and row.get('Ngày lấy'):
                                                    ngay_lay = row.get('Ngày lấy')
                                            
                                            if new_data:
                                                # === MERGE LOGIC: Gộp với dữ liệu có sẵn ===
                                                existing_data = []
                                                existing_sources = []
                                                if 'plan_transfer_data' in st.session_state and st.session_state['plan_transfer_data']:
                                                    existing_data = st.session_state['plan_transfer_data'].get('data', [])
                                                    existing_sources = [st.session_state['plan_transfer_data'].get('source', '')]
                                                
                                                # Gộp dữ liệu: Nếu trùng Tên cám, giữ số lượng lớn hơn
                                                merged_dict = {}
                                                
                                                # Thêm dữ liệu cũ vào dict
                                                for item in existing_data:
                                                    ten_cam = item.get('Tên cám', '')
                                                    if ten_cam:
                                                        if ten_cam not in merged_dict or item.get('Số lượng', 0) > merged_dict[ten_cam].get('Số lượng', 0):
                                                            merged_dict[ten_cam] = item
                                                
                                                # Thêm dữ liệu mới từ Silo: nếu trùng, giữ số lượng lớn hơn
                                                # (Silo thường có số lượng >= Bá Cang vì đã bao gồm cả Bá Cang)
                                                for item in new_data:
                                                    ten_cam = item.get('Tên cám', '')
                                                    if ten_cam:
                                                        if ten_cam not in merged_dict or item.get('Số lượng', 0) > merged_dict[ten_cam].get('Số lượng', 0):
                                                            merged_dict[ten_cam] = item
                                                
                                                merged_data = list(merged_dict.values())
                                                
                                                # Cập nhật sources
                                                new_source = f'Xe bồn Silo - {silo_current_filter}'
                                                if new_source not in existing_sources:
                                                    existing_sources.append(new_source)
                                                combined_source = ' + '.join([s for s in existing_sources if s])
                                                
                                                st.session_state['plan_transfer_data'] = {
                                                    'data': merged_data,
                                                    'source': combined_source,
                                                    'ngay_lay': ngay_lay,
                                                    'sheet': selected_sheet
                                                }
                                                
                                                st.success(f"✅ Đã gộp **{len(new_data)}** sản phẩm mới → Tổng: **{len(merged_data)}** sản phẩm!\n\n👉 Vào **Plan > Nhập kế hoạch thủ công** để xử lý.")
                                                st.info(f"📅 Ngày lấy: **{ngay_lay}** → SX trước 1 ngày")
                                            else:
                                                st.warning("Không có dữ liệu để chuyển!")
                            else:
                                st.info("📅 Tuần này không có dữ liệu xe bồn silo")
                                
                    except Exception as e:
                        st.error(f"❌ Lỗi đọc file: {e}")
                        import traceback
                        with st.expander("Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                            
            except ImportError as e:
                st.error(f"❌ Không thể import module: {e}")
        
        # Sub-tab 2: Nhập tay
        with subtab2:
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
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='xe_bon_silo_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Xe bồn Silo'
            df_insert['Khách vãng lai'] = 0
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm đơn hàng Xe bồn Silo", disabled=disabled, type="primary", key='btn_xe_bon_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab 3: Import Excel khác
        with subtab3:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_xe_bon')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Xe bồn Silo', khach_vang_lai=0)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_xb'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
    
    # TAB 4: Forecast hàng tuần (gửi vào thứ 6)
    with tab4:
        st.header("Forecast đặt hàng hàng tuần")
        st.info("📅 Forecast gửi vào ngày Thứ 6 hàng tuần")
        
        import datetime
        
        # Tính toán ngày thứ 6 tuần này
        today = fn.get_vietnam_time().date()
        weekday = today.weekday()  # 0 = Thứ 2, 4 = Thứ 6
        days_until_friday = (4 - weekday) % 7
        if days_until_friday == 0 and today.weekday() != 4:
            days_until_friday = 7
        next_friday = today + datetime.timedelta(days=days_until_friday)
        
        st.write(f"**Thứ 6 tuần này:** {next_friday.strftime('%d/%m/%Y')}")
        
        subtab1, subtab2, subtab3 = st.tabs(["📁 Import SALEFORECAST", "✍️ Nhập tay", "📂 Import Excel khác"])
        
        # Sub-tab 1: Import từ file SALEFORECAST
        with subtab1:
            st.subheader("Import từ file SALEFORECAST")
            
            try:
                from utils.forecast_importer import ForecastImporter
                
                importer = ForecastImporter()
                
                # === Hiển thị thông tin import gần nhất (nếu có) ===
                if 'forecast_last_import' in st.session_state and st.session_state.forecast_last_import:
                    last_import = st.session_state.forecast_last_import
                    
                    with st.expander(f"📊 Tóm tắt Import gần nhất: {last_import.get('sheet_name', 'N/A')}", expanded=True):
                        # Hiển thị thông tin cơ bản
                        st.success(f"✅ Import thành công **{last_import.get('success', 0)}** sản phẩm | Mã: **{last_import.get('ma_forecast', 'N/A')}**")
                        st.write(f"📅 {last_import.get('week_info', 'N/A')}")
                        
                        # === BẢNG TÓM TẮT THEO VẬT NUÔI ===
                        if 'animal_summary' in last_import and last_import['animal_summary']:
                            animal_summary = last_import['animal_summary']
                            total_kg = sum(animal_summary.values())
                            
                            col_text, col_chart = st.columns([1, 1])
                            
                            with col_text:
                                st.write("**📋 Tóm tắt sản lượng:**")
                                # Hiển thị theo thứ tự giảm dần
                                sorted_animals = sorted(animal_summary.items(), key=lambda x: x[1], reverse=True)
                                for animal, kg in sorted_animals:
                                    if kg > 0:
                                        pct = (kg / total_kg * 100) if total_kg > 0 else 0
                                        st.write(f"**{animal}:** {kg:,.0f} kg ({pct:.1f}%)")
                                
                                st.write(f"**TỔNG CỘNG:** {total_kg:,.0f} kg ({total_kg/1000:,.1f} tấn)")
                            
                            with col_chart:
                                # Pie chart
                                import plotly.express as px
                                
                                # Chuẩn bị dữ liệu cho pie chart
                                chart_data = [(animal, kg) for animal, kg in sorted_animals if kg > 0]
                                if chart_data:
                                    labels = [item[0] for item in chart_data]
                                    values = [item[1] for item in chart_data]
                                    
                                    fig = px.pie(
                                        names=labels,
                                        values=values,
                                        title=f"Sản lượng {last_import.get('sheet_name', 'N/A')}",
                                        hole=0.3
                                    )
                                    fig.update_traces(textposition='inside', textinfo='percent+label')
                                    fig.update_layout(
                                        showlegend=False,
                                        margin=dict(l=20, r=20, t=40, b=20),
                                        height=300
                                    )
                                    st.plotly_chart(fig, width="stretch")
                        else:
                            if last_import.get('tong_san_luong'):
                                st.write(f"📊 Tổng sản lượng: **{last_import.get('tong_san_luong'):,.1f} tấn**")
                    
                    st.divider()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    import os
                    import json
                    file_path = None
                    
                    # === Load config từ file JSON (persist qua browser refresh) ===
                    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
                    os.makedirs(config_dir, exist_ok=True)
                    config_file = os.path.join(config_dir, 'last_files.json')
                    
                    # Load config nếu chưa có trong session state
                    if 'forecast_last_file_path' not in st.session_state:
                        if os.path.exists(config_file):
                            try:
                                with open(config_file, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                                if 'forecast_last_file_path' in config and os.path.exists(config.get('forecast_last_file_path', '')):
                                    st.session_state.forecast_last_file_path = config['forecast_last_file_path']
                                    st.session_state.forecast_last_file_name = config.get('forecast_last_file_name', 'N/A')
                            except:
                                pass
                    
                    # === Checkbox sử dụng file mặc định (hiển thị trước) ===
                    if 'forecast_last_file_path' in st.session_state:
                        last_path = st.session_state.forecast_last_file_path
                        last_name = st.session_state.get('forecast_last_file_name', 'N/A')
                        
                        if os.path.exists(last_path):
                            # Khởi tạo session state cho checkbox nếu chưa có
                            if 'forecast_use_default_file' not in st.session_state:
                                st.session_state.forecast_use_default_file = True
                            
                            use_default = st.checkbox(
                                f"📁 Sử dụng file mặc định: **{last_name}**",
                                key="forecast_use_default_file"
                            )
                            if use_default:
                                file_path = last_path
                                st.caption(f"📂 Đường dẫn: `{last_path}`")
                    
                    # === File uploader (hiển thị sau) ===
                    st.write("**Chọn file Excel SALEFORECAST**")
                    uploaded = st.file_uploader(
                        "Chọn file Excel SALEFORECAST",
                        type=['xlsx', 'xlsm'],
                        key="forecast_upload",
                        label_visibility="collapsed"
                    )
                    
                    # Nếu có file mới upload, ưu tiên dùng file mới
                    if uploaded:
                        import tempfile
                        import shutil
                        
                        # Giữ nguyên extension gốc của file (.xlsx hoặc .xlsm)
                        original_ext = os.path.splitext(uploaded.name)[1].lower()
                        
                        # Lưu file vào thư mục EXCEL để sử dụng lại
                        excel_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'EXCEL')
                        os.makedirs(excel_dir, exist_ok=True)
                        saved_path = os.path.join(excel_dir, uploaded.name)
                        
                        try:
                            with open(saved_path, 'wb') as f:
                                f.write(uploaded.read())
                            file_path = saved_path
                        except PermissionError:
                            # Nếu file đang được sử dụng, tạo file tạm
                            uploaded.seek(0)  # Reset file pointer
                            with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as f:
                                f.write(uploaded.read())
                                file_path = f.name
                        
                        # Lưu đường dẫn file vào session state
                        st.session_state.forecast_last_file_path = file_path
                        st.session_state.forecast_last_file_name = uploaded.name
                        
                        # === Lưu vào config file để persist qua browser refresh ===
                        try:
                            config = {}
                            if os.path.exists(config_file):
                                with open(config_file, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                            config['forecast_last_file_path'] = file_path
                            config['forecast_last_file_name'] = uploaded.name
                            with open(config_file, 'w', encoding='utf-8') as f:
                                json.dump(config, f, ensure_ascii=False, indent=2)
                        except:
                            pass
                
                if file_path:
                    try:
                        sheets = importer.get_available_sheets(file_path)
                        
                        with col2:
                            selected_sheet = st.selectbox(
                                "📅 Chọn tuần",
                                options=sheets,
                                index=len(sheets)-1 if sheets else 0,
                                help="Mỗi sheet tương ứng với một tuần"
                            )
                        
                        if selected_sheet:
                            st.subheader(f"📋 Preview dữ liệu {selected_sheet}")
                            
                            with st.spinner("Đang đọc dữ liệu..."):
                                preview_df = importer.preview_data(
                                    file_path=file_path,
                                    sheet_name=selected_sheet,
                                    limit=500
                                )
                            
                            if len(preview_df) > 0:
                                # === NÚT LỌC THEO VẬT NUÔI ===
                                ANIMAL_FILTERS = ['Tất cả', 'HEO', 'GÀ', 'BÒ', 'VỊT', 'CÚT', 'DÊ']
                                
                                # Lấy filter hiện tại từ session state
                                if 'forecast_animal_filter' not in st.session_state:
                                    st.session_state.forecast_animal_filter = 'Tất cả'
                                
                                # Tạo các nút lọc
                                btn_cols = st.columns(len(ANIMAL_FILTERS))
                                
                                for i, animal in enumerate(ANIMAL_FILTERS):
                                    with btn_cols[i]:
                                        is_selected = st.session_state.forecast_animal_filter == animal
                                        btn_type = "primary" if is_selected else "secondary"
                                        btn_label = f"🐷 {animal}" if animal == 'Tất cả' else animal
                                        if st.button(btn_label, key=f"forecast_animal_{animal}", type=btn_type, width="stretch"):
                                            st.session_state.forecast_animal_filter = animal
                                            st.rerun()
                                
                                # Lọc dữ liệu theo vật nuôi - lấy từ bảng SanPham
                                # Query danh mục sản phẩm để lấy thông tin vật nuôi
                                sanpham_df = ss.get_columns_data(
                                    table_name='SanPham',
                                    columns=['Tên cám', 'Vật nuôi'],
                                    page_number=1,
                                    rows_per_page=10000
                                )
                                
                                # Merge với preview_df để có cột Vật nuôi
                                # Drop duplicates trước khi merge để tránh nhân đôi rows
                                if not sanpham_df.empty:
                                    sanpham_unique = sanpham_df.drop_duplicates(subset=['Tên cám'], keep='first')
                                    preview_df = preview_df.merge(
                                        sanpham_unique[['Tên cám', 'Vật nuôi']],
                                        on='Tên cám',
                                        how='left'
                                    )
                                
                                # Mapping từ tên button sang giá trị trong database
                                ANIMAL_DB_MAPPING = {
                                    'Tất cả': None,
                                    'HEO': 'H',
                                    'GÀ': 'G',
                                    'BÒ': 'B',
                                    'VỊT': 'V',
                                    'CÚT': 'C',
                                    'DÊ': 'D'
                                }
                                
                                if st.session_state.forecast_animal_filter == 'Tất cả':
                                    display_df = preview_df
                                else:
                                    # Lọc theo vật nuôi từ database (dùng mapping)
                                    db_value = ANIMAL_DB_MAPPING.get(st.session_state.forecast_animal_filter)
                                    if 'Vật nuôi' in preview_df.columns and db_value:
                                        display_df = preview_df[preview_df['Vật nuôi'] == db_value]
                                    else:
                                        display_df = preview_df
                                
                                # Xóa cột Vật nuôi tạm trước khi hiển thị
                                display_df = display_df.drop(columns=['Vật nuôi'], errors='ignore')
                                
                                st.dataframe(
                                    display_df,
                                    width="stretch",
                                    column_config={
                                        'Tên cám': st.column_config.TextColumn('Tên cám', width='medium'),
                                        'Kích cỡ ép viên': st.column_config.TextColumn('Kích cỡ ép viên', width='small'),
                                        'Kích cỡ bao (kg)': st.column_config.TextColumn('Kích cỡ bao (kg)', width='small'),
                                        'Số lượng (tấn)': st.column_config.NumberColumn('Số lượng (tấn)', format='%.1f')
                                    }
                                )
                                
                                st.caption(f"Hiển thị {len(display_df)} sản phẩm")
                                
                                # Tính tổng sản lượng từ display_df (dữ liệu đã lọc)
                                tong_san_luong = display_df['Số lượng (tấn)'].sum() if 'Số lượng (tấn)' in display_df.columns else 0
                                st.write(f"📊 **Tổng sản lượng:** {tong_san_luong:,.1f} tấn")
                                
                                # Lấy tổng sản lượng từ Excel (GRAND TOTAL)
                                grand_total_excel = importer.get_grand_total_from_excel(file_path=file_path, sheet_name=selected_sheet)
                                if grand_total_excel is not None:
                                    st.write(f"📋 **Tổng sản lượng Excel (GRAND TOTAL):** {grand_total_excel:,.1f} tấn")
                                
                                col_btn1, col_btn2 = st.columns([1, 3])
                                
                                with col_btn1:
                                    if st.button("🚀 Import vào Database", type="primary", key="btn_import_forecast"):
                                        with st.spinner(f"Đang import dữ liệu {selected_sheet}..."):
                                            # Sử dụng function mới - lưu vào DatHang và tính chênh lệch
                                            result = importer.import_forecast_to_dathang(
                                                file_path=file_path,
                                                sheet_name=selected_sheet,
                                                nguoi_import=st.session_state.get('username', 'system')
                                            )
                                        
                                        total_imported = result['success'] + result['partial']
                                        
                                        if total_imported > 0 or result['skipped'] > 0:
                                            deleted_msg = ""
                                            if result.get('deleted', 0) > 0:
                                                deleted_msg = f"🗑️ Đã xóa **{result['deleted']}** bản ghi cũ\n\n"
                                            
                                            st.success(
                                                f"{deleted_msg}"
                                                f"✅ Import thành công **{result['success']}** sản phẩm mới!\n\n"
                                                f"🔄 Import một phần **{result['partial']}** sản phẩm (đã trừ số lượng từ Bá Cang/Silo)\n\n"
                                                f"⏭️ Bỏ qua **{result['skipped']}** sản phẩm (đã có đủ từ nguồn khác)\n\n"
                                                f"📦 Mã đặt hàng: **{result['ma_dathang']}**\n\n"
                                                f"📅 {result['week_info']}"
                                            )
                                            st.balloons()
                                            
                                            # Hiển thị chi tiết
                                            if result.get('details'):
                                                with st.expander("📋 Chi tiết import từng sản phẩm", expanded=False):
                                                    details_df = pd.DataFrame(result['details'])
                                                    details_df.columns = ['Tên cám', 'Forecast (kg)', 'Đã có (kg)', 'Import (kg)', 'Trạng thái']
                                                    st.dataframe(details_df, width="stretch")
                                            
                                            # === LƯU VÀO SESSION STATE ===
                                            # Tính toán thống kê theo vật nuôi (sử dụng preview_df đã có cột Vật nuôi)
                                            animal_summary = {}
                                            ANIMAL_LABELS = {'H': 'HEO', 'G': 'GÀ', 'B': 'BÒ', 'V': 'VỊT', 'C': 'CÚT', 'D': 'DÊ'}
                                            
                                            if 'Vật nuôi' in preview_df.columns and 'Số lượng (tấn)' in preview_df.columns:
                                                for db_code, label in ANIMAL_LABELS.items():
                                                    animal_data = preview_df[preview_df['Vật nuôi'] == db_code]
                                                    if len(animal_data) > 0:
                                                        # Chuyển từ tấn sang kg
                                                        animal_summary[label] = animal_data['Số lượng (tấn)'].sum() * 1000
                                            
                                            st.session_state.forecast_last_import = {
                                                'sheet_name': selected_sheet,
                                                'success': result['success'],
                                                'partial': result['partial'],
                                                'skipped': result['skipped'],
                                                'ma_forecast': result['ma_dathang'],
                                                'week_info': result['week_info'],
                                                'tong_san_luong': tong_san_luong,
                                                'animal_summary': animal_summary,
                                                'import_time': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            }
                                            
                                            if result['not_found']:
                                                with st.expander(f"⚠️ Không tìm thấy {len(result['not_found'])} mã cám"):
                                                    for code in result['not_found'][:20]:
                                                        st.text(f"- {code}")
                                                    if len(result['not_found']) > 20:
                                                        st.text(f"... và {len(result['not_found']) - 20} mã khác")
                                                
                                                # Gửi email thông báo
                                                email_sent = send_import_notification(
                                                    not_found_codes=result['not_found'],
                                                    filename=file_path,
                                                    import_type='FORECAST',
                                                    ngay_import=selected_sheet,
                                                    nguoi_import=st.session_state.get('username', 'system')
                                                )
                                                if email_sent:
                                                    st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                                        else:
                                            st.error("❌ Không import được sản phẩm nào!")
                                            if result['errors']:
                                                for err in result['errors']:
                                                    st.error(err)
                                            if result['not_found']:
                                                st.warning(f"Không tìm thấy {len(result['not_found'])} mã cám trong database")
                                                # Gửi email thông báo
                                                email_sent = send_import_notification(
                                                    not_found_codes=result['not_found'],
                                                    filename=file_path,
                                                    import_type='FORECAST',
                                                    ngay_import=selected_sheet,
                                                    nguoi_import=st.session_state.get('username', 'system')
                                                )
                                                if email_sent:
                                                    st.info(f"📧 Đã gửi email thông báo về {len(result['not_found'])} mã SP chưa có dữ liệu tới phinho@cp.com.vn")
                            else:
                                st.info("📅 Tuần này không có dữ liệu forecast")
                                
                    except Exception as e:
                        st.error(f"❌ Lỗi đọc file: {e}")
                        import traceback
                        with st.expander("Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                            
            except ImportError as e:
                st.error(f"❌ Không thể import module: {e}")
        
        # Sub-tab 2: Nhập tay
        with subtab2:
            data = {
                'ID sản phẩm': [None],
                'Số lượng': [0],
                'Ngày lấy': [next_friday],
                'Ghi chú': [None]
            }
            
            df = pd.DataFrame(data)
            
            column_config={
                'ID sản phẩm': st.column_config.SelectboxColumn('ID sản phẩm',options=ds_sanpham,format_func=lambda x: x,width='large'),
                'Số lượng': st.column_config.NumberColumn('Số lượng',min_value=0,step=1,format="%d",width='small'),
                'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY',width='medium'),
                'Ghi chú': st.column_config.TextColumn('Ghi chú',width='large')
            }
            
            df_insert = st.data_editor(df, num_rows="dynamic", width='content', column_config=column_config, key='forecast_manual')
            
            df_insert = df_insert.dropna(subset=['ID sản phẩm'])
            df_insert = df_insert[df_insert['Số lượng'] > 0]
            
            madathang = ss.generate_next_code(tablename='DatHang', column_name='Mã đặt hàng', prefix='DH',num_char=5)
            st.write(f'Mã đặt hàng tự động: **{madathang}**')
            
            df_insert = fn.tachma_df(df_insert,column_names=['ID sản phẩm'],delimiter='|',index=-1)
            df_insert['Mã đặt hàng'] = madathang
            df_insert['Ngày đặt'] = fn.get_vietnam_time().strftime('%Y-%m-%d')
            df_insert['Loại đặt hàng'] = 'Forecast tuần'
            df_insert['Khách vãng lai'] = 0
            df_insert['Người tạo'] = st.session_state.username
            df_insert['Thời gian tạo'] = fn.get_vietnam_time()
            
            st.dataframe(df_insert, width='content')
            
            disabled = not (len(df_insert) > 0)
            
            if st.button("Thêm Forecast tuần", disabled=disabled, type="primary", key='btn_forecast_manual'):
                result = ss.insert_data_to_sql_server(table_name='DatHang',dataframe=df_insert)
                show_notification("Lỗi:", result)
        
        # Sub-tab 3: Import Excel khác
        with subtab3:
            st.info("📋 File Excel cần có các cột: **Code cám**, **Số lượng**, **Ngày lấy** (tùy chọn), **Ghi chú** (tùy chọn)")
            
            uploaded_file = st.file_uploader("Chọn file Excel", type=['xlsx', 'xls'], key='upload_forecast')
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                
                # Xử lý import
                df_processed = process_import_dathang(df, 'Forecast tuần', khach_vang_lai=0)
                
                if df_processed is not None and len(df_processed) > 0:
                    st.dataframe(df_processed, width='content')
                    
                    if st.button("💾 Lưu dữ liệu", type='primary', key='save_import_fc'):
                        result = ss.insert_data_to_sql_server(table_name='DatHang', dataframe=df_processed)
                        show_notification("Lỗi:", result)
        
        
    st.header("2. Danh sách đơn đặt hàng hiện tại")
    
    # Bộ lọc và xóa theo Ngày lấy
    import sqlite3
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])
    
    with col_filter1:
        # Lấy danh sách ngày lấy có trong database
        conn_ngaylay = sqlite3.connect('database_new.db')
        cursor_ngaylay = conn_ngaylay.cursor()
        cursor_ngaylay.execute("""
            SELECT DISTINCT [Ngày lấy] 
            FROM DatHang 
            WHERE [Đã xóa] = 0 AND [Ngày lấy] IS NOT NULL
            ORDER BY [Ngày lấy] DESC
        """)
        ngay_lay_list = ['Tất cả'] + [row[0] for row in cursor_ngaylay.fetchall() if row[0]]
        conn_ngaylay.close()
        
        selected_ngay_lay = st.selectbox(
            "🔍 Lọc theo Ngày lấy",
            options=ngay_lay_list,
            index=0,
            key="filter_ngay_lay_dathang"
        )
    
    with col_filter2:
        st.write("")  # Spacing
    
    with col_filter3:
        if selected_ngay_lay != 'Tất cả':
            if st.button("🗑️ Xóa tất cả", type="secondary", key="btn_delete_by_ngaylay"):
                conn_del = sqlite3.connect('database_new.db')
                cursor_del = conn_del.cursor()
                cursor_del.execute("""
                    UPDATE DatHang 
                    SET [Đã xóa] = 1, [Người sửa] = ?, [Thời gian sửa] = ?
                    WHERE [Đã xóa] = 0 AND [Ngày lấy] = ?
                """, (st.session_state.username, fn.get_vietnam_time().strftime('%Y-%m-%d %H:%M:%S'), selected_ngay_lay))
                deleted_count = cursor_del.rowcount
                conn_del.commit()
                conn_del.close()
                st.success(f"✅ Đã xóa **{deleted_count}** đơn hàng có Ngày lấy = **{selected_ngay_lay}**")
                st.session_state.df_key += 1
                st.rerun()
    
    # Build col_where based on filter
    dathang_col_where = {'Đã xóa': ('=', 0)}
    if selected_ngay_lay != 'Tất cả':
        dathang_col_where['Ngày lấy'] = ('=', selected_ngay_lay)
    
    column_config = {
        'Ngày đặt': st.column_config.DateColumn('Ngày đặt', format='DD/MM/YYYY'),
        'Ngày lấy': st.column_config.DateColumn('Ngày lấy', format='DD/MM/YYYY'),
        'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
        'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss')
    }
    
    dataframe_with_selections(
        table_name="DatHang",
        columns=[
            'ID', 'ID sản phẩm', 'Mã đặt hàng', 'Loại đặt hàng', 'Số lượng', 'Ngày đặt', 'Ngày lấy', 
            'Khách vãng lai', 'Ghi chú', 'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'
        ],
        colums_disable=['ID','Mã đặt hàng','Ngày đặt','Người tạo','Thời gian tạo','Người sửa','Thời gian sửa','Fullname'],
        col_where=dathang_col_where,
        col_order={'ID': 'DESC'},
        joins = [
             {
                'table': 'SanPham',
                'on': {'ID sản phẩm': 'ID'},
                'columns': ['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên'],
                'replace_multi':{'ID sản phẩm':['Code cám','Tên cám','Dạng ép viên','Kích cỡ ép viên']}
            }
        ],
        column_config=column_config,
        key=f'DatHang_{st.session_state.df_key}_{selected_ngay_lay}',
        join_user_info=True,
        allow_select_all=True)
    
    # Section 3: Danh sách Forecast
    st.header("3. Danh sách Forecast hàng tuần")
    
    forecast_column_config = {
        'Ngày bắt đầu': st.column_config.DateColumn('Ngày bắt đầu', format='DD/MM/YYYY'),
        'Ngày kết thúc': st.column_config.DateColumn('Ngày kết thúc', format='DD/MM/YYYY'),
        'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss'),
        'Thời gian sửa': st.column_config.DatetimeColumn('Thời gian sửa', format='DD/MM/YYYY HH:mm:ss'),
        'Số lượng tấn': st.column_config.NumberColumn('Số lượng tấn', format='%.1f')
    }
    
    dataframe_with_selections(
        table_name="Forecast",
        columns=[
            'ID', 'ID sản phẩm', 'Mã forecast', 'Số lượng tấn', 'Tuần',
            'Ngày bắt đầu', 'Ngày kết thúc', 'Ghi chú', 
            'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa'
        ],
        colums_disable=['ID', 'Mã forecast', 'Tuần', 'Ngày bắt đầu', 'Ngày kết thúc', 
                       'Người tạo', 'Thời gian tạo', 'Người sửa', 'Thời gian sửa', 'Fullname'],
        col_where={'Đã xóa': ('=', 0)},
        col_order={'ID': 'DESC'},
        joins=[
            {
                'table': 'SanPham',
                'on': {'ID sản phẩm': 'ID'},
                'columns': ['Code cám', 'Tên cám', 'Dạng ép viên', 'Kích cỡ ép viên'],
                'replace_multi': {'ID sản phẩm': ['Code cám', 'Tên cám', 'Dạng ép viên', 'Kích cỡ ép viên']}
            }
        ],
        column_config=forecast_column_config,
        key=f'Forecast_{st.session_state.df_key}',
        join_user_info=True,
        allow_select_all=True)