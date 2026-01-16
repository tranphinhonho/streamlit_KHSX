# Tổng hợp cuộc trò chuyện - B7KHSX Production Planning App

**Ngày:** 12/01/2026

---

## 1. Chạy ứng dụng B7KHSX

### Lỗi gặp phải:
- Virtual environment (venv) bị lỗi do copy từ folder khác (`B7 - Theodoichatluongok`)
- Lệnh `streamlit run main.py` không hoạt động

### Giải pháp:
```powershell
# Dùng python -m thay vì gọi trực tiếp
python -m streamlit run main.py --server.port 8502
```

---

## 2. Thư mục `utils` trong B7KHSX

Chứa các module tiện ích:

| File | Mục đích |
|------|----------|
| `database_utils.py` | Quản lý SQLite database cho báo cáo Test Cân |
| `email_utils.py` | Gửi email qua Outlook COM (pywin32) |
| `ocr_utils.py` | Trích xuất text từ ảnh bằng Gemini AI |

---

## 3. AI phân tích Excel và tổng hợp báo cáo

### Các AI có thể sử dụng:
1. **Google Gemini API** - Đang dùng trong app, miễn phí 15 USD/tháng
2. **OpenAI GPT-4** + Code Interpreter
3. **Microsoft Copilot for Excel**
4. **Claude (Anthropic)**

### Đề xuất:
Thay thế VBA bằng Python + Gemini AI tích hợp vào Streamlit app.

---

## 4. Tự động nhận email và import Excel

**Yêu cầu:** Nhận email từ `dinhnguyen@cp.com.vn` lúc 9h sáng với 2 file:
- `FFSTOCK xx-xx-xxxx.xlsm` (Stock cám)
- `DAILY STOCK EMPTY BAG REPORT xx-xx-xxxx.xlsm` (Bao bì)

**Giải pháp đề xuất:**
- Phương án 1: Đọc email qua Outlook COM (pywin32)
- Phương án 2: Microsoft Graph API

---

## 5. Tính năng Lịch tháng (ĐÃ IMPLEMENT)

### Yêu cầu:
1. Bảng lịch 31 ngày theo tháng
2. Mỗi ngày hiển thị số record Stock Old, Packing, Sale
3. Click vào ngày để xem chi tiết và chuyển đến trang nhập liệu

### Files đã tạo/sửa:

#### [NEW] `PagesKDE/LichThang.py`
```python
# Chức năng chính:
- get_daily_counts(year, month)  # Lấy số record theo ngày
- get_detail_data(date, type)    # Lấy chi tiết dữ liệu
- render_calendar_cell()          # Render ô ngày
- app()                           # Giao diện chính
```

#### [NEW] `add_lichthang_menu.py`
Script thêm menu "Lịch tháng" vào database.

#### [MODIFIED] `PagesKDE/StockOld.py`
Thêm filter theo ngày từ Lịch tháng:
```python
# Hiển thị banner khi đến từ Lịch tháng
if 'filter_date' in st.session_state and st.session_state.filter_date:
    st.info(f"📅 Bạn đến từ Lịch tháng - Ngày: {filter_date}")
    
# Lọc dữ liệu theo ngày
col_where['Ngày stock old'] = ('=', st.session_state.filter_date)
```

#### [MODIFIED] `PagesKDE/Packing.py`
Tương tự StockOld.py - thêm filter theo `Ngày packing`.

#### [MODIFIED] `PagesKDE/Sale.py`
Tương tự - thêm filter theo `Ngày sale`.

### Cách sử dụng:
1. Vào **Kế hoạch sản xuất → Lịch tháng**
2. Click vào ngày bất kỳ
3. Xem chi tiết và click nút "Đi tới Stock Old/Packing/Sale"
4. Click vào tab tương ứng ở menu trên

---

## 6. Tạo môi trường ảo (venv)

```powershell
cd d:\PYTHON\B7KHSX

# Xóa venv cũ (nếu bị lỗi)
Remove-Item -Recurse -Force .\venv

# Tạo venv mới
python -m venv venv

# Kích hoạt
.\venv\Scripts\Activate.ps1

# Cài thư viện
pip install -r requirements.txt

# Chạy app
streamlit run main.py
```

### Nếu gặp lỗi ExecutionPolicy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 7. Cấu trúc Database

### Các bảng liên quan đến Lịch tháng:

| Bảng | Cột ngày | Mô tả |
|------|----------|-------|
| `StockOld` | `[Ngày stock old]` | Stock tồn cám |
| `Packing` | `[Ngày packing]` | Đóng bao |
| `Sale` | `[Ngày sale]` | Bán hàng |

### Bảng hệ thống menu:

| Bảng | Mô tả |
|------|-------|
| `tbsys_ChucNangChinh` | Chức năng sidebar (Kế hoạch sản xuất, Danh mục...) |
| `tbsys_DanhSachChucNang` | Chức năng con (Stock Old, Packing, Lịch tháng...) |
| `tbsys_ModuleChucNang` | Liên kết module Python |
| `tbsys_ChucNangTheoVaiTro` | Phân quyền theo vai trò |

---

## 8. Lưu ý quan trọng

1. **Streamlit không thể tự động chuyển tab** - Người dùng phải click thủ công
2. **Virtual environment** nên tạo mới khi copy folder, không nên copy venv
3. **Database path**: `database_new.db` (cấu hình trong `admin/config.json`)

---

## 9. Các file cần chú ý

```
B7KHSX/
├── main.py                      # Entry point
├── database_new.db              # SQLite database
├── requirements.txt             # Dependencies
├── admin/
│   ├── config.json              # Cấu hình app
│   ├── sys_sqlite.py            # Database utilities
│   └── sys_kde_components.py    # UI components
├── PagesKDE/
│   ├── LichThang.py             # [NEW] Lịch tháng
│   ├── StockOld.py              # [MODIFIED] 
│   ├── Packing.py               # [MODIFIED]
│   ├── Sale.py                  # [MODIFIED]
│   └── ...
└── utils/
    ├── database_utils.py
    ├── email_utils.py
    └── ocr_utils.py
```
