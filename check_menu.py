import sqlite3

conn = sqlite3.connect('database_new.db')
cursor = conn.cursor()

# Check if ChonStockPlan is in menu
cursor.execute("""
    SELECT T1.[Chức năng con], T2.ModulePath 
    FROM tbsys_DanhSachChucNang AS T1 
    LEFT JOIN tbsys_ModuleChucNang AS T2 ON T1.ID = T2.ID_DanhSachChucNang AND T2.[Đã xóa] = 0
    WHERE T1.[Chức năng con] LIKE '%Stock%Plan%' OR T2.ModulePath LIKE '%ChonStockPlan%'
""")

results = cursor.fetchall()
print("=== Menu entries for ChonStockPlan ===")
if results:
    for row in results:
        print(f"Menu: {row[0]} -> Module: {row[1]}")
else:
    print("NOT FOUND in menu!")

conn.close()
