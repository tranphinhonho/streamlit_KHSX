# 📊 Test Cân - Database & History Feature

## ✨ Tính năng mới

### 1. **Lưu báo cáo vào Database** 
- Tự động lưu khi gửi email thành công
- Lưu trữ:
  - ✅ Thời gian cân
  - ✅ Các giá trị 502, 505, 508, 574
  - ✅ Hình ảnh gốc (dạng base64)
  - ✅ Thông tin email đã gửi
  - ✅ Người tạo báo cáo
  - ✅ Ghi chú (tùy chọn)

### 2. **Tab History - Xem lại lịch sử**
- 📋 Danh sách tất cả báo cáo đã lưu
- 📊 Thống kê tổng quan:
  - Tổng số báo cáo
  - Báo cáo hợp lệ
  - Đã gửi email
  - Báo cáo mới nhất
  
- 🔍 Tìm kiếm theo:
  - Khoảng thời gian
  - Người tạo
  
- 💾 Mỗi báo cáo hiển thị:
  - Thông tin chi tiết
  - Hình ảnh đã lưu
  - Nút tải xuống hình ảnh
  - Nút xóa báo cáo

## 🎯 Cách sử dụng

### Tab 1: Test Cân OCR
1. Upload hoặc dán ảnh từ clipboard
2. Chọn định dạng ngày
3. Điều chỉnh giới hạn giá trị (nếu cần)
4. Click **Submit** để OCR
5. Kiểm tra kết quả
6. Nhập email người nhận
7. **Thêm ghi chú** (tùy chọn - mới!)
8. Click **Gửi email**
   - ✅ Email được gửi
   - ✅ Báo cáo tự động lưu vào database
   - ✅ Hiển thị ID báo cáo vừa lưu

### Tab 2: Lịch sử
1. Click tab **📜 Lịch sử**
2. Xem thống kê tổng quan
3. Mở rộng từng báo cáo để xem chi tiết
4. Tải xuống hình ảnh nếu cần
5. Xóa báo cáo không cần thiết

#### Tìm kiếm
1. Click **🔍 Tìm kiếm**
2. Chọn khoảng thời gian
3. Nhập người tạo (nếu có)
4. Click **🔍 Tìm kiếm**

## 📁 Database Structure

### Bảng: TestCan_Reports

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| ID | INTEGER | Primary key (auto increment) |
| Datetime | TEXT | Thời gian cân |
| Value_502 | TEXT | Giá trị 502 |
| Value_505 | TEXT | Giá trị 505 |
| Value_508 | TEXT | Giá trị 508 |
| Value_574 | TEXT | Giá trị 574 |
| Image_Data | TEXT | Hình ảnh (base64) |
| Image_Filename | TEXT | Tên file ảnh |
| Created_By | TEXT | Người tạo |
| Created_At | DATETIME | Thời gian tạo |
| Notes | TEXT | Ghi chú |
| Email_Sent | INTEGER | Đã gửi email (1=có, 0=không) |
| Email_Recipients | TEXT | Người nhận email |
| Is_Valid | INTEGER | Hợp lệ (1=có, 0=không) |

## 🔧 Technical Details

### Files mới:
- `utils/database_utils.py` - Database operations
  - `init_testcan_tables()` - Khởi tạo bảng
  - `save_testcan_report()` - Lưu báo cáo
  - `get_testcan_reports()` - Lấy danh sách
  - `get_testcan_report_by_id()` - Lấy 1 báo cáo
  - `get_testcan_image_bytes()` - Lấy hình ảnh
  - `delete_testcan_report()` - Xóa báo cáo
  - `search_testcan_reports()` - Tìm kiếm
  - `get_testcan_stats()` - Thống kê

### Files cập nhật:
- `PagesKDE/TestCan.py`
  - Thêm import database utilities
  - Thêm tabs (OCR + History)
  - Tự động lưu sau khi gửi email
  - Thêm field "Ghi chú"
  - Thêm view lịch sử với tìm kiếm

## 🚀 Migration

Database tự động khởi tạo khi chạy app lần đầu.

Nếu cần khởi tạo thủ công:

```python
from utils.database_utils import init_testcan_tables
init_testcan_tables("database.db")
```

## 📊 Database Location

`database.db` ở thư mục gốc project:
```
B6 - TestCanGemini/
├── database.db          ← SQLite database
├── utils/
│   └── database_utils.py
└── PagesKDE/
    └── TestCan.py
```

## 💡 Tips

1. **Ghi chú hữu ích**: Thêm ghi chú để dễ tìm kiếm sau này
2. **Tải ảnh**: Có thể tải lại ảnh gốc từ lịch sử
3. **Xóa báo cáo**: Xóa các báo cáo test/không hợp lệ
4. **Tìm kiếm**: Dùng filter theo thời gian để tìm nhanh
5. **Username**: Tự động lấy từ session (nếu đã login)

## 🎨 UI Improvements

- ✅ 2 tabs rõ ràng: OCR | Lịch sử
- ✅ Metrics cards để xem thống kê nhanh
- ✅ Expander cho từng báo cáo (gọn gàng)
- ✅ Thumbnail hình ảnh trong danh sách
- ✅ Download button cho từng ảnh
- ✅ Delete button với confirm
- ✅ Search panel có thể thu gọn

## 🔒 Security Notes

- Image stored as base64 in database
- No authentication on delete (add if needed)
- Username from session_state['username']
- Database file should be backed up regularly
