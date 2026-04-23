# 📊 Walkthrough: App Kế Hoạch Sản Xuất (B7KHSX)

## Tổng Quan

App **Kế Hoạch Sản Xuất** là hệ thống quản lý sản xuất thức ăn chăn nuôi, được xây dựng bằng **Streamlit** và **SQLite**. App giúp tự động hóa quy trình lập kế hoạch sản xuất dựa trên các nguồn dữ liệu như Forecast, đơn hàng, và tồn kho.

---

## 📁 Cấu Trúc Module Chính

| Module | Mô tả | File |
|--------|-------|------|
| **Đặt hàng** | Quản lý các loại đơn hàng: Forecast, Bá Cang, Xe bồn Silo | `PagesKDE/DatHang.py` |
| **Stock đầu ngày** | Tính toán tồn kho đầu ngày tự động | `PagesKDE/StockHomNay.py` |
| **Plan** | Lập kế hoạch sản xuất | `PagesKDE/Plan.py` |
| **Sale** | Quản lý bán hàng | `PagesKDE/Sale.py` |
| **Packing** | Quản lý đóng bao | `PagesKDE/Packing.py` |
| **Stock Old** | Import dữ liệu tồn kho từ Excel | `PagesKDE/StockOld.py` |
| **Pellet Plan** | Kế hoạch ép viên | `PagesKDE/Pellet.py` |
| **Packing Plan** | Kế hoạch đóng bao | `PagesKDE/PackingPlan.py` |
| **Bao bì** | Quản lý tồn kho bao bì | `PagesKDE/BaoBi.py` |
| **Batching** | Theo dõi Mixer | `PagesKDE/Batching.py` |
| **Tồn bồn** | Quản lý tồn bồn Silo | `PagesKDE/TonBon.py` |
| **Nhận email** | Import dữ liệu từ email tự động | `PagesKDE/EmailImport.py` |

---

## 🔄 Quy Trình Chính

### 1. Tính Toán Stock Đầu Ngày

```
Stock đầu ngày (N) = Stock Old (N-2) + Packing (N-1) - Sale (N-1)
```

**Các bước:**
1. Truy cập tab **Stock đầu ngày** → **🧮 Tính toán tự động**
2. Chọn **Ngày tính toán** (mặc định là hôm nay)
3. Tùy chỉnh ngày lấy dữ liệu nếu có ngày nghỉ:
   - 📦 Ngày Stock Old
   - 🏭 Ngày Packing
   - 🚚 Ngày Sale
4. Nhấn **🧮 Tính toán**
5. Xem kết quả và nhấn **💾 Xác nhận Lưu**

**Tính năng mới:**
- 31 nút ngày để xem nhanh stock theo từng ngày
- Lọc theo vật nuôi: HEO, GÀ, BÒ, VỊT, CÚT, DÊ

---

### 2. Lập Kế Hoạch Sản Xuất

**Tab: Plan → 📊 Tổng hợp kế hoạch**

Hệ thống tự động tính toán kế hoạch dựa trên:

| Nguồn | Ưu tiên | Mô tả |
|-------|---------|-------|
| Kế hoạch thủ công | 0 | Được nhập trước bởi user |
| Đơn Bá Cang | 1 | Đơn hàng đại lý, SX hôm nay → giao ngày mai |
| Xe bồn Silo | 1 | Đơn hàng xe bồn, SX hôm nay → lấy ngày mai |
| Forecast DoH < 3 | 2 | Sản phẩm tồn kho thấp (dưới 3 ngày) |
| Bao 50kg | 3 | Chia đều Forecast cho 5 ngày làm việc |

**Công suất:**
- Tối thiểu: **2,100,000 Kg/ngày**
- Cho phép vượt: **+5%** (2,205,000 Kg)

---

### 3. Import Dữ Liệu Từ Email

**Tab: Nhận email**

App tự động nhận và xử lý các file từ email:

| Loại file | Folder Outlook | Bảng Database |
|-----------|----------------|---------------|
| DAILY SALED REPORT | Sent Items | Sale |
| FFSTOCK | FFSTOCK | StockOld |
| PRODUCTION CSV | Sent Items | Mixer |
| TỒN BỒN | Tồn bồn | TonBon |

---

## 🗂️ Cấu Trúc Database

### Bảng chính:

```
SanPham (Sản phẩm)
├── ID (PK)
├── Code cám
├── Tên cám
├── Vật nuôi (H/G/B/V/C/D)
└── Batch size

DatHang (Đặt hàng)
├── ID (PK)
├── ID sản phẩm (FK → SanPham)
├── Loại đặt hàng
├── Số lượng
└── Ngày lấy

StockHomNay (Stock đầu ngày)
├── ID (PK)
├── ID sản phẩm (FK → SanPham)
├── Số lượng
└── Ngày stock

Plan (Kế hoạch)
├── ID (PK)
├── ID sản phẩm (FK → SanPham)
├── Mã plan
├── Số lượng
└── Ngày plan
```

---

## 🛠️ Các Tiện Ích

### 1. Filter theo vật nuôi
Các trang hỗ trợ lọc nhanh theo loại vật nuôi:
- **H** = HEO
- **G** = GÀ
- **B** = BÒ
- **V** = VỊT
- **C** = CÚT
- **D** = DÊ

### 2. Import Excel
Hầu hết các module đều hỗ trợ import từ Excel với file mẫu có sẵn.

### 3. Pagination
Bảng dữ liệu hỗ trợ phân trang: 10, 50, 100 hoặc All.

---

## 📌 Lưu Ý Quan Trọng

1. **Ngày nghỉ:** Khi có ngày nghỉ (Chủ nhật, lễ), cần điều chỉnh ngày lấy dữ liệu Stock Old trong công thức tính Stock đầu ngày.

2. **Backup:** Database được lưu tại `database_new.db`. Nên backup định kỳ.

3. **Xóa dữ liệu:** Các thao tác xóa chỉ đánh dấu `[Đã xóa] = 1`, không xóa vĩnh viễn.

---

## 🚀 Khởi Động App

```bash
cd D:\PYTHON\B7KHSX
python -m streamlit run main.py --server.port 8503
```

Truy cập: **http://localhost:8503**

---

## 📝 Changelog Gần Đây

| Ngày | Thay đổi |
|------|----------|
| 19/01/2026 | Thêm 31 nút ngày và filter vật nuôi cho Stock đầu ngày |
| 19/01/2026 | Hỗ trợ tùy chỉnh ngày lấy dữ liệu khi có ngày nghỉ |
| 18/01/2026 | Cải thiện import Forecast từ .xlsx |
| 17/01/2026 | Thêm chức năng tự động phân loại đơn hàng |

---

*Tài liệu được tạo: 19/01/2026*
