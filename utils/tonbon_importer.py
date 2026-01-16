# -*- coding: utf-8 -*-
"""
Module import dữ liệu Tồn bồn hàng ngày từ file Excel
Đọc dữ liệu từ cột O (Code cám) và P (Số lượng kg) sau khi chạy VBA TongHopBaoCaoCam()
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import time

try:
    import win32com.client as win32
    HAS_WIN32COM = True
except ImportError:
    win32 = None
    HAS_WIN32COM = False


class TonBonImporter:
    """Class xử lý import dữ liệu Tồn bồn từ file Excel"""
    
    # File mặc định
    DEFAULT_FILE = "EXCEL/Báo cáo tồn bồn thành phẩm 01.2026.xlsm"
    
    # Vị trí cột sau khi chạy VBA
    COL_CODE_CAM = 14  # Cột O (index 14)
    COL_SO_LUONG = 15  # Cột P (index 15)
    START_ROW = 2      # Bắt đầu từ dòng 2 (dòng 1 là header)
    
    # Tên VBA macro
    VBA_MACRO_NAME = "TongHopBaoCaoCam"
    
    def __init__(self, db_path: str = "database_new.db"):
        """
        Khởi tạo TonBonImporter
        
        Args:
            db_path: Đường dẫn database SQLite
        """
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Tạo connection đến database"""
        return sqlite3.connect(self.db_path)
    
    def _ensure_import_log_table(self):
        """Tạo bảng EmailImportLog nếu chưa có"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS EmailImportLog (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                TenFile TEXT NOT NULL,
                NgayEmail DATE,
                LoaiFile TEXT NOT NULL,
                SoLuongDong INTEGER DEFAULT 0,
                ThoiGianImport DATETIME DEFAULT CURRENT_TIMESTAMP,
                NguoiImport TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _run_excel_macro(self, file_path: Path, macro_name: str = None) -> bool:
        """
        Mở Excel, chạy VBA macro, lưu file
        
        Args:
            file_path: Đường dẫn file Excel (absolute path)
            macro_name: Tên macro VBA cần chạy
            
        Returns:
            True nếu thành công
        """
        if not HAS_WIN32COM:
            print("❌ Không có win32com - cần cài pywin32")
            return False
        
        macro_name = macro_name or self.VBA_MACRO_NAME
        excel = None
        workbook = None
        
        try:
            # Khởi tạo Excel application
            excel = win32.gencache.EnsureDispatch('Excel.Application')
            excel.Visible = False  # Ẩn Excel
            excel.DisplayAlerts = False  # Tắt cảnh báo
            
            # Mở file (cần đường dẫn tuyệt đối)
            abs_path = str(file_path.resolve())
            print(f"📂 Đang mở file: {abs_path}")
            workbook = excel.Workbooks.Open(abs_path)
            
            # Chạy macro
            print(f"🚀 Đang chạy VBA: {macro_name}...")
            excel.Application.Run(macro_name)
            
            # Lưu file
            workbook.Save()
            print("💾 Đã lưu file")
            
            # Đóng workbook
            workbook.Close(SaveChanges=True)
            workbook = None
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi chạy VBA: {e}")
            return False
            
        finally:
            # Cleanup
            try:
                if workbook:
                    workbook.Close(SaveChanges=False)
            except:
                pass
            try:
                if excel:
                    excel.Quit()
            except:
                pass
    
    def read_direct_from_cells(
        self, 
        file_path: str | Path = None
    ) -> pd.DataFrame:
        """
        Đọc trực tiếp dữ liệu từ các vùng cell cố định ở Sheet 2
        NHANH hơn chạy VBA!
        
        Vùng cell (Sheet 2):
        - A10:C16 (số bồn, code, kg) - Bồn cám bán thành phẩm
        - A21:C38 (số bồn, code, kg) - Bồn cám thành phẩm
        - E10:G15 (số bồn, code, kg) - Bồn cám bán thành phẩm
        - E21:G38 (số bồn, code, kg) - Bồn cám thành phẩm
        
        Returns:
            DataFrame với các cột: Code cám, Số lượng (kg), Số bồn
        """
        file_path = Path(file_path or self.DEFAULT_FILE)
        
        try:
            # Đọc Sheet 2 (index 1)
            df = pd.read_excel(file_path, sheet_name=1, header=None, engine='openpyxl')
            
            data = []
            
            # Các vùng cell cần đọc (row index 0-based)
            # A=0, B=1, C=2, E=4, F=5, G=6
            ranges = [
                # (bon_col, code_col, kg_col, start_row, end_row)
                (0, 1, 2, 9, 16),    # A10:C16 (Bồn cám bán thành phẩm - trái)
                (0, 1, 2, 20, 38),   # A21:C38 (Bồn cám thành phẩm - trái)
                (4, 5, 6, 9, 15),    # E10:G15 (Bồn cám bán thành phẩm - phải)
                (4, 5, 6, 20, 38),   # E21:G38 (Bồn cám thành phẩm - phải)
            ]
            
            for bon_col, code_col, kg_col, start_row, end_row in ranges:
                for row_idx in range(start_row, min(end_row, len(df))):
                    try:
                        bon_val = df.iloc[row_idx, bon_col]
                        code_val = df.iloc[row_idx, code_col]
                        kg_val = df.iloc[row_idx, kg_col]
                        
                        if pd.isna(code_val) or str(code_val).strip() == '':
                            continue
                        
                        # Chuyển code về string 6 chữ số
                        code_str = str(int(float(code_val))).strip()
                        if len(code_str) == 6 and code_str.isdigit():
                            kg = float(kg_val) if not pd.isna(kg_val) else 0
                            
                            # Lấy số bồn (có thể là số hoặc text)
                            if pd.isna(bon_val):
                                so_bon = ''
                            else:
                                so_bon = str(int(float(bon_val))) if isinstance(bon_val, (int, float)) else str(bon_val).strip()
                            
                            if kg > 0:  # Chỉ lấy khi có số lượng
                                data.append({
                                    'Code cám': code_str,
                                    'Số lượng (kg)': kg,
                                    'Số bồn': so_bon
                                })
                    except:
                        continue
            
            # Gộp các mã giống nhau (cộng kg, nối số bồn)
            if data:
                df_result = pd.DataFrame(data)
                # Group và aggregate
                df_grouped = df_result.groupby('Code cám', as_index=False).agg({
                    'Số lượng (kg)': 'sum',
                    'Số bồn': lambda x: ', '.join(sorted(set(str(v) for v in x if v)))  # Nối các bồn
                })
                print(f"📊 Đọc được {len(data)} dòng → {len(df_grouped)} mã (sau gộp)")
                return df_grouped
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Lỗi đọc trực tiếp: {e}")
            return pd.DataFrame()
    
    def run_vba_and_read(
        self, 
        file_path: str | Path = None, 
        limit: int = 50
    ) -> pd.DataFrame:
        """
        Chạy VBA TongHopBaoCaoCam rồi đọc dữ liệu từ cột O-P
        
        Args:
            file_path: Đường dẫn file Excel
            limit: Số dòng tối đa
            
        Returns:
            DataFrame với các cột: Code cám, Số lượng (kg)
        """
        file_path = Path(file_path or self.DEFAULT_FILE)
        
        # Bước 1: Chạy VBA macro
        if not self._run_excel_macro(file_path):
            return pd.DataFrame()
        
        # Đợi Excel đóng hoàn toàn
        time.sleep(1)
        
        # Bước 2: Đọc dữ liệu
        return self.preview_data(file_path, limit=limit)
    
    def get_available_sheets(self, file_path: str | Path = None) -> List[str]:
        """
        Lấy danh sách các sheet có sẵn trong file Excel
        """
        file_path = Path(file_path or self.DEFAULT_FILE)
        
        try:
            xl = pd.ExcelFile(file_path, engine='openpyxl')
            return xl.sheet_names
        except Exception as e:
            print(f"Lỗi đọc file: {e}")
            return []
    
    def preview_data(
        self, 
        file_path: str | Path = None, 
        sheet_name: str = None,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        Xem trước dữ liệu từ file Excel (sau khi chạy VBA)
        
        Args:
            file_path: Đường dẫn file Excel
            sheet_name: Tên sheet (mặc định là sheet đầu tiên)
            limit: Số dòng tối đa
            
        Returns:
            DataFrame với các cột: Code cám, Số lượng (kg)
        """
        file_path = Path(file_path or self.DEFAULT_FILE)
        
        try:
            # Đọc sheet
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
            else:
                df = pd.read_excel(file_path, header=None, engine='openpyxl')
            
            # Lấy dữ liệu từ cột O và P (index 14, 15)
            if len(df.columns) <= self.COL_SO_LUONG:
                print(f"File không đủ cột (cần ít nhất {self.COL_SO_LUONG + 1} cột)")
                return pd.DataFrame()
            
            data = []
            for idx in range(self.START_ROW - 1, min(len(df), self.START_ROW - 1 + limit)):
                row = df.iloc[idx]
                
                code_cam = row.iloc[self.COL_CODE_CAM] if not pd.isna(row.iloc[self.COL_CODE_CAM]) else None
                so_luong = row.iloc[self.COL_SO_LUONG] if not pd.isna(row.iloc[self.COL_SO_LUONG]) else 0
                
                # Chỉ lấy dòng có code hợp lệ (số 6 chữ số)
                if code_cam and str(code_cam).strip():
                    try:
                        # Chuyển về string và làm sạch
                        code_str = str(int(float(code_cam))).strip()
                        if len(code_str) == 6 and code_str.isdigit():
                            data.append({
                                'Code cám': code_str,
                                'Số lượng (kg)': float(so_luong) if so_luong else 0
                            })
                    except:
                        pass
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Lỗi preview: {e}")
            return pd.DataFrame()
    
    def _read_all_data(self, file_path: Path, sheet_name: str = None) -> List[Dict]:
        """
        Đọc toàn bộ dữ liệu từ cột O-P
        
        Returns:
            List các dict: {code_cam, so_luong}
        """
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
            else:
                df = pd.read_excel(file_path, header=None, engine='openpyxl')
            
            if len(df.columns) <= self.COL_SO_LUONG:
                return []
            
            data = []
            for idx in range(self.START_ROW - 1, len(df)):
                row = df.iloc[idx]
                
                code_cam = row.iloc[self.COL_CODE_CAM] if not pd.isna(row.iloc[self.COL_CODE_CAM]) else None
                so_luong = row.iloc[self.COL_SO_LUONG] if not pd.isna(row.iloc[self.COL_SO_LUONG]) else 0
                
                if code_cam and str(code_cam).strip():
                    try:
                        code_str = str(int(float(code_cam))).strip()
                        if len(code_str) == 6 and code_str.isdigit():
                            data.append({
                                'code_cam': code_str,
                                'so_luong': float(so_luong) if so_luong else 0
                            })
                    except:
                        pass
            
            return data
            
        except Exception as e:
            print(f"Lỗi đọc dữ liệu: {e}")
            return []
    
    def _get_product_id(self, cursor, code_cam: str) -> Optional[int]:
        """Tìm ID sản phẩm từ Code cám"""
        cursor.execute("""
            SELECT ID 
            FROM SanPham 
            WHERE TRIM([Code cám]) = ? AND [Đã xóa] = 0
        """, (code_cam.strip(),))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _generate_tonbon_code(self, cursor) -> str:
        """Tạo mã Tồn bồn tự động (TB00001, TB00002...)"""
        cursor.execute("""
            SELECT MAX([Mã tồn bồn]) 
            FROM TonBon 
            WHERE [Mã tồn bồn] LIKE 'TB%'
        """)
        
        result = cursor.fetchone()[0]
        
        if result:
            try:
                last_num = int(result[2:])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        return f"TB{next_num:05d}"
    
    def _delete_old_import(self, cursor, ngay_kiem: str):
        """
        Xóa mềm dữ liệu tồn bồn cũ theo ngày (để import lại)
        
        Args:
            cursor: Database cursor
            ngay_kiem: Ngày kiểm kho (YYYY-MM-DD)
        """
        cursor.execute("""
            UPDATE TonBon 
            SET [Đã xóa] = 1, 
                [Người sửa] = 'system_reimport',
                [Thời gian sửa] = datetime('now')
            WHERE [Ngày kiểm kho] = ? AND [Đã xóa] = 0
              AND [Ghi chú] LIKE '%Import từ%'
        """, (ngay_kiem,))
        
        return cursor.rowcount
    
    def _log_import(
        self, 
        filename: str, 
        loai_file: str,
        so_luong: int,
        ngay_email: Optional[str] = None,
        nguoi_import: Optional[str] = None
    ):
        """Ghi log import vào database"""
        self._ensure_import_log_table()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Thêm timestamp để tránh trùng tên file
        timestamp = datetime.now().strftime('%H%M%S')
        unique_filename = f"{filename}_{timestamp}"
        
        cursor.execute("""
            INSERT INTO EmailImportLog 
            (TenFile, NgayEmail, LoaiFile, SoLuongDong, NguoiImport)
            VALUES (?, ?, ?, ?, ?)
        """, (unique_filename, ngay_email, loai_file, so_luong, nguoi_import))
        
        conn.commit()
        conn.close()
    
    def import_tonbon(
        self,
        file_path: str | Path = None,
        sheet_name: str = None,
        ngay_kiem: str = None,
        nguoi_import: str = "system",
        loai_san_pham: str = "Thành phẩm",
        overwrite: bool = False
    ) -> Dict:
        """
        Import dữ liệu Tồn bồn từ Excel vào database
        
        Args:
            file_path: Đường dẫn file Excel
            sheet_name: Tên sheet (không dùng - đọc từ Sheet 2)
            ngay_kiem: Ngày kiểm kho (YYYY-MM-DD)
            nguoi_import: Username người import
            loai_san_pham: Loại sản phẩm (Thành phẩm / Bán thành phẩm)
            overwrite: Nếu True, xóa dữ liệu cũ trước khi import
            
        Returns:
            Dict kết quả: {success, not_found, errors, total}
        """
        file_path = Path(file_path or self.DEFAULT_FILE)
        filename = file_path.name
        
        # Ngày mặc định là hôm nay
        if not ngay_kiem:
            ngay_kiem = datetime.now().strftime('%Y-%m-%d')
        
        # Đọc dữ liệu trực tiếp từ Sheet 2
        df = self.read_direct_from_cells(file_path)
        
        if len(df) == 0:
            return {
                'success': 0,
                'not_found': [],
                'errors': ["Không tìm thấy dữ liệu trong file"],
                'total': 0
            }
        
        print(f"📊 Đọc được {len(df)} mã sản phẩm từ file")
        
        # Kết nối database
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Xóa dữ liệu cũ nếu overwrite
        if overwrite:
            deleted = self._delete_old_import(cursor, ngay_kiem)
            if deleted > 0:
                print(f"🗑️ Đã xóa mềm {deleted} record cũ (ngày {ngay_kiem})")
        
        thoi_gian_tao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        success_count = 0
        not_found = []
        errors = []
        
        # Lặp qua DataFrame
        for _, row in df.iterrows():
            try:
                code_cam = row['Code cám']
                so_luong = row['Số lượng (kg)']
                so_bon = row.get('Số bồn', 'Import')  # Lấy số bồn từ data
                
                # Tìm ID sản phẩm
                id_sanpham = self._get_product_id(cursor, code_cam)
                
                if not id_sanpham:
                    not_found.append(code_cam)
                    continue
                
                # Bỏ qua nếu số lượng = 0
                if so_luong <= 0:
                    continue
                
                # Tạo mã tự động
                ma_tonbon = self._generate_tonbon_code(cursor)
                
                # Insert vào TonBon
                cursor.execute("""
                    INSERT INTO TonBon 
                    ([Mã tồn bồn], [Ngày kiểm kho], [ID sản phẩm], 
                     [Loại sản phẩm], [Số lượng (kg)], [Số bồn],
                     [Trạng thái], [Kích cỡ đóng bao], [Ca sản xuất],
                     [Ghi chú], [Người tạo], [Thời gian tạo], [Đã xóa])
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (
                    ma_tonbon,
                    ngay_kiem,
                    id_sanpham,
                    loai_san_pham,
                    so_luong,
                    so_bon if so_bon else 'N/A',  # Số bồn từ Excel
                    'Chờ xử lý',  # Trạng thái mặc định
                    'N/A',
                    'Import',  # Ca = Import
                    f"Import từ {filename}",
                    nguoi_import,
                    thoi_gian_tao
                ))
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"{code_cam}: {e}")
        
        conn.commit()
        conn.close()
        
        # Ghi log
        if success_count > 0:
            self._log_import(
                filename=f"TONBON_{ngay_kiem}_{filename}",
                loai_file='TONBON',
                so_luong=success_count,
                ngay_email=ngay_kiem,
                nguoi_import=nguoi_import
            )
        
        print(f"✅ Import thành công: {success_count}/{len(df)} sản phẩm")
        if not_found:
            print(f"⚠️ Không tìm thấy {len(not_found)} mã: {', '.join(not_found[:5])}...")
        
        return {
            'success': success_count,
            'not_found': not_found,
            'errors': errors,
            'total': len(df),
            'ngay_kiem': ngay_kiem
        }


def test_tonbon_importer():
    """Test function"""
    print("=" * 60)
    print("🔍 TEST TONBON IMPORTER")
    print("=" * 60)
    
    importer = TonBonImporter()
    
    # Test preview
    print("\n1. Preview dữ liệu...")
    df = importer.preview_data()
    
    if len(df) > 0:
        print(f"   ✅ Đọc được {len(df)} dòng dữ liệu")
        print(df.head(10))
    else:
        print("   ⚠️ Không có dữ liệu (chạy VBA TongHopBaoCaoCam() trước)")


if __name__ == "__main__":
    test_tonbon_importer()
