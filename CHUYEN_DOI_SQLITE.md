# Hướng Dẫn Chuyển Đổi Từ SQL Server Sang SQLite

## Tóm Tắt Các Thay Đổi

Dự án **B5-SQLite_Database** đã được chuyển đổi hoàn toàn từ SQL Server sang SQLite để đơn giản hóa việc triển khai và quản lý database.

---

## 1. Các File Đã Được Tạo Mới

### `admin/sys_sqlite.py`
- File chính chứa tất cả các hàm thao tác với SQLite database
- Thay thế hoàn toàn cho `admin/sys_sql_server.py`
- Các hàm chính:
  - `connect_db()`: Kết nối đến SQLite database
  - `query_database_sqlite()`: Thực thi truy vấn SQL
  - `get_columns_data()`: Lấy dữ liệu từ bảng với các tùy chọn lọc, sắp xếp, join
  - `insert_data_to_table()`: Chèn dữ liệu vào bảng
  - `update_database_from_dataframe()`: Cập nhật database từ DataFrame
  - `delete_data_from_table_by_ids()`: Đánh dấu xóa bản ghi
  - `get_table_columns()`: Lấy danh sách cột của bảng
  - `generate_create_table_query_sqlite()`: Tạo câu lệnh CREATE TABLE
  - Và nhiều hàm khác...

---

## 2. Các File Đã Được Cập Nhật

### `admin/config.json`
**Trước:**
```json
{
    "server": "42.96.15.70",
    "database": "PVD_05",
    "username": "tranphinho",
    "password": "nho123"
}
```

**Sau:**
```json
{
    "database_path": "../database.db"
}
```
- Chỉ cần đường dẫn đến file SQLite database
- Database sẽ được tạo tự động nếu chưa tồn tại

### `main.py`
- Thay đổi import: `import admin.sys_sqlite as ss` (thay vì `sys_sql_server`)
- Cập nhật các truy vấn SQL:
  - `query_database_sql_server()` → `query_database_sqlite()`
  - Thay đổi cú pháp SQL từ T-SQL (SQL Server) sang SQLite:
    - `SELECT TOP 1` → `SELECT ... LIMIT 1`
    - `LTRIM(RTRIM(...))` → `TRIM(...)`
    - Loại bỏ tiền tố `N` trước chuỗi Unicode

### `admin/config.py`
- Import: `sys_sqlite` thay vì `sys_sql_server`
- Cập nhật câu truy vấn kiểm tra bảng:
  - SQL Server: `INFORMATION_SCHEMA.TABLES`
  - SQLite: `sqlite_master`
- Thay đổi kiểu dữ liệu:
  - `NVARCHAR(255)` → `TEXT`
  - `NVARCHAR(MAX)` → `TEXT`

### `admin/DoiMatKhau.py`
- Import: `sys_sqlite` thay vì `sys_sql_server`

### `admin/sys_VaiTro.py`
- Import: `sys_sqlite` thay vì `sys_sql_server`

### `PagesKDE/Tinh.py`
- Import: `sys_sqlite` thay vì `sys_sql_server`

### `requirements.txt`
- Thêm: `bcrypt` (để mã hóa mật khẩu)
- Thêm: `streamlit_antd_components` (nếu chưa có)
- **Không cần** `pyodbc` nữa vì SQLite là built-in trong Python

---

## 3. Những Khác Biệt Chính Giữa SQL Server và SQLite

### Kiểu Dữ Liệu
| SQL Server | SQLite | Ghi Chú |
|------------|--------|---------|
| NVARCHAR(n) | TEXT | SQLite không giới hạn độ dài |
| VARCHAR(n) | TEXT | |
| INT, BIGINT | INTEGER | |
| FLOAT, REAL | REAL | |
| DECIMAL, MONEY | NUMERIC | |
| DATETIME | DATETIME | SQLite lưu dạng text hoặc số |
| BIT | INTEGER | 0 hoặc 1 |

### Cú Pháp SQL
| SQL Server | SQLite | Mục đích |
|------------|--------|----------|
| `SELECT TOP n` | `SELECT ... LIMIT n` | Giới hạn số dòng |
| `GETDATE()` | `CURRENT_TIMESTAMP` | Lấy thời gian hiện tại |
| `IDENTITY(1,1)` | `AUTOINCREMENT` | Tự động tăng |
| `LTRIM(RTRIM(x))` | `TRIM(x)` | Xóa khoảng trắng |
| `N'chuỗi'` | `'chuỗi'` | SQLite không cần tiền tố N |
| `INFORMATION_SCHEMA` | `sqlite_master` | Metadata |

