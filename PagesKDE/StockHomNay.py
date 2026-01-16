import streamlit as st
from admin.sys_kde_components import *

def app(selected):
    
    # Tabs: Nhập thủ công và Tính toán từ Stock Old + Packing - Sale
    tab1, tab2 = st.tabs(["📝 Nhập thủ công", "🧮 Tính toán tự động"])
    
    with tab2:
        st.header("Tính toán Stock hôm nay")
        
        st.markdown("""
        **Công thức:** Stock hôm nay = Stock Old + Packing - Sale
        
        Hệ thống sẽ:
        1. Lấy dữ liệu từ 3 bảng: Stock Old, Packing, Sale
        2. Tính toán theo từng sản phẩm
        3. Lưu kết quả vào bảng Stock hôm nay
        """)
        
        # Chọn ngày tính toán
        col1, col2 = st.columns(2)
        with col1:
            ngay_tinh = st.date_input("Ngày tính toán", value=fn.get_vietnam_time().date())
        
        with col2:
            st.write("")  # Spacing
        
        # Khởi tạo session state
        if 'calculation_results' not in st.session_state:
            st.session_state.calculation_results = None
        
        # Button tính toán
        if st.button("🧮 Tính toán", type="primary", use_container_width=True):
            import sqlite3
            from datetime import datetime
            
            try:
                conn = sqlite3.connect("database_new.db")
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
                
                for idx, (id_sanpham, code_cam, ten_cam) in enumerate(all_products):
                    # Stock Old
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM StockOld
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                    """, (id_sanpham,))
                    stock_old = cursor.fetchone()[0]
                    
                    # Packing
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM Packing
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                    """, (id_sanpham,))
                    packing = cursor.fetchone()[0]
                    
                    # Sale
                    cursor.execute("""
                        SELECT COALESCE(SUM([Số lượng]), 0)
                        FROM Sale
                        WHERE [ID sản phẩm] = ? AND [Đã xóa] = 0
                    """, (id_sanpham,))
                    sale = cursor.fetchone()[0]
                    
                    # Tính toán
                    stock_hom_nay = stock_old + packing - sale
                    
                    # Chỉ lưu sản phẩm có số lượng > 0
                    if stock_hom_nay > 0:
                        results.append({
                            'id_sanpham': id_sanpham,
                            'code_cam': code_cam,
                            'ten_cam': ten_cam,
                            'stock_old': stock_old,
                            'packing': packing,
                            'sale': sale,
                            'stock_hom_nay': stock_hom_nay
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
                    'stock_hom_nay': 'Stock hôm nay'
                }, inplace=True)
                st.dataframe(
                    df_result[['Code cám', 'Tên cám', 'Stock Old', 'Packing', 'Sale', 'Stock hôm nay']],
                    width='stretch',
                    hide_index=True
                )
            
            # Xác nhận lưu
            st.warning("⚠️ Hành động này sẽ xóa dữ liệu Stock hôm nay cũ và lưu dữ liệu mới!")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Xác nhận Lưu", type="primary", use_container_width=True):
                    import sqlite3
                    from datetime import datetime
                    
                    conn = sqlite3.connect("database_new.db")
                    cursor = conn.cursor()
                    
                    # Xóa dữ liệu cũ
                    cursor.execute("""
                        UPDATE StockHomNay
                        SET [Đã xóa] = 1
                        WHERE [Đã xóa] = 0
                    """)
                    
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
                    
                    ngay_stock = ngay_tinh_saved.strftime('%Y-%m-%d')
                    thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Insert dữ liệu mới
                    for item in results:
                        cursor.execute("""
                            INSERT INTO StockHomNay
                            ([ID sản phẩm], [Mã stock], [Số lượng], [Ngày stock],
                             [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa])
                            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                        """, (
                            item['id_sanpham'],
                            ma_stock,
                            item['stock_hom_nay'],
                            ngay_stock,
                            f"Tính từ: Stock Old({item['stock_old']}) + Packing({item['packing']}) - Sale({item['sale']})",
                            st.session_state.username,
                            thoi_gian_tao
                        ))
                    
                    conn.commit()
                    conn.close()
                    
                    # Xóa session state
                    st.session_state.calculation_results = None
                    
                    st.success(f"🎉 Đã lưu {len(results)} sản phẩm vào Stock hôm nay với mã: **{ma_stock}**")
                    st.balloons()
                    st.rerun()
            
            with col_btn2:
                if st.button("❌ Hủy", use_container_width=True):
                    st.session_state.calculation_results = None
                    st.rerun()
    
    with tab1:
        st.header("1. Stock hôm nay")
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
    
    
    st.header("2. Danh sách stock hôm nay hiện tại")
    
    column_config = {
        'Ngày stock': st.column_config.DateColumn('Ngày stock', format='DD/MM/YYYY'),
        'Thời gian tạo': st.column_config.DatetimeColumn('Thời gian tạo', format='DD/MM/YYYY HH:mm:ss')
    }
    
    dataframe_with_selections(
        table_name="StockHomNay",
        columns=[
            'ID', 'ID sản phẩm', 'Mã stock', 'Số lượng', 'Ngày stock', 'Khách vãng lai', 'Ghi chú',
            'Người tạo', 'Thời gian tạo'
        ],
        colums_disable=['ID','Mã stock','Người tạo','Thời gian tạo'],
        col_where={'Đã xóa': ('=', 0)},
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
        key=f'StockHomNay_{st.session_state.df_key}',
        join_user_info=False)
