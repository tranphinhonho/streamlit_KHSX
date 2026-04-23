# Hướng dẫn sử dụng Module Đặt hàng

## Tổng quan

Module Đặt hàng quản lý việc nhập và theo dõi các đơn đặt hàng cám thức ăn chăn nuôi từ nhiều nguồn khác nhau.

## Các loại đặt hàng

### 1. 👤 Khách vãng lai
- **Mục đích**: Nhập đơn hàng phát sinh thêm, không có trong forecast tuần
- **Nguồn dữ liệu**: Nhập tay hoặc import từ Excel
- **Đặc điểm**: 
  - Đơn hàng đột xuất
  - Không có trong kế hoạch tuần
  - Cần nhập thủ công thông tin

### 2. 🏪 Đại lý Bá Cang
- **Mục đích**: Quản lý đơn hàng của khách hàng Bá Cang - đặt trước, cố định ngày lấy
- **File nguồn**: `EXCEL/KẾ HOẠCH CÁM TUẦN VÕ BÁ CANG 2026.xlsx`
- **Cấu trúc file**:
  - **Bảng 1 - Xe tải (bao 25kg)**: 
    - Cột A: Mã sản phẩm
    - Cột B-G: Số bao theo ngày (mỗi bao 25kg)
    - Hàng 7: Ngày lấy
  - **Bảng 2 - Xe bồn (Silo)**:
    - Tìm "MÃ CÁM" ở cột C làm mốc
    - Cột B: Ngày lấy
    - Cột C: Mã cám
    - Cột D: Số lượng (kg)

### 3. 🚛 Xe bồn Silo
- **Mục đích**: Tổng hợp tất cả đơn hàng xe bồn Silo
- **File nguồn**: `EXCEL/SILO W*.xlsx` (ví dụ: SILO W4-19-24-01-2026.xlsx)
- **Bao gồm**:
  - Xe bồn Silo của Đại lý Bá Cang
  - Xe bồn Silo của các khách hàng khác
- **Đặc điểm**: Dữ liệu theo tuần, mỗi sheet là 1 ngày hoặc khoảng ngày

### 4. 📅 Forecast hàng tuần
- **Mục đích**: Nguồn dữ liệu chính chứa toàn bộ kế hoạch bán hàng tuần
- **File nguồn**: `EXCEL/SALEFORECAST 2026.xlsx` (ví dụ: W4.(19-24-01-) SALEFORECAST 2026.xlsx)
- **Bao gồm**:
  - Xe tải (bao 25kg) của Đại lý Bá Cang
  - Xe bồn (Silo) của Đại lý Bá Cang
  - Xe bồn Silo của các khách hàng còn lại
  - Đại lý khác
  - Cám trại nội bộ của công ty

## Mối quan hệ giữa các loại

```
📅 Forecast hàng tuần (nguồn chính)
├── 🏪 Đại lý Bá Cang
│   ├── Xe tải (bao 25kg)
│   └── Xe bồn (Silo)
├── 🚛 Xe bồn Silo (các khách khác)
├── Đại lý khác
└── Cám trại nội bộ

👤 Khách vãng lai = Phát sinh thêm ngoài forecast
```

## Quy trình import dữ liệu

### Bước 1: Import Forecast hàng tuần
1. Mở tab **📅 Forecast hàng tuần**
2. Chọn file SALEFORECAST hoặc sử dụng file mặc định
3. Chọn tuần cần import
4. Preview và nhấn **Import vào Database**

### Bước 2: Import chi tiết Đại lý Bá Cang (nếu cần)
1. Mở tab **🏪 Đại lý Bá Cang**
2. Chọn file KẾ HOẠCH CÁM TUẦN hoặc sử dụng file mặc định
3. Chọn tuần tương ứng
4. Kiểm tra preview 2 bảng (Xe tải và Xe bồn)
5. Import vào Database

### Bước 3: Import Silo (nếu cần)
1. Mở tab **🚛 Xe bồn Silo**
2. Chọn file SILO hoặc sử dụng file mặc định
3. Chọn tuần
4. Import vào Database

### Bước 4: Nhập Khách vãng lai (nếu có)
1. Mở tab **👤 Khách vãng lai**
2. Nhập tay hoặc import từ Excel
3. Lưu vào Database

## Lưu ý quan trọng

1. **Thứ tự import**: Nên import Forecast trước, sau đó mới chi tiết hóa bằng các loại khác
2. **Tránh trùng lặp**: Hệ thống sẽ xóa dữ liệu cũ của cùng tuần khi import mới
3. **File mặc định**: Hệ thống tự động lưu và nhớ file đã upload để sử dụng lại
4. **Preview**: Luôn kiểm tra dữ liệu preview trước khi import

## Cấu trúc Database

Tất cả đơn đặt hàng được lưu vào bảng `DatHang` với các trường:
- `ID sản phẩm`: Liên kết với bảng SanPham
- `Mã đặt hàng`: Mã tự động (DH00001, DH00002...)
- `Số lượng`: Số kg đặt hàng
- `Ngày đặt`: Ngày tạo đơn
- `Ngày lấy`: Ngày dự kiến lấy hàng
- `Loại đặt hàng`: Phân loại theo nguồn (Khách vãng lai, Đại lý Bá Cang, Xe bồn Silo, Forecast)
- `Ghi chú`: Thông tin bổ sung