### Ràng Buộc và Index
- SQLite **không hỗ trợ** filtered index (index có điều kiện WHERE)
- SQLite **không hỗ trợ** ALTER COLUMN (thay đổi kiểu dữ liệu cột)
- SQLite **không hỗ trợ** DROP COLUMN trực tiếp (cần tạo bảng mới và copy dữ liệu)

---

## 4. Cách Sử Dụng

### Bước 1: Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### Bước 2: Cấu Hình Database
File `admin/config.json` đã được cấu hình sẵn với đường dẫn:
```json
{
    "database_path": "../database.db"
}
```
Database sẽ được tạo tự động tại `d:\PVD_Full\B5-SQLite_Database\database.db`

### Bước 3: Chạy Ứng Dụng
```bash
streamlit run main.py
```

### Bước 4: Khởi Tạo Dữ Liệu
Nếu đây là lần chạy đầu tiên, bạn cần:
1. Tạo các bảng hệ thống thông qua menu "Admin KDE" → "Tạo bảng"
2. Thêm người dùng đầu tiên thông qua "Admin KDE" → "Thêm users"
3. Cấu hình vai trò và chức năng

---

## 5. Migration Dữ Liệu Từ SQL Server (Nếu Cần)

Nếu bạn đã có dữ liệu trên SQL Server và muốn chuyển sang SQLite:

### Cách 1: Export/Import qua CSV
1. Export dữ liệu từ SQL Server ra file CSV
2. Import vào SQLite bằng Python:
```python
import pandas as pd
import sqlite3

# Đọc CSV
df = pd.read_csv('data.csv')

# Kết nối SQLite
conn = sqlite3.connect('database.db')

# Ghi vào SQLite
df.to_sql('table_name', conn, if_exists='append', index=False)

conn.close()
```

### Cách 2: Sử dụng Script Python
```python
import admin.sys_sql_server as sql_server  # File cũ
import admin.sys_sqlite as sqlite  # File mới

# Lấy dữ liệu từ SQL Server
df = sql_server.get_columns_data('table_name', columns=['col1', 'col2'])

# Chèn vào SQLite
sqlite.insert_data_to_sql_server('table_name', df, created_by='admin')
```

---

## 6. Lưu Ý Quan Trọng

### Hiệu Năng
- SQLite phù hợp cho ứng dụng nhỏ đến trung bình (< 100GB)
- Không phù hợp cho ứng dụng có nhiều người dùng đồng thời ghi dữ liệu
- Phù hợp cho ứng dụng desktop, ứng dụng đọc nhiều hơn ghi

### Backup
- File database là file đơn `database.db`
- Backup đơn giản bằng cách copy file
- Nên backup thường xuyên

### Concurrent Access
- SQLite hỗ trợ nhiều người đọc đồng thời
- Chỉ một người ghi tại một thời điểm
- Sử dụng `check_same_thread=False` trong kết nối để cho phép multi-threading

### Transactions
- SQLite tự động bắt đầu transaction cho mỗi lệnh
- Nên commit thường xuyên để tránh lock database
- Sử dụng `conn.commit()` sau các thao tác ghi

---

## 7. Troubleshooting

### Lỗi "database is locked"
**Nguyên nhân:** Một process khác đang giữ lock database.
**Giải pháp:**
- Đảm bảo đóng tất cả kết nối sau khi sử dụng
- Tăng timeout: `sqlite3.connect('database.db', timeout=10)`
- Kiểm tra có process nào đang mở database không

### Lỗi "no such table"
**Nguyên nhân:** Bảng chưa được tạo.
**Giải pháp:**
- Chạy script tạo bảng
- Kiểm tra đường dẫn database có đúng không

### Lỗi "unable to open database file"
**Nguyên nhân:** Không có quyền ghi vào thư mục hoặc đường dẫn sai.
**Giải pháp:**
- Kiểm tra quyền thư mục
- Kiểm tra đường dẫn trong `config.json`
- Tạo thư mục nếu chưa tồn tại

---

## 8. File Cũ (Có Thể Xóa hoặc Giữ Lại Để Tham Khảo)

- `admin/sys_sql_server.py` - File cũ sử dụng SQL Server
  - **Lưu ý:** Nên giữ lại file này trong trường hợp cần tham khảo hoặc migration dữ liệu

---

## 9. Liên Hệ & Hỗ Trợ

Nếu gặp vấn đề khi sử dụng, vui lòng kiểm tra:
1. Đường dẫn database trong `admin/config.json`
2. Quyền đọc/ghi thư mục
3. Log lỗi trong terminal khi chạy Streamlit

---

**Ngày cập nhật:** 12/11/2025
**Phiên bản:** 1.0 - Chuyển đổi từ SQL Server sang SQLite
