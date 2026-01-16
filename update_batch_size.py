"""
Script cập nhật Batch size từ đơn vị tấn sang kg
- 8.4 -> 8400
- 8.0 -> 8000
"""
import admin.sys_sqlite as ss

print("=== Cập nhật Batch size ===")

# Cập nhật 8.4 -> 8400
result1 = ss.query_database_sqlite('UPDATE SanPham SET [Batch size] = 8400 WHERE [Batch size] = 8.4')
print(f'Cập nhật 8.4 -> 8400: {result1}')

# Cập nhật 8.0 -> 8000  
result2 = ss.query_database_sqlite('UPDATE SanPham SET [Batch size] = 8000 WHERE [Batch size] = 8.0')
print(f'Cập nhật 8.0 -> 8000: {result2}')

# Kiểm tra lại kết quả
df = ss.get_columns_data('SanPham', ['Batch size'], col_where={'Đã xóa': ('=', 0)})
print('\n=== Kết quả sau khi cập nhật ===')
print(df['Batch size'].value_counts())
