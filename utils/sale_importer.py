"""
Module import dữ liệu Sale từ file Excel DAILY SALED REPORT
Parse dữ liệu từ các sheet theo ngày (1, 2, 3, ..., 31)
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class SaleImporter:
    """Class xử lý import dữ liệu Sale từ file Excel DAILY SALED REPORT"""
    
    # Default file path
    DEFAULT_FILE = "EXCEL/DAILY SALED REPORT THANG 1.2026.xlsm"
    
    # Column mapping (0-indexed)
    COL_TEN_CAM = 28      # Cột AC - Tên cám
    COL_KICH_CO_BAO = 29  # Cột AD - Kích cỡ đóng bao
    COL_SO_LUONG_BAO = 10 # Cột K - Số lượng bao
    COL_SO_LUONG_KG = 12  # Cột M - Số lượng kg
    
    # Start row (0-indexed, data starts from row 3 in Excel = row 2 in pandas)
    START_ROW = 2
    
    def __init__(self, db_path: str = "database_new.db"):
        """
        Khởi tạo SaleImporter
        
        Args:
            db_path: Đường dẫn database SQLite
        """
        self.db_path = db_path
    
    def _get_connection(self):
        """Tạo connection đến database"""
        return sqlite3.connect(self.db_path)
    
    def get_available_sheets(self, file_path: str | Path = None) -> List[str]:
        """
        Lấy danh sách các sheet (ngày) có sẵn trong file Excel
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
            
        xl = pd.ExcelFile(file_path)
        # Chỉ lấy các sheet là số (ngày)
        day_sheets = [s for s in xl.sheet_names if s.isdigit()]
        return sorted(day_sheets, key=lambda x: int(x))
    
    def get_excel_total(
        self, 
        file_path: str | Path = None, 
        sheet_name: str = "1"
    ) -> Optional[float]:
        """
        Lấy giá trị tổng sản lượng từ ô M4 trong Excel
        
        Args:
            file_path: Đường dẫn file Excel
            sheet_name: Tên sheet (ngày)
            
        Returns:
            Giá trị tổng từ ô M4 hoặc None nếu không có
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            # Ô M4 = row index 3, column index 12
            value = df.iloc[3, 12]
            if pd.notna(value):
                # Xử lý trường hợp Date format
                if hasattr(value, 'toordinal'):
                    return float((value - pd.Timestamp('1899-12-31')).days)
                return float(value)
            return None
        except Exception:
            return None
    
    def preview_data(
        self, 
        file_path: str | Path = None, 
        sheet_name: str = "1",
        limit: int = 15
    ) -> pd.DataFrame:
        """
        Xem trước dữ liệu từ một sheet
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        except Exception:
            # Sheet trống hoặc không có dữ liệu
            return pd.DataFrame()
        
        # Kiểm tra số cột tối thiểu cần thiết
        min_cols_required = max(self.COL_TEN_CAM, self.COL_KICH_CO_BAO, self.COL_SO_LUONG_BAO, self.COL_SO_LUONG_KG) + 1
        if len(df.columns) < min_cols_required:
            # File không đúng format, trả về DataFrame rỗng
            return pd.DataFrame()
        
        data = []
        end_row = len(df) if limit is None else min(len(df), self.START_ROW + limit * 2)
        for idx in range(self.START_ROW, end_row):
            row = df.iloc[idx]
            
            ten_cam = row[self.COL_TEN_CAM]
            kich_co_bao = row[self.COL_KICH_CO_BAO]
            so_luong_bao = row[self.COL_SO_LUONG_BAO]
            so_luong_kg = row[self.COL_SO_LUONG_KG]
            
            # Bỏ qua dòng trống
            if pd.isna(ten_cam) or pd.isna(so_luong_kg):
                continue
            
            # Xử lý kích cỡ bao - convert to numeric
            try:
                kich_co_bao_num = float(kich_co_bao)
            except (ValueError, TypeError):
                # Nếu là text (như "Silo"), giữ nguyên nhưng đặt thành text
                kich_co_bao_num = None
            
            # Xử lý số lượng bao - có thể bị định dạng Date trong Excel
            try:
                if pd.notna(so_luong_bao):
                    if hasattr(so_luong_bao, 'toordinal'):
                        so_luong_bao_num = int((so_luong_bao - pd.Timestamp('1899-12-31')).days)
                    elif isinstance(so_luong_bao, (int, float)):
                        so_luong_bao_num = int(so_luong_bao)
                    else:
                        so_luong_bao_num = int(float(str(so_luong_bao)))
                else:
                    so_luong_bao_num = 0
            except (ValueError, TypeError):
                so_luong_bao_num = 0
            
            # Xử lý số lượng kg - có thể bị định dạng Date trong Excel
            try:
                if pd.notna(so_luong_kg):
                    if hasattr(so_luong_kg, 'toordinal'):
                        so_luong_kg_val = float((so_luong_kg - pd.Timestamp('1899-12-31')).days)
                    elif isinstance(so_luong_kg, (int, float)):
                        so_luong_kg_val = float(so_luong_kg)
                    else:
                        so_luong_kg_val = float(str(so_luong_kg))
                else:
                    so_luong_kg_val = 0
            except (ValueError, TypeError):
                so_luong_kg_val = 0
                
            data.append({
                'Tên cám': str(ten_cam).strip(),
                'Kích cỡ bao (kg)': kich_co_bao_num if kich_co_bao_num else str(kich_co_bao),
                'Số lượng bao': so_luong_bao_num,
                'Số lượng (kg)': so_luong_kg_val
            })
            
            if limit is not None and len(data) >= limit:
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
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # Kiểm tra số cột tối thiểu cần thiết
        min_cols_required = max(self.COL_TEN_CAM, self.COL_KICH_CO_BAO, self.COL_SO_LUONG_BAO, self.COL_SO_LUONG_KG) + 1
        if len(df.columns) < min_cols_required:
            return []  # File không đúng format
        
        # Dictionary để gộp dữ liệu theo tên cám
        aggregated = {}
        
        for idx in range(self.START_ROW, len(df)):
            row = df.iloc[idx]
            
            ten_cam = row[self.COL_TEN_CAM]
            kich_co_bao = row[self.COL_KICH_CO_BAO]
            so_luong_bao = row[self.COL_SO_LUONG_BAO]
            so_luong_kg = row[self.COL_SO_LUONG_KG]
            
            # Bỏ qua dòng trống
            if pd.isna(ten_cam) or pd.isna(so_luong_kg):
                continue
            

            
            # Parse số lượng kg - xử lý trường hợp Date format
            try:
                if pd.notna(so_luong_kg):
                    if hasattr(so_luong_kg, 'toordinal'):
                        so_luong_kg_val = float((so_luong_kg - pd.Timestamp('1899-12-31')).days)
                    elif isinstance(so_luong_kg, (int, float)):
                        so_luong_kg_val = float(so_luong_kg)
                    else:
                        so_luong_kg_val = float(str(so_luong_kg))
                else:
                    so_luong_kg_val = 0
            except (ValueError, TypeError):
                continue
            
            # Parse số lượng bao - xử lý trường hợp Date format
            try:
                if pd.notna(so_luong_bao):
                    if hasattr(so_luong_bao, 'toordinal'):
                        so_luong_bao_val = int((so_luong_bao - pd.Timestamp('1899-12-31')).days)
                    elif isinstance(so_luong_bao, (int, float)):
                        so_luong_bao_val = int(so_luong_bao)
                    else:
                        so_luong_bao_val = int(float(str(so_luong_bao)))
                else:
                    so_luong_bao_val = 0
            except (ValueError, TypeError):
                so_luong_bao_val = 0
            
            if so_luong_kg_val <= 0:
                continue
            
            ten_cam_clean = str(ten_cam).strip()
            
            # Gộp vào dictionary
            if ten_cam_clean in aggregated:
                aggregated[ten_cam_clean]['so_luong_bao'] += so_luong_bao_val
                aggregated[ten_cam_clean]['so_luong_kg'] += so_luong_kg_val
            else:
                aggregated[ten_cam_clean] = {
                    'ten_cam': ten_cam_clean,
                    'kich_co_bao': kich_co_bao,
                    'so_luong_bao': so_luong_bao_val,
                    'so_luong_kg': so_luong_kg_val
                }
        
        return list(aggregated.values())
    
    def _get_product_id(self, cursor, ten_cam: str) -> Optional[int]:
        """Tìm ID sản phẩm từ Tên cám (case-insensitive)"""
        cursor.execute("""
            SELECT ID 
            FROM SanPham 
            WHERE UPPER(TRIM([Tên cám])) = UPPER(?) AND [Đã xóa] = 0
        """, (ten_cam,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _generate_sale_code(self, cursor) -> str:
        """Tạo mã Sale tự động (SL00001, SL00002...)"""
        cursor.execute("""
            SELECT MAX([Mã sale]) 
            FROM Sale 
            WHERE [Mã sale] LIKE 'SL%'
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
            
        return f"SL{next_num:05d}"
    
    def _delete_sale_by_date(self, cursor, ngay_sale: str) -> int:
        """
        Xóa tất cả sale của ngày cụ thể (import từ DAILY SALED REPORT)
        """
        cursor.execute("""
            SELECT COUNT(*) FROM Sale 
            WHERE [Ngày sale] = ? 
            AND [Ghi chú] LIKE '%Import từ DAILY SALED REPORT%'
            AND [Đã xóa] = 0
        """, (ngay_sale,))
        count = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE Sale 
            SET [Đã xóa] = 1 
            WHERE [Ngày sale] = ? 
            AND [Ghi chú] LIKE '%Import từ DAILY SALED REPORT%'
            AND [Đã xóa] = 0
        """, (ngay_sale,))
        
        return count
    
    def import_sale_data(
        self,
        file_path: str | Path = None,
        sheet_name: str = "1",
        nguoi_import: str = "system",
        ngay_sale: Optional[str] = None,
        year: int = 2026,
        month: int = 1
    ) -> Dict:
        """
        Import dữ liệu Sale từ Excel vào database
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
            
        result = {
            'success': 0,
            'errors': [],
            'not_found': [],
            'ma_sale': None,
            'ngay_sale': None,
            'deleted': 0
        }
        
        try:
            # Tính ngày sale từ sheet name
            if ngay_sale is None:
                day = int(sheet_name)
                ngay_sale = f"{year}-{month:02d}-{day:02d}"
            
            result['ngay_sale'] = ngay_sale
            
            # Đọc dữ liệu từ sheet
            data = self._read_sheet_data(file_path, sheet_name)
            
            if not data:
                result['errors'].append("Không có dữ liệu hợp lệ trong sheet")
                return result
            
            # Kết nối database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # Xóa dữ liệu cũ của ngày này trước
                deleted_count = self._delete_sale_by_date(cursor, ngay_sale)
                result['deleted'] = deleted_count
                
                # Tạo mã sale
                ma_sale = self._generate_sale_code(cursor)
                result['ma_sale'] = ma_sale
                
                thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Import từng dòng
                for item in data:
                    product_id = self._get_product_id(cursor, item['ten_cam'])
                    
                    if not product_id:
                        result['not_found'].append(item['ten_cam'])
                        continue
                    
                    # Insert vào Sale
                    cursor.execute("""
                        INSERT INTO Sale 
                        ([ID sản phẩm], [Mã sale], [Số lượng], [Ngày sale],
                         [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa])
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        product_id,
                        ma_sale,
                        int(item['so_luong_kg']),
                        ngay_sale,
                        f"Import từ DAILY SALED REPORT sheet {sheet_name}.{month}.{year}",
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


def test_sale_importer():
    """Test function"""
    importer = SaleImporter()
    
    print("=== Test SaleImporter ===")
    
    print("\n1. Lấy danh sách sheets:")
    sheets = importer.get_available_sheets()
    print(f"   Có {len(sheets)} sheets: {sheets[:5]}...")
    
    print("\n2. Preview sheet '2':")
    preview = importer.preview_data(sheet_name="2", limit=5)
    print(preview)
    
    print("\n=== Test hoàn tất ===")


if __name__ == "__main__":
    test_sale_importer()
