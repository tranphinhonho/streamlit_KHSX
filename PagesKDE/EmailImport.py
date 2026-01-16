"""
Trang Streamlit: Nhận email và import FFSTOCK
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import pandas as pd

# Import modules
try:
    from utils.email_receiver import EmailReceiver
    from utils.stock_importer import StockImporter
    from utils.bag_report_importer import BagReportImporter
    from utils.production_importer import ProductionImporter
    EMAIL_AVAILABLE = True
except ImportError as e:
    EMAIL_AVAILABLE = False
    IMPORT_ERROR = str(e)


def app(selected):
    """Main app function"""
    
    st.header("📧 Nhận email Stock Daily")
    st.caption("Tự động nhận email từ dinhnguyen@cp.com.vn và import file FFSTOCK, BAG REPORT")
    
    if not EMAIL_AVAILABLE:
        st.error(f"⚠️ Không thể import module: {IMPORT_ERROR}")
        st.info("Hãy đảm bảo đã cài đặt pywin32: `pip install pywin32`")
        return
    
    # Khởi tạo session state
    if 'email_list' not in st.session_state:
        st.session_state.email_list = []
    if 'production_list' not in st.session_state:
        st.session_state.production_list = []
    if 'import_results' not in st.session_state:
        st.session_state.import_results = []
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📥 Nhận email", "🏭 PRODUCTION (Batching)", "📋 Lịch sử import"])
    
    with tab1:
        render_email_tab()
    
    with tab2:
        render_production_tab()
    
    with tab3:
        render_history_tab()


def render_email_tab():
    """Render tab nhận email"""
    
    # Section 1: Kiểm tra email
    st.subheader("1. Kiểm tra email mới")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        days_back = st.slider(
            "Tìm email trong", 
            min_value=1, 
            max_value=30, 
            value=4,
            help="Số ngày lùi lại để tìm email"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")
        check_btn = st.button("🔍 Kiểm tra email mới", type="primary", use_container_width=True)
    
    if check_btn:
        with st.spinner("Đang kết nối Outlook..."):
            try:
                receiver = EmailReceiver()
                if not receiver.connect():
                    st.error("❌ Không thể kết nối Outlook!")
                    return
                
                emails = receiver.get_stock_emails(days_back=days_back)
                st.session_state.email_list = emails
                st.session_state.receiver = receiver
                
                if emails:
                    st.success(f"✅ Tìm thấy {len(emails)} email có file FFSTOCK/BAG REPORT")
                else:
                    st.warning("⚠️ Không tìm thấy email nào có file FFSTOCK hoặc BAG REPORT")
                    
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())
    
    # Section 2: Danh sách email
    if st.session_state.email_list:
        st.subheader("2. Danh sách email tìm thấy")
        
        importer = StockImporter()
        bag_importer = BagReportImporter()
        
        for idx, email in enumerate(st.session_state.email_list):
            with st.expander(
                f"📧 {email['sender']} - {email['received_time'].strftime('%d/%m/%Y %H:%M')}",
                expanded=(idx == 0)
            ):
                st.write(f"**Subject:** {email['subject']}")
                st.write(f"**Từ:** {email['sender_email']}")
                st.write(f"**Thời gian:** {email['received_time']}")
                
                if email['unread']:
                    st.info("📬 Chưa đọc")
                
                st.write("---")
                st.write("**📎 File đính kèm:**")
                
                for file_info in email['stock_files']:
                    filename = file_info['filename']
                    size_kb = file_info['size'] / 1024
                    
                    # Kiểm tra đã import chưa
                    is_duplicate = importer.check_duplicate(filename)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        # Trích xuất ngày từ filename để hiển thị
                        receiver_temp = st.session_state.get('receiver')
                        if receiver_temp:
                            ngay_file = receiver_temp.extract_date_from_filename(filename)
                            if ngay_file:
                                # Convert YYYY-MM-DD to DD/MM
                                parts = ngay_file.split('-')
                                ngay_hien_thi = f"{parts[2]}/{parts[1]}"
                            else:
                                ngay_hien_thi = None
                        else:
                            ngay_hien_thi = None
                        
                        if is_duplicate:
                            st.write(f"📄 {filename} ({size_kb:.1f} KB)")
                            st.caption("✅ Đã import trước đó")
                        else:
                            st.write(f"📄 **{filename}** ({size_kb:.1f} KB)")
                            if ngay_hien_thi:
                                st.caption(f"🆕 Stock cuối ngày {ngay_hien_thi} - Chưa import")
                            else:
                                st.caption("🆕 Chưa import")
                    
                    with col2:
                        if is_duplicate:
                            # File đã import - hiển thị nút Import lại
                            if st.button(
                                "🔄 Import lại",
                                key=f"reimp_{idx}_{file_info['index']}",
                                use_container_width=True
                            ):
                                download_and_import(email, file_info, overwrite=True)
                        else:
                            if st.button(
                                "⬇️ Download",
                                key=f"dl_{idx}_{file_info['index']}",
                                use_container_width=True
                            ):
                                download_file(email, file_info)
                    
                    with col3:
                        if is_duplicate:
                            # Không cần nút nào khác cho file đã import
                            pass
                        else:
                            if st.button(
                                "🚀 Import",
                                key=f"imp_{idx}_{file_info['index']}",
                                type="primary",
                                use_container_width=True
                            ):
                                download_and_import(email, file_info, overwrite=False)
                
                # Hiển thị BAG REPORT files
                for file_info in email.get('bag_files', []):
                    filename = file_info['filename']
                    size_kb = file_info['size'] / 1024
                    
                    # Kiểm tra đã import chưa
                    is_duplicate = bag_importer.check_duplicate(filename)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        receiver_temp = st.session_state.get('receiver')
                        if receiver_temp:
                            ngay_file = receiver_temp.extract_date_from_filename(filename)
                            if ngay_file:
                                parts = ngay_file.split('-')
                                ngay_hien_thi = f"{parts[2]}/{parts[1]}"
                            else:
                                ngay_hien_thi = None
                        else:
                            ngay_hien_thi = None
                        
                        if is_duplicate:
                            st.write(f"📦 {filename} ({size_kb:.1f} KB)")
                            st.caption("✅ Đã import trước đó")
                        else:
                            st.write(f"📦 **{filename}** ({size_kb:.1f} KB)")
                            if ngay_hien_thi:
                                st.caption(f"🆕 BAG REPORT ngày {ngay_hien_thi} - Chưa import")
                            else:
                                st.caption("🆕 Chưa import")
                    
                    with col2:
                        if is_duplicate:
                            if st.button(
                                "🔄 Import lại",
                                key=f"bag_reimp_{idx}_{file_info['index']}",
                                use_container_width=True
                            ):
                                download_and_import_bag(email, file_info, overwrite=True)
                        else:
                            if st.button(
                                "⬇️ Download",
                                key=f"bag_dl_{idx}_{file_info['index']}",
                                use_container_width=True
                            ):
                                download_file(email, file_info)
                    
                    with col3:
                        if is_duplicate:
                            pass
                        else:
                            if st.button(
                                "🚀 Import",
                                key=f"bag_imp_{idx}_{file_info['index']}",
                                type="primary",
                                use_container_width=True
                            ):
                                download_and_import_bag(email, file_info, overwrite=False)
    
    # Section 3: Kết quả import
    if st.session_state.import_results:
        st.subheader("3. Kết quả import")
        
        for result in st.session_state.import_results[-5:]:  # Hiển thị 5 kết quả gần nhất
            if result.get('skipped'):
                st.warning(f"⚠️ **{result['filename']}**: Đã import trước đó")
            elif result['success'] > 0:
                # Format ngày hiển thị
                ngay_display = ""
                if result.get('ngay_stock'):
                    parts = result['ngay_stock'].split('-')
                    ngay_display = f" | Ngày {parts[2]}/{parts[1]}/{parts[0]}"
                
                # Kiểm tra loại file để hiển thị phù hợp
                if result.get('file_type') == 'BAG_REPORT':
                    st.success(
                        f"✅ **{result['filename']}**: Import {result['success']} dòng bao bì{ngay_display}"
                    )
                else:
                    st.success(
                        f"✅ **{result['filename']}**: Import {result['success']} sản phẩm{ngay_display} | "
                        f"Mã: {result.get('ma_stock_old', 'N/A')}"
                    )
                    
                    # Hiển thị sản phẩm được tự động thêm
                    auto_added = result.get('auto_added', [])
                    if auto_added:
                        with st.expander(f"🆕 Tự động thêm {len(auto_added)} sản phẩm mới"):
                            for prod in auto_added:
                                st.text(f"- {prod['code']} | {prod['ten']} | {prod['kich_co_ep']} | {prod['kich_co_bao']}kg")
                    
                    not_found = result.get('not_found', [])
                    if not_found:
                        with st.expander(f"⚠️ Không tìm thấy {len(not_found)} mã"):
                            for code in not_found[:20]:
                                st.text(f"- {code}")
                            if len(not_found) > 20:
                                st.text(f"... và {len(not_found) - 20} mã khác")
            else:
                st.error(f"❌ **{result['filename']}**: Lỗi import")
                if result.get('errors'):
                    with st.expander("Chi tiết lỗi"):
                        for err in result['errors']:
                            st.text(err)


def render_production_tab():
    """Render tab import PRODUCTION (Batching) từ Sent Items"""
    
    st.subheader("🏭 Import báo cáo Batching từ email Sent")
    st.caption("Tìm file PRODUCTION*.csv từ email đã gửi (mixer2@cp.com.vn hoặc phinho@cp.com.vn)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        days_back = st.slider(
            "Tìm email trong",
            min_value=1,
            max_value=30,
            value=7,
            help="Số ngày lùi lại để tìm email đã gửi",
            key="production_days_back"
        )
    
    with col2:
        st.write("")
        st.write("")
        check_btn = st.button("🔍 Tìm PRODUCTION emails", type="primary", use_container_width=True)
    
    if check_btn:
        with st.spinner("Đang tìm email PRODUCTION trong Sent Items..."):
            try:
                receiver = EmailReceiver()
                if not receiver.connect():
                    st.error("❌ Không thể kết nối Outlook!")
                    return
                
                emails = receiver.get_production_emails(days_back=days_back)
                st.session_state.production_list = emails
                st.session_state.receiver = receiver
                
                if emails:
                    total_files = sum(len(e.get('production_files', [])) for e in emails)
                    st.success(f"✅ Tìm thấy {len(emails)} email với {total_files} file PRODUCTION")
                else:
                    st.warning("⚠️ Không tìm thấy email nào có file PRODUCTION*.csv trong Sent Items")
                    
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())
    
    # Hiển thị danh sách email PRODUCTION
    if st.session_state.production_list:
        st.subheader("📧 Danh sách email PRODUCTION")
        
        prod_importer = ProductionImporter()
        
        for idx, email in enumerate(st.session_state.production_list):
            with st.expander(
                f"📧 {email['subject'][:50]}... - {email['received_time'].strftime('%d/%m/%Y %H:%M')}",
                expanded=(idx == 0)
            ):
                st.write(f"**Subject:** {email['subject']}")
                st.write(f"**Thời gian gửi:** {email['received_time']}")
                
                st.write("---")
                st.write("**📎 File PRODUCTION:**")
                
                for file_info in email.get('production_files', []):
                    filename = file_info['filename']
                    size_kb = file_info['size'] / 1024
                    
                    # Kiểm tra đã import chưa
                    is_duplicate = prod_importer.check_duplicate(filename)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        if is_duplicate:
                            st.write(f"🏭 {filename} ({size_kb:.1f} KB)")
                            st.caption("✅ Đã import trước đó")
                        else:
                            st.write(f"🏭 **{filename}** ({size_kb:.1f} KB)")
                            st.caption("🆕 Chưa import")
                    
                    with col2:
                        if is_duplicate:
                            if st.button(
                                "🔄 Import lại",
                                key=f"prod_reimp_{idx}_{file_info['index']}",
                                use_container_width=True
                            ):
                                download_and_import_production(email, file_info, overwrite=True)
                        else:
                            if st.button(
                                "⬇️ Download",
                                key=f"prod_dl_{idx}_{file_info['index']}",
                                use_container_width=True
                            ):
                                download_file(email, file_info)
                    
                    with col3:
                        if not is_duplicate:
                            if st.button(
                                "🚀 Import",
                                key=f"prod_imp_{idx}_{file_info['index']}",
                                type="primary",
                                use_container_width=True
                            ):
                                download_and_import_production(email, file_info, overwrite=False)


def download_and_import_production(email: dict, file_info: dict, overwrite: bool = False):
    """Download và import file PRODUCTION CSV"""
    try:
        receiver = st.session_state.get('receiver')
        if not receiver:
            receiver = EmailReceiver()
            receiver.connect()
            st.session_state.receiver = receiver
        
        filename = file_info['filename']
        action = "import lại" if overwrite else "import"
        
        download_folder = Path("D:/PYTHON/B7KHSX/downloads")
        existing_file = download_folder / filename
        
        with st.spinner(f"Đang {action} {filename}..."):
            if existing_file.exists():
                save_path = existing_file
            else:
                save_path = receiver.download_attachment(email, file_info)
                
                if not save_path:
                    st.error("❌ Lỗi download file")
                    return
            
            # Import bằng ProductionImporter
            prod_importer = ProductionImporter()
            username = st.session_state.get('username', 'system')
            
            result = prod_importer.import_production(
                file_path=save_path,
                nguoi_import=username,
                overwrite=overwrite
            )
            
            result['filename'] = filename
            result['file_type'] = 'PRODUCTION'
            st.session_state.import_results.append(result)
            
            if result.get('skipped'):
                st.warning(f"⚠️ File đã được import trước đó!")
            elif result['success'] > 0:
                ngay_display = ""
                ngay_sx = result.get('ngay_san_xuat')
                if ngay_sx:
                    parts = ngay_sx.split('-')
                    ngay_display = f" (Ngày SX: {parts[2]}/{parts[1]}/{parts[0]})"
                
                st.success(
                    f"✅ Import PRODUCTION thành công {result['success']} sản phẩm{ngay_display}!"
                )
                
                # Hiển thị sản phẩm không tìm thấy - mở sẵn để dễ xem
                not_found = result.get('not_found', [])
                if not_found:
                    with st.expander(f"⚠️ Không tìm thấy {len(not_found)} mã sản phẩm", expanded=True):
                        for code in not_found[:30]:
                            st.text(f"- {code}")
                        if len(not_found) > 30:
                            st.text(f"... và {len(not_found) - 30} mã khác")
            else:
                st.error(f"❌ Không import được sản phẩm nào")
                if result['errors']:
                    st.write("Lỗi:", result['errors'])
                if result['not_found']:
                    st.write(f"Không tìm thấy: {len(result['not_found'])} mã")
            
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
        import traceback
        with st.expander("Chi tiết lỗi"):
            st.code(traceback.format_exc())


def download_file(email: dict, file_info: dict):
    """Download file từ email"""
    try:
        receiver = st.session_state.get('receiver')
        if not receiver:
            receiver = EmailReceiver()
            receiver.connect()
        
        with st.spinner(f"Đang download {file_info['filename']}..."):
            save_path = receiver.download_attachment(email, file_info)
            
            if save_path:
                st.success(f"✅ Đã download: {save_path}")
            else:
                st.error("❌ Lỗi download file")
                
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")


def download_and_import(email: dict, file_info: dict, overwrite: bool = False):
    """Download và import file
    
    Args:
        overwrite: Nếu True, xóa dữ liệu cũ trước khi import lại
    """
    try:
        receiver = st.session_state.get('receiver')
        if not receiver:
            receiver = EmailReceiver()
            receiver.connect()
            st.session_state.receiver = receiver
        
        filename = file_info['filename']
        action = "import lại" if overwrite else "import"
        
        # Kiểm tra file đã tồn tại trong downloads folder chưa
        download_folder = Path("D:/PYTHON/B7KHSX/downloads")
        existing_file = download_folder / filename
        
        with st.spinner(f"Đang {action} {filename}..."):
            # Nếu file đã tồn tại, dùng file đó
            if existing_file.exists():
                save_path = existing_file
                print(f"📁 Dùng file đã download: {save_path}")
            else:
                # Download từ email
                save_path = receiver.download_attachment(email, file_info)
                
                if not save_path:
                    st.error("❌ Lỗi download file. Thử refresh trang và kiểm tra email lại!")
                    return
            
            # Trích xuất ngày từ filename
            ngay_stock = receiver.extract_date_from_filename(filename)
            
            # Import
            importer = StockImporter()
            
            username = st.session_state.get('username', 'system')
            
            result = importer.import_ffstock(
                file_path=save_path,
                nguoi_import=username,
                ngay_stock=ngay_stock,
                overwrite=overwrite
            )
            
            result['filename'] = filename
            result['ngay_stock'] = ngay_stock
            st.session_state.import_results.append(result)
            
            if result.get('skipped'):
                st.warning(f"⚠️ File đã được import trước đó!")
            elif result['success'] > 0:
                # Format ngày hiển thị
                ngay_display = ""
                if ngay_stock:
                    parts = ngay_stock.split('-')
                    ngay_display = f" (Stock cuối ngày {parts[2]}/{parts[1]}/{parts[0]})"
                
                st.success(
                    f"✅ Import thành công {result['success']} sản phẩm{ngay_display}! "
                    f"Mã Stock Old: {result['ma_stock_old']}"
                )
                st.balloons()
            else:
                st.error(f"❌ Không import được sản phẩm nào")
                if result['errors']:
                    st.write("Lỗi:", result['errors'])
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
        import traceback
        with st.expander("Chi tiết lỗi"):
            st.code(traceback.format_exc())


def download_and_import_bag(email: dict, file_info: dict, overwrite: bool = False):
    """Download và import file BAG REPORT
    
    Args:
        overwrite: Nếu True, xóa dữ liệu cũ trước khi import lại
    """
    try:
        receiver = st.session_state.get('receiver')
        if not receiver:
            receiver = EmailReceiver()
            receiver.connect()
            st.session_state.receiver = receiver
        
        filename = file_info['filename']
        action = "import lại" if overwrite else "import"
        
        download_folder = Path("D:/PYTHON/B7KHSX/downloads")
        existing_file = download_folder / filename
        
        with st.spinner(f"Đang {action} BAG REPORT {filename}..."):
            if existing_file.exists():
                save_path = existing_file
            else:
                save_path = receiver.download_attachment(email, file_info)
                
                if not save_path:
                    st.error("❌ Lỗi download file")
                    return
            
            ngay_stock = receiver.extract_date_from_filename(filename)
            
            # Import bằng BagReportImporter
            bag_importer = BagReportImporter()
            username = st.session_state.get('username', 'system')
            
            result = bag_importer.import_bag_report(
                file_path=save_path,
                nguoi_import=username,
                ngay_stock=ngay_stock,
                overwrite=overwrite
            )
            
            result['filename'] = filename
            result['file_type'] = 'BAG_REPORT'
            st.session_state.import_results.append(result)
            
            if result.get('skipped'):
                st.warning(f"⚠️ File đã được import trước đó!")
            elif result['success'] > 0:
                ngay_display = ""
                if ngay_stock:
                    parts = ngay_stock.split('-')
                    ngay_display = f" (Ngày {parts[2]}/{parts[1]}/{parts[0]})"
                
                st.success(
                    f"✅ Import BAG REPORT thành công {result['success']} dòng{ngay_display}!"
                )
                st.balloons()
            else:
                st.error(f"❌ Không import được dòng nào")
                if result['errors']:
                    st.write("Lỗi:", result['errors'])
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
        import traceback
        with st.expander("Chi tiết lỗi"):
            st.code(traceback.format_exc())


def render_history_tab():
    """Render tab lịch sử import"""
    
    st.subheader("📋 Lịch sử import")
    
    try:
        importer = StockImporter()
        history = importer.get_import_history(limit=50)
        
        if not history:
            st.info("Chưa có lịch sử import nào")
            return
        
        df = pd.DataFrame(history)
        
        # Format columns
        df['ThoiGianImport'] = pd.to_datetime(df['ThoiGianImport'])
        
        st.dataframe(
            df,
            column_config={
                'ID': st.column_config.NumberColumn('ID', width='small'),
                'TenFile': st.column_config.TextColumn('Tên file', width='large'),
                'NgayEmail': st.column_config.DateColumn('Ngày email', format='DD/MM/YYYY'),
                'LoaiFile': st.column_config.TextColumn('Loại', width='small'),
                'SoLuongDong': st.column_config.NumberColumn('Số dòng', format='%d'),
                'ThoiGianImport': st.column_config.DatetimeColumn(
                    'Thời gian import', 
                    format='DD/MM/YYYY HH:mm'
                ),
                'NguoiImport': st.column_config.TextColumn('Người import')
            },
            hide_index=True,
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Lỗi lấy lịch sử: {e}")
