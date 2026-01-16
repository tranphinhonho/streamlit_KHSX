"""
Script cập nhật ghi chú cho Sale và Packing
Chuyển từ format "sheet 13" thành "sheet 13.1.2026"
"""

import sqlite3

def update_ghi_chu():
    conn = sqlite3.connect('database_new.db')
    cursor = conn.cursor()
    
    # 1. Cập nhật Sale
    cursor.execute('''
        SELECT ID, [Ghi chú], [Ngày sale] FROM Sale 
        WHERE [Ghi chú] LIKE 'Import từ DAILY SALED REPORT sheet %' 
        AND [Ghi chú] NOT LIKE 'Import từ DAILY SALED REPORT sheet %.%.%'
        AND [Đã xóa] = 0
    ''')
    sale_records = cursor.fetchall()
    print(f'Sale: Tìm thấy {len(sale_records)} bản ghi cần cập nhật')
    
    updated_sale = 0
    for id, ghi_chu, ngay_sale in sale_records:
        if ngay_sale:
            parts = ngay_sale.split('-')
            if len(parts) == 3:
                year, month, day = parts
                new_ghi_chu = f'Import từ DAILY SALED REPORT sheet {int(day)}.{int(month)}.{year}'
                cursor.execute('UPDATE Sale SET [Ghi chú] = ? WHERE ID = ?', (new_ghi_chu, id))
                updated_sale += 1
    
    # 2. Cập nhật Packing
    cursor.execute('''
        SELECT ID, [Ghi chú], [Ngày packing] FROM Packing 
        WHERE [Ghi chú] LIKE 'Import từ DAILY PACKING sheet %' 
        AND [Ghi chú] NOT LIKE 'Import từ DAILY PACKING sheet %.%.%'
        AND [Đã xóa] = 0
    ''')
    packing_records = cursor.fetchall()
    print(f'Packing: Tìm thấy {len(packing_records)} bản ghi cần cập nhật')
    
    updated_packing = 0
    for id, ghi_chu, ngay_packing in packing_records:
        if ngay_packing:
            parts = ngay_packing.split('-')
            if len(parts) == 3:
                year, month, day = parts
                new_ghi_chu = f'Import từ DAILY PACKING sheet {int(day)}.{int(month)}.{year}'
                cursor.execute('UPDATE Packing SET [Ghi chú] = ? WHERE ID = ?', (new_ghi_chu, id))
                updated_packing += 1
    
    conn.commit()
    print()
    print('=== KẾT QUẢ ===')
    print(f'Sale: Đã cập nhật {updated_sale} bản ghi')
    print(f'Packing: Đã cập nhật {updated_packing} bản ghi')
    conn.close()

if __name__ == '__main__':
    update_ghi_chu()
