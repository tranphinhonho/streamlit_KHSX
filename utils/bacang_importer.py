"""
Module import dữ liệu Đại lý Bá Cang hàng tuần từ file Excel KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG
Parse dữ liệu từ 2 bảng trong mỗi sheet
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import re


class BaCangImporter:
    """Class xử lý import dữ liệu Đại lý Bá Cang từ file Excel"""
    
    # Default file path
    DEFAULT_FILE = "EXCEL/KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG 2026.xlsm"
    
    # Column mapping cho Bảng 1 (0-indexed)
    TABLE1_COL_NGAY_LAY = 10    # Cột K - Ngày lấy cám
    TABLE1_COL_TEN_CAM = 11     # Cột L - Tên cám
    TABLE1_COL_SO_BAO = 12      # Cột M - Số bao cám
    TABLE1_COL_SO_LUONG = 13    # Cột N - Số lượng cám (kg)
    
    # Column mapping cho Bảng 2 (0-indexed)
    TABLE2_COL_NGAY_LAY = 17    # Cột R - Ngày lấy cám
    TABLE2_COL_TEN_CAM = 18     # Cột S - Tên cám
    TABLE2_COL_SO_LUONG = 19    # Cột T - Số lượng cám (kg)
    
    # Start row (0-indexed, data starts from row 3 in Excel = row 2 in pandas)
    START_ROW = 2
    
    def __init__(self, db_path: str = "database_new.db"):
        """
        Khởi tạo BaCangImporter
        
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
        return xl.sheet_names
    
    def preview_data(
        self, 
        file_path: str | Path = None, 
        sheet_name: str = None,
        limit: int = 15
    ) -> tuple:
        """
        Xem trước dữ liệu từ một sheet
        Returns: (DataFrame bảng 1, DataFrame bảng 2)
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE
        
        if sheet_name is None:
            sheets = self.get_available_sheets(file_path)
            sheet_name = sheets[-1] if sheets else None
            
        if not sheet_name:
            return pd.DataFrame(), pd.DataFrame()
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        except Exception:
            return pd.DataFrame(), pd.DataFrame()
        
        # Đọc bảng 1
        data1 = []
        for idx in range(self.START_ROW, min(len(df), self.START_ROW + limit * 2)):
            row = df.iloc[idx]
            
            ngay_lay = row[self.TABLE1_COL_NGAY_LAY] if self.TABLE1_COL_NGAY_LAY < len(row) else None
            ten_cam = row[self.TABLE1_COL_TEN_CAM] if self.TABLE1_COL_TEN_CAM < len(row) else None
            so_bao = row[self.TABLE1_COL_SO_BAO] if self.TABLE1_COL_SO_BAO < len(row) else None
            so_luong = row[self.TABLE1_COL_SO_LUONG] if self.TABLE1_COL_SO_LUONG < len(row) else None
            
            if pd.isna(ten_cam) or pd.isna(so_luong):
                continue
            
            try:
                so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
                so_bao_val = int(so_bao) if pd.notna(so_bao) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
            
            ngay_lay_str = ""
            if pd.notna(ngay_lay):
                if isinstance(ngay_lay, datetime):
                    ngay_lay_str = ngay_lay.strftime('%d/%m/%Y')
                else:
                    ngay_lay_str = str(ngay_lay)
                
            data1.append({
                'Ngày lấy': ngay_lay_str,
                'Tên cám': str(ten_cam).strip(),
                'Số bao': so_bao_val,
                'Số lượng (kg)': so_luong_val
            })
            
            if len(data1) >= limit:
                break
        
        # Đọc bảng 2
        data2 = []
        for idx in range(self.START_ROW, min(len(df), self.START_ROW + limit * 2)):
            row = df.iloc[idx]
            
            ngay_lay = row[self.TABLE2_COL_NGAY_LAY] if self.TABLE2_COL_NGAY_LAY < len(row) else None
            ten_cam = row[self.TABLE2_COL_TEN_CAM] if self.TABLE2_COL_TEN_CAM < len(row) else None
            so_luong = row[self.TABLE2_COL_SO_LUONG] if self.TABLE2_COL_SO_LUONG < len(row) else None
            
            if pd.isna(ten_cam) or pd.isna(so_luong):
                continue
            
            try:
                so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
            
            ngay_lay_str = ""
            if pd.notna(ngay_lay):
                if isinstance(ngay_lay, datetime):
                    ngay_lay_str = ngay_lay.strftime('%d/%m/%Y')
                else:
                    ngay_lay_str = str(ngay_lay)
                
            data2.append({
                'Ngày lấy': ngay_lay_str,
                'Tên cám': str(ten_cam).strip(),
                'Số lượng (kg)': so_luong_val
            })
            
            if len(data2) >= limit:
                break
        
        return pd.DataFrame(data1), pd.DataFrame(data2)
    
    def _read_sheet_data(
        self, 
        file_path: str | Path, 
        sheet_name: str
    ) -> List[Dict]:
        """
        Đọc toàn bộ dữ liệu từ cả 2 bảng trong sheet
        Mỗi dòng là 1 bản ghi riêng biệt
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        except Exception:
            return []
        
        data = []
        
        # Đọc bảng 1
        for idx in range(self.START_ROW, len(df)):
            row = df.iloc[idx]
            
            ngay_lay = row[self.TABLE1_COL_NGAY_LAY] if self.TABLE1_COL_NGAY_LAY < len(row) else None
            ten_cam = row[self.TABLE1_COL_TEN_CAM] if self.TABLE1_COL_TEN_CAM < len(row) else None
            so_luong = row[self.TABLE1_COL_SO_LUONG] if self.TABLE1_COL_SO_LUONG < len(row) else None
            
            if pd.isna(ten_cam) or pd.isna(so_luong):
                continue
            
            try:
                so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
            
            ten_cam_clean = str(ten_cam).strip()
            
            ngay_lay_str = None
            if pd.notna(ngay_lay):
                if isinstance(ngay_lay, datetime):
                    ngay_lay_str = ngay_lay.strftime('%Y-%m-%d')
                else:
                    try:
                        ngay_lay_str = str(ngay_lay)
                    except:
                        pass
            
            data.append({
                'ten_cam': ten_cam_clean,
                'ngay_lay': ngay_lay_str,
                'so_luong': so_luong_val,
                'source': 'table1'
            })
        
        # Đọc bảng 2
        for idx in range(self.START_ROW, len(df)):
            row = df.iloc[idx]
            
            ngay_lay = row[self.TABLE2_COL_NGAY_LAY] if self.TABLE2_COL_NGAY_LAY < len(row) else None
            ten_cam = row[self.TABLE2_COL_TEN_CAM] if self.TABLE2_COL_TEN_CAM < len(row) else None
            so_luong = row[self.TABLE2_COL_SO_LUONG] if self.TABLE2_COL_SO_LUONG < len(row) else None
            
            if pd.isna(ten_cam) or pd.isna(so_luong):
                continue
            
            try:
                so_luong_val = float(so_luong) if pd.notna(so_luong) else 0
            except (ValueError, TypeError):
                continue
            
            if so_luong_val <= 0:
                continue
            
            ten_cam_clean = str(ten_cam).strip()
            
            ngay_lay_str = None
            if pd.notna(ngay_lay):
                if isinstance(ngay_lay, datetime):
                    ngay_lay_str = ngay_lay.strftime('%Y-%m-%d')
                else:
                    try:
                        ngay_lay_str = str(ngay_lay)
                    except:
                        pass
            
            data.append({
                'ten_cam': ten_cam_clean,
                'ngay_lay': ngay_lay_str,
                'so_luong': so_luong_val,
                'source': 'table2'
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
    
    def _delete_bacang_by_sheet(self, cursor, sheet_name: str) -> int:
        """
        Xóa tất cả đặt hàng Bá Cang của tuần cụ thể
        """
        cursor.execute("""
            SELECT COUNT(*) FROM DatHang 
            WHERE [Ghi chú] LIKE ? 
            AND [Loại đặt hàng] = 'Đại lý Bá Cang'
            AND [Đã xóa] = 0
        """, (f'%{sheet_name}%',))
        count = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE DatHang 
            SET [Đã xóa] = 1 
            WHERE [Ghi chú] LIKE ? 
            AND [Loại đặt hàng] = 'Đại lý Bá Cang'
            AND [Đã xóa] = 0
        """, (f'%{sheet_name}%',))
        
        return count
    
    def delete_all_bacang_data(self) -> Dict:
        """
        Xóa tất cả dữ liệu Đại lý Bá Cang
        Returns: Dict với số lượng đã xóa và thông báo
        """
        result = {
            'deleted': 0,
            'success': False,
            'message': ''
        }
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Đếm số bản ghi sẽ xóa
            cursor.execute("""
                SELECT COUNT(*) FROM DatHang 
                WHERE [Loại đặt hàng] = 'Đại lý Bá Cang'
                AND [Đã xóa] = 0
            """)
            count = cursor.fetchone()[0]
            
            # Soft delete (đánh dấu đã xóa)
            cursor.execute("""
                UPDATE DatHang 
                SET [Đã xóa] = 1 
                WHERE [Loại đặt hàng] = 'Đại lý Bá Cang'
                AND [Đã xóa] = 0
            """)
            
            conn.commit()
            conn.close()
            
            result['deleted'] = count
            result['success'] = True
            result['message'] = f"Đã xóa {count} bản ghi Đại lý Bá Cang"
            
        except Exception as e:
            result['message'] = str(e)
            
        return result
    
    def import_bacang_data(
        self,
        file_path: str | Path = None,
        sheet_name: str = None,
        nguoi_import: str = "system"
    ) -> Dict:
        """
        Import dữ liệu Đại lý Bá Cang từ Excel vào database (bảng DatHang)
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
            'sheet_name': sheet_name,
            'deleted': 0
        }
        
        if not sheet_name:
            result['errors'].append("Không tìm thấy sheet hợp lệ")
            return result
        
        try:
            # Đọc dữ liệu từ sheet (cả 2 bảng)
            data = self._read_sheet_data(file_path, sheet_name)
            
            if not data:
                result['errors'].append("Không có dữ liệu hợp lệ trong sheet")
                return result
            
            # Kết nối database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # Xóa dữ liệu cũ
                deleted_count = self._delete_bacang_by_sheet(cursor, sheet_name)
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
                        if item['ten_cam'] not in result['not_found']:
                            result['not_found'].append(item['ten_cam'])
                        continue
                    
                    # Số lượng (kg)
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
                        'Đại lý Bá Cang',
                        0,
                        f"Import từ Bá Cang {sheet_name} ({item['source']})",
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


def test_bacang_importer():
    """Test function"""
    importer = BaCangImporter()
    
    print("=== Test BaCangImporter ===")
    
    print("\n1. Lấy danh sách sheets:")
    sheets = importer.get_available_sheets()
    print(f"   Sheets: {sheets}")
    
    print("\n2. Preview sheet cuối:")
    df1, df2 = importer.preview_data(limit=5)
    print("Bảng 1:")
    print(df1)
    print("\nBảng 2:")
    print(df2)
    
    print("\n=== Test hoàn tất ===")


if __name__ == "__main__":
    test_bacang_importer()
