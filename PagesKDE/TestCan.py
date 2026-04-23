from __future__ import annotations

import re
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Dict

import traceback

import pandas as pd
import streamlit as st
from PIL import Image, ImageGrab
from streamlit_paste_button import paste_image_button
import win32com.client

from utils.email_utils import send_outlook_email
from utils.ocr_utils import (
    CROP_BOXES,
    DATE_FORMAT_OPTIONS,
    DEFAULT_DATE_ORDER,
    ocr_regions_from_image,
    to_serializable,
)
from utils.database_utils import (
    init_testcan_tables,
    save_testcan_report,
    get_testcan_reports,
    get_testcan_report_by_id,
    get_testcan_image_bytes,
    delete_testcan_report,
    search_testcan_reports,
    get_testcan_stats,
)

CLIPBOARD_STATE_KEY = "testcan_clipboard_bytes"
OCR_IMAGE_KEY = "testcan_ocr_image"
VALUE_FIELDS = ["502", "505", "508", "574"]
DEFAULT_RECIPIENTS = "doantuan@cp.com.vn"
DEFAULT_SENDER = "mixer2@cp.com.vn"
EMAIL_STATUS_KEY = "testcan_email_status"
DB_PATH = "database_new.db"
DEFAULT_RANGES = {
    "502": (-15, 100.0),
    "505": (10.0, 100.0),
    "508": (950.0, 1050.0),
    "574": (8, 50.0),
}


def _load_image(uploaded_file) -> Image.Image | None:
    try:
        buffer = BytesIO(uploaded_file.getvalue())
        return Image.open(buffer).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Không thể đọc ảnh: {exc}")
        return None


def _serializable_to_dataframe(results: Dict[str, list[dict]]) -> pd.DataFrame:
    datetime_entries = results.get("DATE_TIME", [])
    row = {
        "Thời gian": datetime_entries[0].get("text", "") if datetime_entries else "",
    }
    for field in VALUE_FIELDS:
        entries = results.get(field, [])
        row[field] = entries[0]["text"] if entries else ""
    return pd.DataFrame([row])


def _grab_clipboard_bytes() -> bytes | None:
    data = ImageGrab.grabclipboard()
    if isinstance(data, Image.Image):
        buffer = BytesIO()
        data.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()
    return None


def _render_range_inputs() -> Dict[str, Dict[str, float]]:
    st.subheader("Giới hạn giá trị")
    cols = st.columns(len(VALUE_FIELDS))
    ranges: Dict[str, Dict[str, float]] = {}
    for idx, field in enumerate(VALUE_FIELDS):
        default_min, default_max = DEFAULT_RANGES[field]
        with cols[idx]:
            min_val = st.number_input(
                f"Min {field}", value=float(default_min), key=f"{field}_min", step=1.0
            )
            max_val = st.number_input(
                f"Max {field}", value=float(default_max), key=f"{field}_max", step=1.0
            )
            if max_val <= min_val:
                st.warning(f"{field}: Max phải lớn hơn Min")
            ranges[field] = {"min": min_val, "max": max_val}
    return ranges


def _extract_numeric_value(value: str) -> float | None:
    if not value:
        return None
    cleaned = value.replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def _validate_ranges(row: Dict[str, str], ranges: Dict[str, Dict[str, float]]):
    issues = []
    for field, limits in ranges.items():
        numeric_value = _extract_numeric_value(row.get(field, ""))
        if numeric_value is None:
            issues.append(f"Không đọc được giá trị {field}.")
            continue
        if not (limits["min"] <= numeric_value <= limits["max"]):
            issues.append(
                f"{field}: {numeric_value} nằm ngoài [{limits['min']}, {limits['max']}]."
            )
    return issues


