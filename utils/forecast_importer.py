"""
Module import dữ liệu Forecast hàng tuần từ file Excel SALEFORECAST
Parse dữ liệu từ các sheet theo tuần (W1, W2, W3, ...)
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import re


class ForecastImporter:
    """Class xử lý import dữ liệu Forecast từ file Excel SALEFORECAST"""
    
    # Default file path
    DEFAULT_FILE = "EXCEL/W3.(12-17-01-) SALEFORECAST 2026.xlsm"
    
    # Column mapping (0-indexed)
    COL_TEN_CAM = 31      # Cột AF - Tên cám
    COL_KICH_CO_EP = 32   # Cột AG - Kích cỡ ép viên
    COL_KICH_CO_BAO = 33  # Cột AH - Kích cỡ đóng bao
    COL_SO_LUONG_TAN = 34 # Cột AI - Số lượng tấn đặt hàng
    
    # Start row (0-indexed, data starts from row 3 in Excel = row 2 in pandas)
    START_ROW = 2
    
    def __init__(self, db_path: str = "database_new.db"):
        """
        Khởi tạo ForecastImporter
        
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
        # Lấy các sheet bắt đầu bằng W
        week_sheets = [s for s in xl.sheet_names if s.startswith('W')]
        return week_sheets
    
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
            
            ten_cam = row[self.COL_TEN_CAM] if self.COL_TEN_CAM < len(row) else None
            kich_co_ep = row[self.COL_KICH_CO_EP] if self.COL_KICH_CO_EP < len(row) else None
            kich_co_bao = row[self.COL_KICH_CO_BAO] if self.COL_KICH_CO_BAO < len(row) else None
            so_luong_tan = row[self.COL_SO_LUONG_TAN] if self.COL_SO_LUONG_TAN < len(row) else None
            
            # Bỏ qua dòng trống
            if pd.isna(ten_cam) or pd.isna(so_luong_tan):
                continue
            
            # Xử lý số lượng
            try:
                so_luong_val = float(so_luong_tan) if pd.notna(so_luong_tan) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
                
            data.append({
                'Tên cám': str(ten_cam).strip(),
                'Kích cỡ ép viên': kich_co_ep,
                'Kích cỡ bao (kg)': kich_co_bao,
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
        Đọc toàn bộ dữ liệu từ một sheet và gộp các dòng cùng tên cám
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        except Exception:
            return []
        
        # Dictionary để gộp dữ liệu theo tên cám
        aggregated = {}
        
        for idx in range(self.START_ROW, len(df)):
            row = df.iloc[idx]
            
            ten_cam = row[self.COL_TEN_CAM] if self.COL_TEN_CAM < len(row) else None
            kich_co_ep = row[self.COL_KICH_CO_EP] if self.COL_KICH_CO_EP < len(row) else None
            kich_co_bao = row[self.COL_KICH_CO_BAO] if self.COL_KICH_CO_BAO < len(row) else None
            so_luong_tan = row[self.COL_SO_LUONG_TAN] if self.COL_SO_LUONG_TAN < len(row) else None
            
            # Bỏ qua dòng trống
            if pd.isna(ten_cam) or pd.isna(so_luong_tan):
                continue
            
            # Parse số lượng
            try:
                so_luong_val = float(so_luong_tan) if pd.notna(so_luong_tan) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
            
            ten_cam_clean = str(ten_cam).strip()
            
            # Gộp vào dictionary
            if ten_cam_clean in aggregated:
                aggregated[ten_cam_clean]['so_luong_tan'] += so_luong_val
            else:
                aggregated[ten_cam_clean] = {
                    'ten_cam': ten_cam_clean,
                    'kich_co_ep': kich_co_ep,
                    'kich_co_bao': kich_co_bao,
                    'so_luong_tan': so_luong_val
                }
        
        return list(aggregated.values())
    
    def _get_product_id(self, cursor, ten_cam: str) -> Optional[int]:
        """Tìm ID sản phẩm từ Tên cám"""
        cursor.execute("""
            SELECT ID 
            FROM SanPham 
            WHERE TRIM([Tên cám]) = ? AND [Đã xóa] = 0
        """, (ten_cam,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _generate_forecast_code(self, cursor) -> str:
        """Tạo mã Forecast tự động (FC00001, FC00002...)"""
        cursor.execute("""
            SELECT MAX([Mã forecast]) 
            FROM Forecast 
            WHERE [Mã forecast] LIKE 'FC%'
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
            
        return f"FC{next_num:05d}"
    
    def _parse_week_info(self, sheet_name: str) -> tuple:
        """
        Parse thông tin tuần từ tên sheet
        VD: "W3.12-17-01-2026" -> (3, "2026-01-12", "2026-01-17")
        """
        # Tìm số tuần
        week_match = re.search(r'W(\d+)', sheet_name)
        week_num = int(week_match.group(1)) if week_match else 1
        
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
            
        return week_num, date_start, date_end
    
    def _delete_forecast_by_week(self, cursor, sheet_name: str) -> int:
        """
        Xóa tất cả forecast của tuần cụ thể
        """
        cursor.execute("""
            SELECT COUNT(*) FROM Forecast 
            WHERE [Ghi chú] LIKE ? 
            AND [Đã xóa] = 0
        """, (f'%{sheet_name}%',))
        count = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE Forecast 
            SET [Đã xóa] = 1 
            WHERE [Ghi chú] LIKE ? 
            AND [Đã xóa] = 0
        """, (f'%{sheet_name}%',))
        
        return count
    
    def _ensure_forecast_table(self, cursor):
        """Tạo bảng Forecast nếu chưa có"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Forecast (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                [ID sản phẩm] INTEGER,
                [Mã forecast] TEXT,
                [Số lượng tấn] REAL,
                [Tuần] INTEGER,
                [Ngày bắt đầu] DATE,
                [Ngày kết thúc] DATE,
                [Ghi chú] TEXT,
                [Người tạo] TEXT,
                [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
                [Người sửa] TEXT,
                [Thời gian sửa] DATETIME,
                [Đã xóa] INTEGER DEFAULT 0
            )
        """)
    
    def import_forecast_data(
        self,
        file_path: str | Path = None,
        sheet_name: str = None,
        nguoi_import: str = "system"
    ) -> Dict:
        """
        Import dữ liệu Forecast từ Excel vào database
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
            'ma_forecast': None,
            'week_info': None,
            'deleted': 0
        }
        
        if not sheet_name:
            result['errors'].append("Không tìm thấy sheet hợp lệ")
            return result
        
        try:
            # Parse thông tin tuần
            week_num, date_start, date_end = self._parse_week_info(sheet_name)
            result['week_info'] = f"Tuần {week_num}: {date_start} đến {date_end}"
            
            # Đọc dữ liệu từ sheet
            data = self._read_sheet_data(file_path, sheet_name)
            
            if not data:
                result['errors'].append("Không có dữ liệu hợp lệ trong sheet")
                return result
            
            # Kết nối database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # Tạo bảng nếu chưa có
                self._ensure_forecast_table(cursor)
                
                # Xóa dữ liệu cũ
                deleted_count = self._delete_forecast_by_week(cursor, sheet_name)
                result['deleted'] = deleted_count
                
                # Tạo mã forecast
                ma_forecast = self._generate_forecast_code(cursor)
                result['ma_forecast'] = ma_forecast
                
                thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Import từng dòng
                for item in data:
                    product_id = self._get_product_id(cursor, item['ten_cam'])
                    
                    if not product_id:
                        result['not_found'].append(item['ten_cam'])
                        continue
                    
                    # Insert vào Forecast
                    cursor.execute("""
                        INSERT INTO Forecast 
                        ([ID sản phẩm], [Mã forecast], [Số lượng tấn], [Tuần],
                         [Ngày bắt đầu], [Ngày kết thúc], [Ghi chú], 
                         [Người tạo], [Thời gian tạo], [Đã xóa])
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        product_id,
                        ma_forecast,
                        item['so_luong_tan'],
                        week_num,
                        date_start,
                        date_end,
                        f"Import từ SALEFORECAST {sheet_name}",
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


def test_forecast_importer():
    """Test function"""
    importer = ForecastImporter()
    
    print("=== Test ForecastImporter ===")
    
    print("\n1. Lấy danh sách sheets:")
    sheets = importer.get_available_sheets()
    print(f"   Sheets: {sheets}")
    
    print("\n2. Preview sheet cuối:")
    preview = importer.preview_data(limit=5)
    print(preview)
    
    print("\n=== Test hoàn tất ===")


if __name__ == "__main__":
    test_forecast_importer()
