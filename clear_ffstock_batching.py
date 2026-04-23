"""
Script xóa tất cả dữ liệu FFSTOCK (StockOld) và BATCHING (Mixer) để import lại
"""
import sqlite3

def clear_data():
    conn = sqlite3.connect('database_new.db')
    cursor = conn.cursor()
    
    # Đếm số record trước khi xóa
    cursor.execute("SELECT COUNT(*) FROM StockOld WHERE [Đã xóa] = 0")
    stock_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Mixer WHERE [Đã xóa] = 0")
    mixer_count = cursor.fetchone()[0]
    
    print(f"=== DỮ LIỆU HIỆN TẠI ===")
    print(f"StockOld (FFSTOCK): {stock_count} records")
    print(f"Mixer (BATCHING): {mixer_count} records")
    print()
    
    # Xóa mềm tất cả StockOld
    cursor.execute("""
        UPDATE StockOld 
        SET [Đã xóa] = 1, 
            [Người sửa] = 'system_clear_all',
            [Thời gian sửa] = datetime('now')
        WHERE [Đã xóa] = 0
    """)
    deleted_stock = cursor.rowcount
    
    # Xóa mềm tất cả Mixer
    cursor.execute("""
        UPDATE Mixer 
        SET [Đã xóa] = 1, 
            [Người sửa] = 'system_clear_all',
            [Thời gian sửa] = datetime('now')
        WHERE [Đã xóa] = 0
    """)
    deleted_mixer = cursor.rowcount
    
    # Xóa log import của FFSTOCK và PRODUCTION
    cursor.execute("DELETE FROM EmailImportLog WHERE LoaiFile IN ('FFSTOCK', 'PRODUCTION')")
    deleted_logs = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"=== ĐÃ XÓA ===")
    print(f"StockOld: {deleted_stock} records")
    print(f"Mixer: {deleted_mixer} records") 
    print(f"EmailImportLog: {deleted_logs} logs")
    print()
    print("Bạn có thể import lại từ trang Nhận email!")

if __name__ == "__main__":
    confirm = input("Xác nhận xóa tất cả dữ liệu FFSTOCK và BATCHING? (y/n): ")
    if confirm.lower() == 'y':
        clear_data()
    else:
        print("Đã hủy.")