def _build_email_body(row: Dict[str, str]) -> str:
    lines = ["Kết quả Test cân:"]
    for key, value in row.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _save_temp_attachment(image: Image.Image) -> Path:
    """Save PIL image to a temp file and return its path for email attachment."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image.save(tmp, format="PNG")
        return Path(tmp.name)


def _image_to_bytes(image: Image.Image) -> bytes:
    """Convert PIL Image to bytes"""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _render_email_form(row: Dict[str, str], image: Image.Image, current_user: str = "system") -> None:
    """Form gửi email và lưu vào database"""
    st.subheader("📧 Gửi email qua Outlook")
    default_subject = f"Báo cáo Test Cân lúc {row.get('Thời gian', '')}"
    default_body = _build_email_body(row)

    status = st.session_state.get(EMAIL_STATUS_KEY)
    if status:
        if status.get("success"):
            st.success(status["message"])
            st.caption(
                f"From: `{status.get('sender', 'Không xác định')}` → To: `{status.get('delivered_to', '')}`"
            )
            if status.get("log_line"):
                st.code(status["log_line"], language="text")
            if status.get("saved_id"):
                st.info(f"✅ Đã lưu vào database với ID: {status['saved_id']}")
        else:
            st.error(status.get("message", "Không thể gửi email."))
            if status.get("error_detail"):
                st.warning(f"Chi tiết lỗi: {status['error_detail']}")
            if status.get("log_line"):
                st.code(status["log_line"], language="text")
            if status.get("traceback"):
                with st.expander("🔍 Xem chi tiết lỗi"):
                    st.code(status["traceback"], language="text")

    with st.form("email_form"):
        to_raw = st.text_input(
            "Người nhận",
            value=DEFAULT_RECIPIENTS,
            key="email_form_recipients",
        )
        subject = st.text_input("Tiêu đề", value=default_subject)
        body = st.text_area("Nội dung", value=default_body, height=180)
        notes = st.text_input("Ghi chú (tùy chọn)", placeholder="Nhập ghi chú nếu cần...")
        st.caption(f"Email sẽ gửi từ tài khoản Outlook: `{DEFAULT_SENDER}`")
        
        col1, col2 = st.columns(2)
        with col1:
            send_mail = st.form_submit_button("📧 Gửi email tự động", width="stretch")
        with col2:
            display_mail = st.form_submit_button("👁️ Mở trong Outlook", width="stretch", help="Hiển thị email trong Outlook để bạn tự gửi")

    if send_mail or display_mail:
        recipients = [addr.strip() for addr in re.split(r"[;,]", to_raw) if addr.strip()]
        if not recipients:
            st.error("Vui lòng nhập ít nhất một địa chỉ email.")
            return
        
        # Lưu vào database trước
        image_bytes = _image_to_bytes(image)
        
        # Nếu chọn Display, chỉ hiển thị email
        if display_mail:
            try:
                attachment_path = _save_temp_attachment(image)
                
                outlook = win32com.client.Dispatch("Outlook.Application")
                mail = outlook.CreateItem(0)
                
                # Set account
                accounts = outlook.Session.Accounts
                for idx in range(1, accounts.Count + 1):
                    account = accounts.Item(idx)
                    if DEFAULT_SENDER.lower() in getattr(account, "SmtpAddress", "").lower():
                        mail.SendUsingAccount = account
                        break
                
                mail.To = ";".join(recipients)
                mail.Subject = subject
                mail.Body = body
                mail.Attachments.Add(str(attachment_path))
                
                # Display thay vì Send
                mail.Display(False)  # False = không modal
                
                # Lưu vào database
                saved_id = save_testcan_report(
                    datetime_value=row.get('Thời gian', ''),
                    value_502=row.get('502', ''),
                    value_505=row.get('505', ''),
                    value_508=row.get('508', ''),
                    value_574=row.get('574', ''),
                    image_bytes=image_bytes,
                    image_filename=attachment_path.name,
                    created_by=current_user,
                    notes=notes,
                    email_sent=False,
                    email_recipients="",
                    is_valid=True,
                    db_path=DB_PATH
                )
                
                st.session_state[EMAIL_STATUS_KEY] = {
                    "success": True,
                    "message": "✅ Đã mở email trong Outlook. Vui lòng kiểm tra và nhấn Send.",
                    "sender": DEFAULT_SENDER,
                    "delivered_to": ";".join(recipients),
                    "log_line": f"Email displayed → To: {';'.join(recipients)} | Subject: {subject}",
                    "saved_id": saved_id,
                }
                st.rerun()
                return
                
            except Exception as exc:
                st.error(f"❌ Lỗi khi mở email: {exc}")
                with st.expander("Chi tiết"):
                    st.code(traceback.format_exc())
                return
        
        try:
            attachment_path = _save_temp_attachment(image)
            sender, delivered_to = send_outlook_email(
                recipients,
                subject,
                body,
                attachments=[attachment_path],
                preferred_sender=DEFAULT_SENDER,
            )
            
            # Lưu vào database với thông tin email đã gửi
            saved_id = save_testcan_report(
                datetime_value=row.get('Thời gian', ''),
                value_502=row.get('502', ''),
                value_505=row.get('505', ''),
                value_508=row.get('508', ''),
                value_574=row.get('574', ''),
                image_bytes=image_bytes,
                image_filename=attachment_path.name,
                created_by=current_user,
                notes=notes,
                email_sent=True,
                email_recipients=delivered_to,
                is_valid=True,
                db_path=DB_PATH
            )
            
            log_line = (
                f"Outlook send → From: {sender or 'Không xác định'} | To: {delivered_to} | Subject: {subject} | Attachment: {attachment_path.name}"
            )
            st.session_state[EMAIL_STATUS_KEY] = {
                "success": True,
                "message": "Đã gửi email thành công qua Outlook (có đính kèm ảnh).",
                "sender": sender or "Không xác định",
                "delivered_to": delivered_to,
                "log_line": log_line,
                "saved_id": saved_id,
            }
        except Exception as exc:  # noqa: BLE001
            # Vẫn lưu vào database nhưng đánh dấu email chưa gửi
            try:
                saved_id = save_testcan_report(
                    datetime_value=row.get('Thời gian', ''),
                    value_502=row.get('502', ''),
                    value_505=row.get('505', ''),
                    value_508=row.get('508', ''),
                    value_574=row.get('574', ''),
                    image_bytes=image_bytes,
                    image_filename="image.png",
                    created_by=current_user,
                    notes=notes,
                    email_sent=False,
                    email_recipients="",
                    is_valid=True,
                    db_path=DB_PATH
                )
                saved_msg = f" Đã lưu vào database với ID: {saved_id}"
            except Exception:
                saved_msg = ""
            
            error_str = str(exc)
            log_line = f"Outlook send thất bại → To: {recipients} | Subject: {subject}"
            st.session_state[EMAIL_STATUS_KEY] = {
                "success": False,
                "message": f"Không thể gửi email.{saved_msg}",
                "error_detail": error_str,
                "log_line": log_line,
                "traceback": traceback.format_exc(),
            }
        finally:
            st.rerun()


def _render_crop_previews(image: Image.Image, serializable: Dict[str, list[dict]]) -> None:
    labels = list(CROP_BOXES.keys())
    if not labels:
        st.info("Chưa có cấu hình vùng cắt để hiển thị.")
        return

    with st.expander("Ảnh cắt & text OCR", expanded=False):
        chunk_size = 3
        for start in range(0, len(labels), chunk_size):
            chunk = labels[start : start + chunk_size]
            cols = st.columns(len(chunk))
            for col, label in zip(cols, chunk):
                crop = image.crop(CROP_BOXES[label])
                entries = serializable.get(label, [])
                recognized = ", ".join(entry["text"] for entry in entries) or "(trống)"
                with col:
                    st.image(crop, caption=f"Vùng {label}", width="stretch")
                    st.markdown(f"**Text OCR:** `{recognized}`")


def _render_history_view():
    """Hiển thị lịch sử báo cáo đã lưu"""
    st.header("📜 Lịch sử báo cáo Test Cân")
    
    # Thống kê
    stats = get_testcan_stats(DB_PATH)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng báo cáo", stats['total_reports'])
    with col2:
        st.metric("Báo cáo hợp lệ", stats['valid_reports'])
    with col3:
        st.metric("Tuần này", stats.get('this_week', 0))
    with col4:
        st.metric("Mới nhất", stats['latest_datetime'] or "N/A")
    
    st.markdown("---")
    
    # Xuất Excel
    st.subheader("📊 Xuất báo cáo Excel")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_type = st.selectbox(
            "Loại báo cáo",
            ["Tuần này", "Tháng này", "Tùy chỉnh"],
            key="export_type"
        )
    
    with col2:
        if export_type == "Tùy chỉnh":
            from_date = st.date_input("Từ ngày", key="export_from")
        else:
            from_date = None
            st.info(f"Sẽ xuất {export_type.lower()}")
    
    with col3:
        if export_type == "Tùy chỉnh":
            to_date = st.date_input("Đến ngày", key="export_to")
        else:
            to_date = None
            st.empty()
    
    if st.button("📥 Xuất Excel", width="stretch"):
        try:
            from datetime import datetime, timedelta
            import io
            
            # Xác định khoảng thời gian
            if export_type == "Tuần này":
                today = datetime.now()
                start_of_week = today - timedelta(days=today.weekday())
                from_dt = start_of_week.strftime("%Y-%m-%d 00:00:00")
                to_dt = datetime.now().strftime("%Y-%m-%d 23:59:59")
                filename = f"TestCan_Tuan_{start_of_week.strftime('%d%m%Y')}.xlsx"
            elif export_type == "Tháng này":
                today = datetime.now()
                from_dt = today.replace(day=1).strftime("%Y-%m-%d 00:00:00")
                to_dt = datetime.now().strftime("%Y-%m-%d 23:59:59")
                filename = f"TestCan_Thang_{today.strftime('%m%Y')}.xlsx"
            else:
                from_dt = f"{from_date} 00:00:00"
                to_dt = f"{to_date} 23:59:59"
                filename = f"TestCan_{from_date.strftime('%d%m%Y')}_{to_date.strftime('%d%m%Y')}.xlsx"
            
            # Lấy dữ liệu
            reports = search_testcan_reports(
                datetime_from=from_dt,
                datetime_to=to_dt,
                created_by=None,
                is_valid=None,
                limit=1000,
                db_path=DB_PATH
            )
            
            if not reports:
                st.warning("Không có dữ liệu trong khoảng thời gian này")
            else:
                # Tạo DataFrame
                df = pd.DataFrame(reports)
                
                # Chọn và sắp xếp cột
                columns_order = ['ID', 'Datetime', 'Value_502', 'Value_505', 'Value_508', 'Value_574',
                                'Created_By', 'Created_At', 'Notes', 'Is_Valid']
                df = df[[col for col in columns_order if col in df.columns]]
                
                # Đổi tên cột tiếng Việt
                df = df.rename(columns={
                    'ID': 'Mã số',
                    'Datetime': 'Thời gian cân',
                    'Value_502': 'Giá trị 502',
                    'Value_505': 'Giá trị 505',
                    'Value_508': 'Giá trị 508',
                    'Value_574': 'Giá trị 574',
                    'Created_By': 'Người tạo',
                    'Created_At': 'Ngày tạo',
                    'Notes': 'Ghi chú',
                    'Is_Valid': 'Hợp lệ'
                })
                
                # Tạo Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Báo cáo Test Cân', index=False)
                    
                    # Format worksheet
                    worksheet = writer.sheets['Báo cáo Test Cân']
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                output.seek(0)
                
                st.success(f"✅ Đã tạo file Excel với {len(df)} bản ghi")
                st.download_button(
                    label="📥 Tải xuống Excel",
                    data=output.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )
                
        except Exception as e:
            st.error(f"Lỗi khi xuất Excel: {e}")
            with st.expander("Chi tiết lỗi"):
                st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # Tìm kiếm
    with st.expander("🔍 Tìm kiếm", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            search_from = st.date_input("Từ ngày", value=None)
        with col2:
            search_to = st.date_input("Đến ngày", value=None)
        with col3:
            search_user = st.text_input("Người tạo", placeholder="Tất cả")
        
        if st.button("🔍 Tìm kiếm"):
            reports = search_testcan_reports(
                datetime_from=str(search_from) if search_from else None,
                datetime_to=str(search_to) if search_to else None,
                created_by=search_user if search_user else None,
                is_valid=True,
                limit=100,
                db_path=DB_PATH
            )
            st.session_state['search_results'] = reports
    
    # Lấy danh sách báo cáo
    if 'search_results' in st.session_state:
        reports = st.session_state['search_results']
    else:
        reports = get_testcan_reports(limit=50, db_path=DB_PATH)
    
    if not reports:
        st.info("Chưa có báo cáo nào được lưu.")
        return
    
    # Hiển thị danh sách
    st.subheader(f"📋 Danh sách báo cáo ({len(reports)} kết quả)")
    
    for report in reports:
        with st.expander(
            f"🕐 {report['Datetime']} - ID: {report['ID']} - {report['Created_By']}",
            expanded=False
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Thời gian cân:** {report['Datetime']}")
                st.markdown(f"**ID:** {report['ID']}")
                st.markdown(f"**Người tạo:** {report['Created_By']}")
                st.markdown(f"**Ngày tạo:** {report['Created_At']}")
                
                # Giá trị
                st.markdown("**Giá trị:**")
                data = {
                    '502': report['Value_502'],
                    '505': report['Value_505'],
                    '508': report['Value_508'],
                    '574': report['Value_574'],
                }
                df = pd.DataFrame([data])
                st.dataframe(df, hide_index=True)
                
                # Email info
                if report['Email_Sent']:
                    st.success(f"✅ Đã gửi email đến: {report['Email_Recipients']}")
                else:
                    st.info("📧 Chưa gửi email")
                
                if report['Notes']:
                    st.markdown(f"**Ghi chú:** {report['Notes']}")
            
            with col2:
                # Hiển thị hình ảnh
                image_bytes = get_testcan_image_bytes(report['ID'], DB_PATH)
                if image_bytes:
                    image = Image.open(BytesIO(image_bytes))
                    st.image(image, caption=f"Ảnh #{report['ID']}", width=200)
                    
                    # Nút tải xuống
                    st.download_button(
                        label="📥 Tải ảnh",
                        data=image_bytes,
                        file_name=f"testcan_{report['ID']}_{report['Datetime'].replace(':', '-')}.png",
                        mime="image/png",
                        key=f"download_{report['ID']}"
                    )
            
            # Nút xóa
            if st.button(f"🗑️ Xóa báo cáo #{report['ID']}", key=f"delete_{report['ID']}"):
                if delete_testcan_report(report['ID'], DB_PATH):
                    st.success(f"Đã xóa báo cáo #{report['ID']}")
                    st.rerun()
                else:
                    st.error("Không thể xóa báo cáo")


def app(selected):
    # Khởi tạo database tables nếu chưa có
    init_testcan_tables(DB_PATH)
    
    # Lấy username hiện tại (nếu có authentication)
    current_user = st.session_state.get('username', 'system')
    
    # Tabs: OCR và History
    tab1, tab2 = st.tabs(["📊 Test Cân OCR", "📜 Lịch sử"])
    
    with tab1:
        st.header(selected)
        st.markdown(
            "**Cách dán ảnh từ clipboard:**"
        )
        st.info("1️⃣ Copy ảnh (Ctrl+C) → 2️⃣ Click nút đỏ bên dưới → 3️⃣ Paste (Ctrl+V) vào vùng nút → 4️⃣ Nhấn Submit")

        if CLIPBOARD_STATE_KEY not in st.session_state:
            st.session_state[CLIPBOARD_STATE_KEY] = None

        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Sử dụng streamlit-paste-button
            paste_result = paste_image_button(
                label="📋 Dán ảnh (Click + Ctrl+V)",
                text_color="#ffffff",
                background_color="#FF0000",
                hover_background_color="#CC0000",
                key="paste_button_testcan",
                errors="ignore"
            )
            
            if paste_result is not None and paste_result.image_data is not None:
                # Convert PIL Image to bytes
                buffer = BytesIO()
                paste_result.image_data.save(buffer, format="PNG")
                st.session_state[CLIPBOARD_STATE_KEY] = buffer.getvalue()
                st.success("✅ Đã lấy ảnh!")
        
        with col2:
            # Fallback: Nút backup dùng ImageGrab (chỉ hoạt động trên server)
            if st.button("🔄 Dán từ clipboard (backup)", help="Phương pháp backup - lấy ảnh trực tiếp từ clipboard Windows"):
                clipboard_bytes = _grab_clipboard_bytes()
                if clipboard_bytes:
                    st.session_state[CLIPBOARD_STATE_KEY] = clipboard_bytes
                    st.success("✅ Đã lấy ảnh từ clipboard!")
                else:
                    st.warning("⚠️ Không tìm thấy ảnh trong clipboard. Hãy copy ảnh trước (Ctrl+C).")

        if st.session_state.get(CLIPBOARD_STATE_KEY):
            st.image(
                Image.open(BytesIO(st.session_state[CLIPBOARD_STATE_KEY])),
                caption="Bản xem trước từ clipboard",
                width=300,
            )

        with st.form("ocr_form"):
            date_order = st.selectbox(
                "Định dạng ngày trong ảnh",
                options=DATE_FORMAT_OPTIONS,
                index=DATE_FORMAT_OPTIONS.index(DEFAULT_DATE_ORDER),
                help="mdy = tháng/ngày/năm, dmy = ngày/tháng/năm, ymd = năm/tháng/ngày",
            )
            range_config = _render_range_inputs()
            uploaded_file = st.file_uploader(
                "Ảnh từ cân", type=["png", "jpg", "jpeg"], accept_multiple_files=False
            )
            submitted = st.form_submit_button("Submit")

        if not submitted:
            st.info("Chọn hoặc dán một ảnh rồi nhấn Submit để xem kết quả.")
            return

        image: Image.Image | None = None
        debug_source = ""
        if uploaded_file is not None:
            image = _load_image(uploaded_file)
            debug_source = uploaded_file.name
        elif st.session_state.get(CLIPBOARD_STATE_KEY):
            image = Image.open(BytesIO(st.session_state[CLIPBOARD_STATE_KEY])).convert("RGB")
            debug_source = "clipboard"
        else:
            st.warning("Vui lòng tải ảnh hoặc bấm nút dán ảnh trước khi Submit.")
            return

        if image is None:
            return

        st.subheader("Ảnh đã nhận")
        st.caption(f"Nguồn: {debug_source or 'n/a'}")
        st.image(image, caption="Xem lại ảnh trước khi OCR", width=300)

        with st.spinner("Đang nhận diện chữ..."):
            ocr_raw = ocr_regions_from_image(image)
            serializable = to_serializable(ocr_raw, date_order=date_order)

        st.subheader("Kết quả Test cân")
        df = _serializable_to_dataframe(serializable)
        st.dataframe(df, width="stretch")
        st.caption("Bảng chỉ giữ 5 trường yêu cầu: Thời gian và 4 mã 502/505/508/574.")

        _render_crop_previews(image, serializable)

        row = df.iloc[0].to_dict()
        issues = _validate_ranges(row, range_config)
        
        st.markdown("---")
        
        # Nút lưu nhanh (không gửi email)
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("💾 Lưu nhanh", help="Lưu kết quả test cân vào database (không gửi email)"):
                try:
                    image_bytes = _image_to_bytes(image)
                    saved_id = save_testcan_report(
                        datetime_value=row.get('Thời gian', ''),
                        value_502=row.get('502', ''),
                        value_505=row.get('505', ''),
                        value_508=row.get('508', ''),
                        value_574=row.get('574', ''),
                        image_bytes=image_bytes,
                        image_filename=f"testcan_{row.get('Thời gian', '').replace(':', '-').replace(' ', '_')}.png",
                        created_by=current_user,
                        notes="",
                        email_sent=False,
                        email_recipients="",
                        is_valid=len(issues) == 0,
                        db_path=DB_PATH
                    )
                    st.success(f"✅ Đã lưu vào database với ID: {saved_id}")
                    st.info("💡 Xem trong tab 'Lịch sử' và xuất Excel theo tuần/tháng")
                except Exception as e:
                    st.error(f"❌ Lỗi khi lưu: {e}")
        
        if issues:
            st.error("\n".join(issues))
            st.warning("⚠️ Giá trị chưa hợp lệ nhưng vẫn có thể lưu hoặc gửi email.")
        else:
            st.success("✅ Tất cả giá trị nằm trong giới hạn cho phép.")
        
        # Form gửi email (luôn hiển thị)
        _render_email_form(row, image, current_user)

        with st.expander("Chi tiết vùng cắt (CROP_BOXES)"):
            st.json(CROP_BOXES)
    
    with tab2:
        _render_history_view()
