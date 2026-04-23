# -*- coding: utf-8 -*-
"""
Module helper để gửi email thông báo khi import dữ liệu có sản phẩm không tìm thấy
Sử dụng chung cho tất cả các importer
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

# Import email utilities
try:
    from utils.email_utils import send_outlook_email
    EMAIL_AVAILABLE = True
except ImportError:
    try:
        from .email_utils import send_outlook_email
        EMAIL_AVAILABLE = True
    except ImportError:
        EMAIL_AVAILABLE = False


def send_import_notification(
    not_found_codes: List[str],
    filename: str,
    import_type: str,
    ngay_import: str = None,
    nguoi_import: str = "system",
    recipient_email: str = "phinho@cp.com.vn"
) -> bool:
    """
    Gửi email thông báo khi có sản phẩm không import được do chưa có dữ liệu
    
    Args:
        not_found_codes: Danh sách mã/tên sản phẩm không tìm thấy
        filename: Tên file đang import
        import_type: Loại import (Stock, Sale, Packing, TonBon, BaCang, Silo, Forecast)
        ngay_import: Ngày import (YYYY-MM-DD hoặc dd/mm/yyyy)
        nguoi_import: Người thực hiện import
        recipient_email: Email nhận thông báo
        
    Returns:
        True nếu gửi email thành công
    """
    if not EMAIL_AVAILABLE:
        print("⚠️ Không thể gửi email: Module email_utils không khả dụng")
        return False
    
    if not not_found_codes:
        return True
    
    # Định dạng ngày
    ngay_display = ngay_import or datetime.now().strftime('%d/%m/%Y')
    if ngay_import and '-' in ngay_import:
        parts = ngay_import.split('-')
        if len(parts) == 3 and len(parts[0]) == 4:  # YYYY-MM-DD
            ngay_display = f"{parts[2]}/{parts[1]}/{parts[0]}"
    
    # Map loại import sang tên tiếng Việt
    import_type_names = {
        'STOCK': 'Stock Daily',
        'FFSTOCK': 'Stock Daily (FFSTOCK)',
        'BAG_REPORT': 'Báo cáo bao bì',
        'SALE': 'Bán hàng (DAILY SALED REPORT)',
        'PACKING': 'Đóng bao (DAILY PACKING)',
        'TONBON': 'Tồn bồn',
        'BACANG': 'Đại lý Bá Cang',
        'SILO': 'Xe bồn Silo',
        'FORECAST': 'Forecast hàng tuần',
        'PRODUCTION': 'Batching (PRODUCTION)'
    }
    import_type_display = import_type_names.get(import_type.upper(), import_type)
    
    # Tạo nội dung email
    subject = f"⚠️ KHSX Import {import_type_display}: {len(not_found_codes)} sản phẩm chưa có dữ liệu"
    
    # Body email
    body_lines = [
        f"Xin chào,",
        f"",
        f"Khi import file {import_type_display}, có {len(not_found_codes)} mã/tên sản phẩm không tìm thấy trong database.",
        f"",
        f"📁 File: {filename}",
        f"📊 Loại: {import_type_display}",
        f"📅 Ngày: {ngay_display}",
        f"👤 Người import: {nguoi_import}",
        f"⏰ Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"",
        f"📋 Danh sách sản phẩm không tìm thấy:",
        f"{'=' * 50}",
    ]
    
    for idx, code in enumerate(not_found_codes, 1):
        body_lines.append(f"   {idx}. {code}")
    
    body_lines.extend([
        f"{'=' * 50}",
        f"",
        f"Vui lòng thêm các sản phẩm này vào bảng SanPham trong database để import đầy đủ.",
        f"",
        f"Trân trọng,",
        f"Hệ thống KHSX B7"
    ])
    
    body = "\n".join(body_lines)
    
    # Gửi email
    try:
        send_outlook_email(
            recipients=[recipient_email],
            subject=subject,
            body=body,
            preferred_sender="phinho@cp.com.vn"
        )
        print(f"📧 Đã gửi email thông báo về {len(not_found_codes)} SP chưa có dữ liệu tới {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False
