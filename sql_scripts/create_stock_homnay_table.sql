-- Tạo bảng StockHomNay tương tự DatHang
CREATE TABLE IF NOT EXISTS StockHomNay (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    [ID sản phẩm] INTEGER,
    [Mã stock] TEXT,
    [Số lượng] INTEGER DEFAULT 0,
    [Ngày lấy] DATETIME,
    [Ngày stock] DATE,
    [Khách vãng lai] INTEGER DEFAULT 0,
    [Ghi chú] TEXT,
    [Người tạo] TEXT,
    [Thời gian tạo] DATETIME DEFAULT CURRENT_TIMESTAMP,
    [Người sửa] TEXT,
    [Thời gian sửa] DATETIME,
    [Đã xóa] INTEGER DEFAULT 0,
    FOREIGN KEY ([ID sản phẩm]) REFERENCES SanPham(ID)
);

-- Tạo index cho tìm kiếm nhanh
CREATE INDEX IF NOT EXISTS idx_stockhomnay_mastock ON StockHomNay([Mã stock]);
CREATE INDEX IF NOT EXISTS idx_stockhomnay_ngaystock ON StockHomNay([Ngày stock]);
CREATE INDEX IF NOT EXISTS idx_stockhomnay_sanpham ON StockHomNay([ID sản phẩm]);
CREATE INDEX IF NOT EXISTS idx_stockhomnay_deleted ON StockHomNay([Đã xóa]);
