import streamlit as st
import admin.sys_sqlite as ss
import pandas as pd

def app(selected):
    st.header('Cấu trúc Cơ sở dữ liệu SQL', divider='rainbow')

    # --- Query to get CREATE TABLE scripts ---
    sql_tables = """
    SELECT 
        s.name AS schema_name,
        t.name AS table_name,
        'CREATE TABLE [' + s.name + '].[' + t.name + '] (' + CHAR(13) +
        STUFF((
            SELECT ',' + CHAR(13) + '   [' + c.name + '] ' + 
                   UPPER(tp.name) + 
                   CASE WHEN tp.name IN ('varchar','char','varbinary','binary','nvarchar','nchar')
                        THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(c.max_length AS VARCHAR(5)) END + ')'
                        ELSE '' END +
                   CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END
            FROM sys.columns c
            JOIN sys.types tp ON c.user_type_id = tp.user_type_id
            WHERE c.object_id = t.object_id
            FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 2, '') + CHAR(13) + ')' AS table_script
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    ORDER BY s.name, t.name;
    """

    # --- Query to get CREATE VIEW scripts ---
    sql_views = """
    SELECT 
        s.name AS schema_name,
        v.name AS view_name,
        m.definition AS view_definition
    FROM sys.views v
    JOIN sys.sql_modules m ON v.object_id = m.object_id
    JOIN sys.schemas s ON v.schema_id = s.schema_id
    ORDER BY s.name, v.name;
    """

    try:
        # --- Fetch data first ---
        df_tables = ss.query_database_sqlite(sql_string=sql_tables, data_type='dataframe')
        df_views = ss.query_database_sqlite(sql_string=sql_views, data_type='dataframe')

        # --- Section for copying all scripts ---
        st.subheader('🚀 Sao chép toàn bộ cấu trúc')

        # Combine all table scripts
        if not df_tables.empty:
            st.markdown("##### Toàn bộ cấu trúc Bảng (Tables)")
            all_tables_script = "\n\nGO\n\n".join(df_tables['table_script'].tolist())
            st.code(all_tables_script, language='sql')
        else:
            st.info("Không có kịch bản bảng nào để hiển thị.")

        # Combine all view scripts
        if not df_views.empty:
            st.markdown("##### Toàn bộ cấu trúc View")
            all_views_script = "\n\nGO\n\n".join(df_views['view_definition'].tolist())
            st.code(all_views_script, language='sql')
        else:
            st.info("Không có kịch bản view nào để hiển thị.")

        st.markdown("---")

        # --- Section for individual viewing ---
        st.subheader('📜 Chi tiết cấu trúc Bảng (Tables)')
        if not df_tables.empty:
            for index, row in df_tables.iterrows():
                with st.expander(f"Table: `{row['schema_name']}.{row['table_name']}`"):
                    st.code(row['table_script'], language='sql')
        else:
            st.info("Không tìm thấy bảng nào.")

        st.markdown("---")

        st.subheader('🖼️ Chi tiết cấu trúc View')
        if not df_views.empty:
            for index, row in df_views.iterrows():
                with st.expander(f"View: `{row['schema_name']}.{row['view_name']}`"):
                    st.code(row['view_definition'], language='sql')
        else:
            st.info("Không tìm thấy view nào.")

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi truy vấn cấu trúc cơ sở dữ liệu: {e}")