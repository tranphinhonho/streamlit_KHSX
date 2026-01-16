"""
Module import dữ liệu Xe bồn Silo hàng tuần từ file Excel SILO
Parse dữ liệu từ các sheet theo tuần (VD: 12-17-01-2026)
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import re


class SiloImporter:
    """Class xử lý import dữ liệu Xe bồn Silo từ file Excel"""
    
    # Default file path
    DEFAULT_FILE = "EXCEL/SILO W3-12-17-01-2026.xlsm"
    
    # Column mapping (0-indexed)
    COL_NGAY_LAY = 11     # Cột L - Ngày lấy cám
    COL_TEN_CAM = 12      # Cột M - Tên cám
    COL_SO_LUONG = 13     # Cột N - Số lượng cám cần lấy
    
    # Start row (0-indexed, data starts from row 3 in Excel = row 2 in pandas)
    START_ROW = 2
    
    def __init__(self, db_path: str = "database_new.db"):
        """
        Khởi tạo SiloImporter
        
        Args:
            db_path: Đường dẫn database SQLite
        """
        self.db_path = db_path
    
    def _get_connection(self):
        """Tạo connection đến database"""
        return sqlite3.connect(self.db_path)
    
    def get_available_sheets(self, file_path: str | Path = None) -> List[str]:
        """
        Lấy danh sách các sheet (tuần) có sẵn trong file Excel
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
            
        xl = pd.ExcelFile(file_path)
        # Lấy tất cả sheets có định dạng ngày
        return xl.sheet_names
    
    def preview_data(
        self, 
        file_path: str | Path = None, 
        sheet_name: str = None,
        limit: int = 15
    ) -> pd.DataFrame:
        """
        Xem trước dữ liệu từ một sheet
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
        
        if sheet_name is None:
            sheets = self.get_available_sheets(file_path)
            sheet_name = sheets[-1] if sheets else None
            
        if not sheet_name:
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        except Exception:
            return pd.DataFrame()
        
        data = []
        for idx in range(self.START_ROW, min(len(df), self.START_ROW + limit * 2)):
            row = df.iloc[idx]
            
            ngay_lay = row[self.COL_NGAY_LAY] if self.COL_NGAY_LAY < len(row) else None
            ten_cam = row[self.COL_TEN_CAM] if self.COL_TEN_CAM < len(row) else None
            so_luong = row[self.COL_SO_LUONG] if self.COL_SO_LUONG < len(row) else None
            
            # Bỏ qua dòng trống
            if pd.isna(ten_cam) or pd.isna(so_luong):
                continue
            
            # Xử lý số lượng
            try:
                so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
            
            # Format ngày lấy
            ngay_lay_str = ""
            if pd.notna(ngay_lay):
                if isinstance(ngay_lay, datetime):
                    ngay_lay_str = ngay_lay.strftime('%d/%m/%Y')
                else:
                    ngay_lay_str = str(ngay_lay)
                
            data.append({
                'Ngày lấy': ngay_lay_str,
                'Tên cám': str(ten_cam).strip(),
                'Số lượng (tấn)': so_luong_val
            })
            
            if len(data) >= limit:
                break
        
        return pd.DataFrame(data)
    
    def _read_sheet_data(
        self, 
        file_path: str | Path, 
        sheet_name: str
    ) -> List[Dict]:
        """
        Đọc toàn bộ dữ liệu từ một sheet - mỗi dòng là 1 bản ghi riêng biệt
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        except Exception:
            return []
        
        data = []
        
        for idx in range(self.START_ROW, len(df)):
            row = df.iloc[idx]
            
            ngay_lay = row[self.COL_NGAY_LAY] if self.COL_NGAY_LAY < len(row) else None
            ten_cam = row[self.COL_TEN_CAM] if self.COL_TEN_CAM < len(row) else None
            so_luong = row[self.COL_SO_LUONG] if self.COL_SO_LUONG < len(row) else None
            
            # Bỏ qua dòng trống
            if pd.isna(ten_cam) or pd.isna(so_luong):
                continue
            
            # Parse số lượng (đơn vị tấn)
            try:
                so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
            
            ten_cam_clean = str(ten_cam).strip()
            
            # Format ngày lấy thành YYYY-MM-DD
            ngay_lay_str = None
            if pd.notna(ngay_lay):
                if isinstance(ngay_lay, datetime):
                    ngay_lay_str = ngay_lay.strftime('%Y-%m-%d')
                else:
                    try:
                        ngay_lay_str = str(ngay_lay)
                    except:
                        pass
            
            # Thêm trực tiếp vào list, không gộp
            data.append({
                'ten_cam': ten_cam_clean,
                'ngay_lay': ngay_lay_str,
                'so_luong': so_luong_val
            })
        
        return data
    
    def _get_product_id(self, cursor, ten_cam: str) -> Optional[int]:
        """Tìm ID sản phẩm từ Tên cám"""
        cursor.execute("""
            SELECT ID 
            FROM SanPham 
            WHERE TRIM([Tên cám]) = ? AND [Đã xóa] = 0
        """, (ten_cam,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _generate_dathang_code(self, cursor) -> str:
        """Tạo mã Đặt hàng tự động (DH00001, DH00002...)"""
        cursor.execute("""
            SELECT MAX([Mã đặt hàng]) 
            FROM DatHang 
            WHERE [Mã đặt hàng] LIKE 'DH%'
        """)
        result = cursor.fetchone()[0]
        
        if result:
            try:
                last_num = int(result[2:])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
            
        return f"DH{next_num:05d}"
    
    def _parse_week_info(self, sheet_name: str) -> tuple:
        """
        Parse thông tin tuần từ tên sheet
        VD: "12-17-01-2026" -> (ngày bắt đầu, ngày kết thúc)
        """
        # Tìm ngày tháng năm
        date_match = re.search(r'(\d+)-(\d+)-(\d+)-(\d+)', sheet_name)
        if date_match:
            day_start = int(date_match.group(1))
            day_end = int(date_match.group(2))
            month = int(date_match.group(3))
            year = int(date_match.group(4))
            
            date_start = f"{year}-{month:02d}-{day_start:02d}"
            date_end = f"{year}-{month:02d}-{day_end:02d}"
        else:
            date_start = datetime.now().strftime('%Y-%m-%d')
            date_end = date_start
            
        return date_start, date_end
    
    def _delete_silo_by_sheet(self, cursor, sheet_name: str) -> int:
        """
        Xóa tất cả đặt hàng xe bồn silo của tuần cụ thể
        """
        cursor.execute("""
            SELECT COUNT(*) FROM DatHang 
            WHERE [Ghi chú] LIKE ? 
            AND [Loại đặt hàng] = 'Xe bồn Silo'
            AND [Đã xóa] = 0
        """, (f'%{sheet_name}%',))
        count = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE DatHang 
            SET [Đã xóa] = 1 
            WHERE [Ghi chú] LIKE ? 
            AND [Loại đặt hàng] = 'Xe bồn Silo'
            AND [Đã xóa] = 0
        """, (f'%{sheet_name}%',))
        
        return count
    
    def import_silo_data(
        self,
        file_path: str | Path = None,
        sheet_name: str = None,
        nguoi_import: str = "system"
    ) -> Dict:
        """
        Import dữ liệu Xe bồn Silo từ Excel vào database (bảng DatHang)
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
            
        if sheet_name is None:
            sheets = self.get_available_sheets(file_path)
            sheet_name = sheets[-1] if sheets else None
            
        result = {
            'success': 0,
            'errors': [],
            'not_found': [],
            'ma_dathang': None,
            'week_info': None,
            'deleted': 0
        }
        
        if not sheet_name:
            result['errors'].append("Không tìm thấy sheet hợp lệ")
            return result
        
        try:
            # Parse thông tin tuần
            date_start, date_end = self._parse_week_info(sheet_name)
            result['week_info'] = f"Tuần: {date_start} đến {date_end}"
            
            # Đọc dữ liệu từ sheet
            data = self._read_sheet_data(file_path, sheet_name)
            
            if not data:
                result['errors'].append("Không có dữ liệu hợp lệ trong sheet")
                return result
            
            # Kết nối database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # Xóa dữ liệu cũ
                deleted_count = self._delete_silo_by_sheet(cursor, sheet_name)
                result['deleted'] = deleted_count
                
                # Tạo mã đặt hàng
                ma_dathang = self._generate_dathang_code(cursor)
                result['ma_dathang'] = ma_dathang
                
                thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ngay_dat = datetime.now().strftime('%Y-%m-%d')
                
                # Import từng dòng
                for item in data:
                    product_id = self._get_product_id(cursor, item['ten_cam'])
                    
                    if not product_id:
                        result['not_found'].append(item['ten_cam'])
                        continue
                    
                    # Số lượng (chuyển từ tấn sang kg nếu cần - hiện giữ nguyên tấn)
                    so_luong = item['so_luong']
                    
                    # Insert vào DatHang
                    cursor.execute("""
                        INSERT INTO DatHang 
                        ([ID sản phẩm], [Mã đặt hàng], [Số lượng], [Ngày đặt], [Ngày lấy],
                         [Loại đặt hàng], [Khách vãng lai], [Ghi chú], 
                         [Người tạo], [Thời gian tạo], [Đã xóa])
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        product_id,
                        ma_dathang,
                        so_luong,
                        ngay_dat,
                        item['ngay_lay'],
                        'Xe bồn Silo',
                        0,
                        f"Import từ SILO {sheet_name}",
                        nguoi_import,
                        thoi_gian_tao
                    ))
                    
                    result['success'] += 1
                
                conn.commit()
                
            finally:
                conn.close()
                
        except Exception as e:
            result['errors'].append(str(e))
            
        return result


def test_silo_importer():
    """Test function"""
    importer = SiloImporter()
    
    print("=== Test SiloImporter ===")
    
    print("\n1. Lấy danh sách sheets:")
    sheets = importer.get_available_sheets()
    print(f"   Sheets: {sheets}")
    
    print("\n2. Preview sheet cuối:")
    preview = importer.preview_data(limit=5)
    print(preview)
    
    print("\n=== Test hoàn tất ===")


if __name__ == "__main__":
    test_silo_importer()
