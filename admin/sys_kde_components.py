import datetime
import json
import hashlib
import streamlit as st
import time
import pandas as pd
import admin.sys_functions as fn
import base64
import admin.sys_sqlite as ss
import os
from PIL import Image
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import streamlit_antd_components as sac

# JavaScript để lưu và khôi phục vị trí cuộn
def inject_scroll_preservation():
    """Inject JavaScript to preserve scroll position across reruns"""
    st.markdown("""
        <script>
            // Khôi phục vị trí cuộn khi trang load
            (function() {
                const savedScroll = localStorage.getItem('streamlit_scroll_pos');
                if (savedScroll) {
                    setTimeout(function() {
                        window.scrollTo(0, parseInt(savedScroll));
                        localStorage.removeItem('streamlit_scroll_pos');
                    }, 100);
                }
            })();
            
            // Lưu vị trí cuộn trước khi rerun (gọi bởi Streamlit component events)
            function saveScrollPosition() {
                localStorage.setItem('streamlit_scroll_pos', window.scrollY.toString());
            }
            
            // Lắng nghe sự kiện click trên checkbox để lưu scroll
            document.addEventListener('click', function(e) {
                if (e.target.type === 'checkbox' || e.target.closest('[data-testid="stCheckbox"]')) {
                    saveScrollPosition();
                }
            });
        </script>
    """, unsafe_allow_html=True)


def import_data(title='Đọc và hiển thị dữ liệu Excel', file_path='NganhNgheKinhDoanh.xlsx', output_name='NganhNgheKinhDoanh.xlsx', dtype={'Mã ngành': str}, table_name='NganhNgheKinhDoanh', delete_old_data=False, delete_by_ids=None, col_where=None,
                unique_columns=None, date_columns=None):
    # Hiển thị tiêu đề ứng dụng
    st.header(title, divider='rainbow')
    fn.download_file(location=st, title='📥 Tải file excel mẫu', file_path=file_path, output_name=output_name)

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = fn.get_timestamp()

    # Hiển thị giao diện tải lên file Excel hoặc CSV
    uploaded_file = st.file_uploader("Tải lên file Excel hoặc CSV", type=["xlsx", "csv"], key=f"{file_path}_{st.session_state.uploader_key}")

    # Kiểm tra nếu file đã được tải lên
    if uploaded_file is not None:
        # Lấy đuôi của file đã tải lên
        file_extension = uploaded_file.name.split(".")[-1]

        # Đọc dữ liệu từ file Excel hoặc CSV vào DataFrame
        if file_extension.lower() == "csv":
            df = pd.read_csv(uploaded_file, dtype=dtype)
        else:
            df = pd.read_excel(uploaded_file, dtype=dtype)

        # Convert date columns to date format
        if date_columns:
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col]).dt.date

        # Kiểm tra giá trị trùng lặp trong các cột unique_columns
        has_duplicates = False
        if unique_columns:
            for col in unique_columns:
                df[f'Check unique {col}'] = df.duplicated(subset=[col], keep=False).map({True: 'Trùng', False: None})
                if df[f'Check unique {col}'].eq('Trùng').any():
                    has_duplicates = True

        # Nếu có trùng, hiển thị cảnh báo
        if has_duplicates:
            st.warning("⚠️ Dữ liệu có giá trị trùng lặp trong các cột yêu cầu. Vui lòng kiểm tra lại.")

        # Hiển thị dữ liệu
        st.subheader('Dữ liệu từ file')
        df = selectable_dataframe(df, key=f'preview_{table_name}', add_select=False, hide_index=False, disabled_columns=[])

        # Kiểm tra nút "Lưu dữ liệu" được nhấn
        if st.button("Lưu dữ liệu", type='primary'):
            st.session_state.uploader_key = fn.get_timestamp()

            if 'ID' in df.columns.tolist():
                df = df.drop(columns=['ID'])

            # Xóa các cột check unique trước khi insert vào SQL Server
            check_columns = [col for col in df.columns if col.startswith("Check unique ")]
            df = df.drop(columns=check_columns)

            df['Người tạo'] = st.session_state.username
            df['Thời gian tạo'] = fn.get_vietnam_time()

            # Chèn dữ liệu vào SQL Server
            result = ss.insert_data_to_sql_server(table_name=table_name, dataframe=df, delete_old_data=delete_old_data, delete_by_ids=delete_by_ids, col_where=col_where)
            show_notification('Lỗi:', result)

def css_metric_card_text(location, title, value, background_color="#f0f8ff", title_color="#573333", value_color="#007BFF", font_size_title="18px", font_size_value="24px", margin_bottom="20px"):
    location.markdown(f"""
        <div style="background-color:{background_color}; padding:10px; border-radius:10px; text-align:center; font-family:Arial,sans-serif; display:flex; flex-direction:column; justify-content:center; align-items:center; margin-bottom:{margin_bottom};">
            <span style="color:{title_color}; font-weight:bold; font-size:{font_size_title};">{title}</span>
            <span style="color:{value_color}; font-weight:bold; font-size:{font_size_value};">{value}</span>
        </div>""", unsafe_allow_html=True)

def css_metric_card(title, value, pos, image_url=None, color_title='#333', color_value='#007bff', font_size_title=1, font_size_value=2, background_color='#f0f8ff', border_radius=10, padding=0, box_shadow='0 4px 10px rgba(0,0,0,0.1)', margin_bottom=20, text_align='center', image_size='50px', height='120px'):
    container_id = title.replace(" ", "-").lower()
    image_html = f'<img src="{image_url}" alt="{title}" style="width:{image_size}; height:{image_size}; margin-bottom:10px;">' if image_url else ""
    pos.markdown(f"""
        <style>
        .metric-container-{container_id} {{ background-color:{background_color}; border-radius:{border_radius}px; padding:{padding}px; text-align:{text_align}; box-shadow:{box_shadow}; margin-bottom:{margin_bottom}px; height:{height}; display:flex; flex-direction:column; justify-content:center; align-items:center; gap:10px; overflow:hidden; }}
        .metric-header-{container_id} {{ font-size:{font_size_title}em; color:{color_title}; margin:0; line-height:1.2; text-align:center; max-height:calc({height}/3); overflow:hidden; }}
        .metric-value-{container_id} {{ font-size:{font_size_value}em; font-weight:bold; color:{color_value}; margin:0; line-height:1; text-align:center; max-height:calc({height}/3); overflow:hidden; }}
        img {{ width:{image_size}; height:{image_size}; object-fit:contain; }}
        </style>
        <div class="metric-container-{container_id}">
            {image_html}
            <h2 class="metric-header-{container_id}">{title}</h2>
            <p class="metric-value-{container_id}">{value}</p>
        </div>""", unsafe_allow_html=True)

def hide_header_streamlit():
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 0rem;
                    padding-bottom: 5rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)
    if 'rerun' not in st.session_state:
        st.session_state.rerun = True
        st.rerun()

def image_to_base64(img):
    if img:
        with BytesIO() as buffer:
            img.save(buffer, "png")
            return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    return None

def autofit_columns(sheet):
    for column_cells in sheet.columns:
        max_length = 0
        column = column_cells[0].column_letter
        for cell in column_cells:
            try:
                if len(str(cell.value)) > max_length: max_length = len(cell.value)
            except: pass
        sheet.column_dimensions[column].width = max_length + 2

def download_multi_sheets(dataframes, sheet_names, filename, button_text, key):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for df, sheet_name in zip(dataframes, sheet_names):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            autofit_columns(writer.sheets[sheet_name])
    st.download_button(label=button_text, data=output.getvalue(), file_name=filename, key=key, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type='primary')

def show_notification(key, result, rerun=True, second=1):
    if key in result: st.error(result)
    else: st.success(result)
    if rerun:
        time.sleep(second)
        st.rerun()

def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def logo_glow(image_path, width=100, justify_content='center', padding=3, color='#CC0000', box_shadow=10, border_radius=5, margin_top=10, margin_bottom=10, content=None, space=True):
    st.markdown(f"""
        <style>
        .cover-glow-container {{ display:flex; justify-content:{justify_content}; }}
        .cover-glow {{ width:{width}px; height:auto; padding:{padding}px; margin-top:{margin_top}px; margin-bottom:{margin_bottom}px; box-shadow:0 0 {box_shadow}px {color}; position:relative; z-index:-1; border-radius:{border_radius}px; }}
        </style>""", unsafe_allow_html=True)
    img_base64 = img_to_base64(image_path)
    st.markdown(f'<div class="cover-glow-container"><img src="data:image/png;base64,{img_base64}" class="cover-glow"></div>', unsafe_allow_html=True)
    if content: st.success(content)
    if space: st.markdown('---')

def pagination_component(total_records, key_prefix=""):
    ss_page_num_key = f'{key_prefix}_page_num'
    ss_page_size_key = f'{key_prefix}_page_size'
    ss_pagination_widget_key = f'{key_prefix}_pagination_widget'

    if ss_page_size_key not in st.session_state: st.session_state[ss_page_size_key] = 10
    if ss_page_num_key not in st.session_state: st.session_state[ss_page_num_key] = 1

    pagination_cols = st.columns([2, 1])
    with pagination_cols[1]:
        page_sizes = [2, 5, 10, 20, 30]
        prev_page_size = st.session_state[ss_page_size_key]
        # This is the original code, with only the 'index' parameter removed to fix the warning.
        st.selectbox("Số mục/trang", options=page_sizes, label_visibility='collapsed', key=ss_page_size_key)
        if st.session_state[ss_page_size_key] != prev_page_size:
            st.session_state[ss_page_num_key] = 1
            st.rerun()

    with pagination_cols[0]:
        if total_records > 0:
            def on_page_change():
                st.session_state[ss_page_num_key] = st.session_state[ss_pagination_widget_key]
                st.rerun()
            sac.pagination(total=total_records, page_size=st.session_state[ss_page_size_key], index=st.session_state[ss_page_num_key], align='start', jump=True, show_total=True, key=ss_pagination_widget_key, on_change=on_page_change)

    return st.session_state[ss_page_num_key], st.session_state[ss_page_size_key]

def dataframe_with_selections(
    table_name, columns, search_columns=None, col_where=None, col_order=None,
    join_user_info=False, key=None, title=None, colums_disable=[], column_config=None, width='content',
    download=False, num_rows='fix', image_columns=[], joins=None, multi_select=True, select_all=None,
    selected=False, output_columns=None, post_process_func=None, add_select=True, return_all=False, return_selected_rows=False,
    table_edit=None, column_key_edit='ID', allow_select_all=False, custom_columns=None):
    
    # Inject JavaScript để lưu vị trí cuộn khi click checkbox
    inject_scroll_preservation()

    results = {
        "df_return_all": None,
        "df_selected_rows": None
    }

    if key is None:
        st.error("Hàm `dataframe_with_selections` yêu cầu một `key` duy nhất.")
        return results

    if not columns:
        columns = ss.get_table_columns(table_name)
        if not columns:
            st.error(f"Không thể lấy danh sách cột cho bảng '{table_name}'.")
            return results

    if search_columns is None:
        search_columns = list(columns)  # Bắt đầu với các cột của bảng chính
        if joins:
            for join in joins:
                join_table = join.get("table")
                join_alias = join.get("alias", join_table) # Sử dụng alias
                join_columns = join.get("columns", [])
                if join_table and join_columns:
                    # Thêm tiền tố (alias) vào các cột được join để tìm kiếm
                    search_columns.extend([f"{join_alias}.{col}" for col in join_columns])

    # Quản lý trạng thái của ô tìm kiếm để reset phân trang khi thay đổi
    search_state_key = f'dws_search_value_{key}'
    selection_state_key = f"dws_selection_state_{key}"

    if search_state_key not in st.session_state:
        st.session_state[search_state_key] = ""

    # Sử dụng st.session_state để giữ giá trị tìm kiếm qua các lần rerun
    search_value = st.text_input('Tìm kiếm', value=st.session_state[search_state_key], key=f'search_{key}')

    # Nếu giá trị tìm kiếm thay đổi, reset lại trang và lựa chọn
    if search_value != st.session_state[search_state_key]:
        st.session_state[search_state_key] = search_value
        st.session_state.page_num = 1
        if selection_state_key in st.session_state:
            st.session_state[selection_state_key] = set()
        st.rerun()
    
    total_records = ss.get_total_count(table_name=table_name, search_columns=search_columns, search_value=search_value, col_where=col_where, joins=joins)
    
    # page_num, page_size = pagination_component(total_records, key_prefix=key)
    if 'page_size' not in st.session_state:
        st.session_state.page_size = 10
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 1
    
    pagination_cols = st.columns([2, 1])
    with pagination_cols[1]:
        page_sizes = [10, 50, 100, 'All']
        def get_page_size():
            st.session_state.page_size = st.session_state[f'{key}_page_size_select']
            st.session_state.page_num = 1
            st.rerun() # Rerun để pagination cập nhật
        page_size = st.selectbox("Số dòng/trang", options=page_sizes,
                                     index=page_sizes.index(st.session_state.page_size),
                                     label_visibility='collapsed',
                                     on_change=get_page_size,
                                     key=f'{key}_page_size_select')

    with pagination_cols[0]:
        def get_page_num():
            st.session_state.page_num = st.session_state[f'{key}_pagination']
            st.rerun() # Rerun để bảng cập nhật
        
        # Xử lý 'All' - hiển thị tất cả bản ghi
        actual_page_size = total_records if st.session_state.page_size == 'All' else st.session_state.page_size
        
        page_num = sac.pagination(total=total_records, page_size=actual_page_size,
                                  index=st.session_state.page_num,
                                  align='start', jump=True, show_total=True, key=f'{key}_pagination',
                                  on_change=get_page_num)
        
    df = ss.get_columns_data(table_name=table_name, columns=columns, col_order=col_order, col_where=col_where, search_columns=search_columns,
                             joins=joins, search_value=search_value, page_number=page_num, rows_per_page=actual_page_size, custom_columns=custom_columns)
    
    if post_process_func:
        df = post_process_func(df)


    if df.empty:
        st.info('Không có dữ liệu')

    if join_user_info:
        df = ss.get_info(df=df, table_name='tbsys_Users', columns_name=['Username', 'Fullname'], columns_map=['Người tạo'], columns_key=['Username'])

    edited_df = df.copy()
    selected_rows = pd.DataFrame()

    if add_select:
        if 'ID' not in df.columns:
            st.error("DataFrame phải có cột 'ID' để sử dụng chức năng lựa chọn.")
            return results
        
        selection_state_key = f"dws_selection_state_{key}"
        initial_selection_done_key = f"dws_initial_selection_done_{key}"

        if selection_state_key not in st.session_state:
            st.session_state[selection_state_key] = set()
            st.session_state[initial_selection_done_key] = False

        if selected and multi_select and not st.session_state[initial_selection_done_key]:
            if total_records > 0:
                all_ids_df = ss.get_columns_data(
                    table_name=table_name, columns=['ID'], col_order=col_order, col_where=col_where,
                    search_columns=search_columns, joins=joins, search_value=search_value,
                    page_number=page_num, rows_per_page=total_records
                )
                if not all_ids_df.empty:
                    st.session_state[selection_state_key] = set(all_ids_df['ID'])
            st.session_state[initial_selection_done_key] = True

        df_with_selections = df.copy()
        df_with_selections.insert(0, 'Select', df_with_selections['ID'].isin(st.session_state[selection_state_key]))

        if image_columns:
            for col_name in image_columns:
                if col_name in df_with_selections.columns:
                    preview_col_name = f"{col_name} Preview"
                    df_with_selections[preview_col_name] = df_with_selections[col_name].apply(lambda x: os.path.join('images_data', 'images', str(x)) if x else None)
                    df_with_selections[preview_col_name] = df_with_selections[preview_col_name].apply(lambda x: image_to_base64(Image.open(x)) if x and os.path.exists(x) else None)
                    if column_config is None: column_config = {}
                    column_config[preview_col_name] = st.column_config.ImageColumn(label="Preview")

        if title: st.markdown(f"**{title}**")
        
        ids_on_page = set(df['ID'])
        if (select_all or allow_select_all) and multi_select and not df.empty:
            all_on_page_selected = ids_on_page.issubset(st.session_state[selection_state_key])
            
            def on_select_all_change():
                if not isinstance(st.session_state[selection_state_key], set):
                    st.session_state[selection_state_key] = set(st.session_state[selection_state_key])
                
                if st.session_state[f"select_all_{key}"]:
                    st.session_state[selection_state_key].update(ids_on_page)
                else:
                    st.session_state[selection_state_key].difference_update(ids_on_page)

            st.checkbox("Chọn tất cả trên trang này", value=all_on_page_selected, key=f"select_all_{key}", on_change=on_select_all_change)

        column_config2 = {"Select": st.column_config.CheckboxColumn(required=True, width="small")}
        if column_config: column_config2.update(column_config)

        df_display = df_with_selections
        if output_columns:
            # Build the final list of columns, ensuring 'Select' is always first.
            final_cols = ['Select']
            # Add columns from output_columns, ensuring they exist and are not duplicates.
            for col in output_columns:
                if col in df_with_selections.columns and col not in final_cols:
                    final_cols.append(col)
            df_display = df_with_selections[final_cols]
        # Sử dụng hash của dataframe làm key để đảm bảo data_editor được làm mới hoàn toàn khi dữ liệu thay đổi
        df_hash = hashlib.md5(pd.util.hash_pandas_object(df_display, index=True).values).hexdigest()
        editor_key = f"editor_{key}_{df_hash}"
        edited_df = st.data_editor(df_display, key=editor_key, hide_index=True, column_config=column_config2,
                                   disabled=df.columns, width=width, num_rows=num_rows)
        

        # --- Logic cập nhật trạng thái lựa chọn mạnh mẽ hơn ---
        # 1. Lấy ID các dòng được chọn trên trang hiện tại từ data_editor
        selected_ids_on_current_page = set(edited_df['ID'][edited_df.Select])
        
        # 2. Lấy ID của tất cả các dòng trên trang hiện tại
        all_ids_on_current_page = set(df['ID'])
        
        # 3. Lấy ID các dòng đã được chọn ở các trang khác
        if not isinstance(st.session_state[selection_state_key], set):
            st.session_state[selection_state_key] = set(st.session_state[selection_state_key])
        selected_ids_off_current_page = st.session_state[selection_state_key] - all_ids_on_current_page
        
        # 4. Kết hợp lựa chọn từ các trang khác với lựa chọn mới trên trang này
        new_total_selection = selected_ids_off_current_page.union(selected_ids_on_current_page)
        
        # 5. Nếu trạng thái tổng thể thay đổi, cập nhật và rerun
        if new_total_selection != st.session_state[selection_state_key]:
            st.session_state[selection_state_key] = new_total_selection
            st.rerun()

        selection_set = st.session_state.get(selection_state_key, set())
        # st.write(selection_state_key)
        # st.write(selection_set)
        # Chuyển đổi cả cột ID và các giá trị trong tập hợp lựa chọn sang kiểu chuỗi để so sánh an toàn
        selected_rows = df_display[df_display['ID'].astype(str).isin([str(i) for i in selection_set])].copy()

        if not selected_rows.empty and not return_selected_rows:
            st.markdown("---")
            st.markdown("#### Dữ liệu đã chọn")
            selected_ids_str = "_".join(map(str, sorted(list(st.session_state[selection_state_key]))))
            selected_rows_to_edit = selected_rows.drop(columns=['Select'])
            # Lọc column_config để chỉ áp dụng cho các cột có trong DataFrame và không bị disable
            # Cũng loại bỏ DateColumn và DatetimeColumn vì dữ liệu có thể là string gây lỗi type compatibility
            filtered_column_config = None
            if column_config:
                existing_columns = selected_rows_to_edit.columns.tolist()
                filtered_column_config = {}
                for k, v in column_config.items():
                    if k not in colums_disable and k in existing_columns:
                        # Loại bỏ DateColumn và DatetimeColumn để tránh lỗi type compatibility
                        col_type_str = str(type(v))
                        if 'DateColumn' not in col_type_str and 'DatetimeColumn' not in col_type_str:
                            filtered_column_config[k] = v
                if not filtered_column_config:
                    filtered_column_config = None

            edited_selection = st.data_editor(selected_rows_to_edit, key=f"editor_{key}_selected_{selected_ids_str}", hide_index=True, disabled=colums_disable,
                                              width=width, num_rows='fix', column_config=filtered_column_config)
            btn = sac.buttons(items=[sac.ButtonsItem(label='Cập nhật thông tin', icon='arrow-counterclockwise', color='#4BC4FF'), sac.ButtonsItem(label='Xóa dữ liệu', icon='trash', color='#FF4B4B')], label='', align='left', index=None, gap=100, key=f"actions_{key}")
            if btn:
                ids_to_process = edited_selection['ID'].tolist()
                result = ""
                target_table = table_edit if table_edit is not None else table_name
                if btn == 'Xóa dữ liệu':
                    result = ss.delete_data_from_table_by_ids(target_table, ids_to_process, nguoisua=st.session_state.username, thoigiansua=fn.get_vietnam_time(), col_where=column_key_edit)
                elif btn == 'Cập nhật thông tin':
                    df_to_update = edited_selection.copy()
                    # Xử lý các cột Selectbox và các cột chuỗi có chứa delimiter
                    for col_name in df_to_update.columns:
                        if col_name not in ['ID', 'Select']:
                            # Kiểm tra nếu là SelectboxColumn một cách an toàn
                            is_selectbox = False
                            if column_config and col_name in column_config:
                                col_type_str = str(type(column_config[col_name]))
                                if 'SelectboxColumn' in col_type_str:
                                    is_selectbox = True
                            
                            # Áp dụng logic tách chuỗi nếu là selectbox hoặc nếu cột chứa delimiter
                            if is_selectbox or df_to_update[col_name].astype(str).str.contains(' | ').any():
                                df_to_update[col_name] = df_to_update[col_name].apply(lambda x: x.split(' | ')[0].strip() if isinstance(x, str) and ' | ' in x else x)

                    if "Select" in df_to_update.columns:
                        df_to_update = df_to_update.drop(columns=["Select"])
                    
                    # Lọc ra các cột không bị disable để cập nhật
                    if colums_disable:
                        # Lấy danh sách các cột có thể chỉnh sửa (không nằm trong colums_disable)
                        editable_columns = [col for col in df_to_update.columns if col not in colums_disable]
                        # Luôn giữ lại cột khóa để xác định dòng cần cập nhật
                        if column_key_edit not in editable_columns:
                            editable_columns.append(column_key_edit)
                        df_to_update = df_to_update[editable_columns]

                    result = ss.update_database_from_dataframe(table_name=target_table, dataframe=df_to_update, nguoisua=st.session_state.username, column_key=column_key_edit)
                st.session_state[selection_state_key] = set()
                show_notification("Lỗi:", result)
    else:
        if title: st.markdown(f"**{title}**")
        edited_df = st.data_editor(df, key=f"editor_{key}", hide_index=True, column_config=column_config,
                                   disabled=df.columns, width=width, num_rows=num_rows)

    if download:
        sheetname = fn.sanitize_sheet_name(title if title else 'Data')
        download_multi_sheets([df], sheet_names=[sheetname], filename=f'{sheetname}.xlsx', button_text='Download Excel', key=f'download_{key}')

    if return_all:
        results["df_return_all"] = edited_df
    if return_selected_rows:
        results["df_selected_rows"] = selected_rows
        
    return results


def selectable_dataframe(df, table_name=None, multi_select=True, key=None, column_config=None, hide_index=True, width='content', num_rows='fix',
                allow_select_all=False, select_all=False, disabled_columns=None, add_select=True, table_edit=None, column_key_edit='ID', return_selected_row=False,
                allow_edit=False, columns_edit=None):
    """
    Displays a dataframe with a selection column, allowing single or multiple selections.

    Args:
        df (pd.DataFrame): The dataframe to display.
        multi_select (bool): If True, allows selecting multiple rows. If False, only one row can be selected.
        key (str): A unique key for the component.
        column_config (dict, optional): Configuration for the dataframe columns. Defaults to None.
        hide_index (bool, optional): Whether to hide the dataframe index. Defaults to True.
        width (str, optional): 'content' or 'stretch'. Defaults to 'content'.
        num_rows (str, optional): How to display rows ('fix' or 'dynamic'). Defaults to 'fix'.
        allow_select_all (bool): If True, shows a "Select All" checkbox.
        select_all (bool): If True, all rows are selected by default on first load.
        return_selected_row (bool): If True, returns the selected rows. If False, shows edit/delete buttons.
        allow_edit (bool): If True, allows editing of specified columns. Defaults to False.
        columns_edit (list, optional): A list of column names to allow editing for. Used when allow_edit is True. Defaults to None.

    Returns:
        pd.DataFrame: A dataframe containing the selected rows.
    """
    if df.empty:
        st.info("Không có dữ liệu để hiển thị.")
        return pd.DataFrame()

    if key is None:
        st.error("Hàm `selectable_dataframe` yêu cầu một `key` duy nhất.")
        return pd.DataFrame()

    # Keys for session state
    selection_state_key = f"selection_state_{key}"
    initial_load_key = f"initial_load_{key}"

    # Initialize session state
    if selection_state_key not in st.session_state:
        st.session_state[selection_state_key] = []
    if initial_load_key not in st.session_state:
        st.session_state[initial_load_key] = True

    # Handle `select_all` on the very first run
    if st.session_state[initial_load_key] and select_all:
        st.session_state[selection_state_key] = df.index.tolist()
        st.session_state[initial_load_key] = False

    if not add_select:
        all_data_columns_no_select = df.columns.tolist()
        if allow_edit and columns_edit is not None:
            cols_to_disable_no_select = [col for col in all_data_columns_no_select if col not in columns_edit]
        else:
            cols_to_disable_no_select = all_data_columns_no_select
        
        if disabled_columns is not None:
            cols_to_disable_no_select = list(set(cols_to_disable_no_select + disabled_columns))

        edited_df = st.data_editor(
            df,
            key=f"editor_{key}",
            hide_index=hide_index,
            column_config=column_config,
            disabled=cols_to_disable_no_select,
            width=width,
            num_rows=num_rows
        )
        return edited_df

    # Handle "Select All" checkbox logic
    if allow_select_all and multi_select:
        all_indices = set(df.index)
        selected_indices = set(st.session_state[selection_state_key])
        is_all_selected = all_indices.issubset(selected_indices) and bool(all_indices)

        select_all_checkbox = st.checkbox("Chọn tất cả", value=is_all_selected, key=f"select_all_cb_{key}")

        if select_all_checkbox and not is_all_selected:
            st.session_state[selection_state_key] = df.index.tolist()
            st.rerun()
        elif not select_all_checkbox and is_all_selected:
            st.session_state[selection_state_key] = []
            st.rerun()

    # Create the dataframe to show, with the 'Select' column based on our state
    df_to_show = df.copy()
    df_to_show.insert(0, 'Select', df_to_show.index.isin(st.session_state[selection_state_key]))

    # Prepare column configuration
    final_column_config = {"Select": st.column_config.CheckboxColumn(required=True, width="small")}
    if column_config:
        final_column_config.update(column_config)

    # Determine which columns should be disabled for editing
    all_data_columns = df.columns.tolist()
    if allow_edit and columns_edit is not None:
        cols_to_disable = [col for col in all_data_columns if col not in columns_edit]
    else:
        cols_to_disable = all_data_columns

    if disabled_columns is not None:
        cols_to_disable = list(set(cols_to_disable + disabled_columns))

    # Display the data editor
    edited_df = st.data_editor(
        df_to_show,
        key=f"editor_{key}",
        hide_index=hide_index,
        column_config=final_column_config,
        disabled=cols_to_disable,
        width=width,
        num_rows=num_rows
    )

    # Get the list of selected indices from the user's interaction
    selected_indices_after_edit = edited_df.index[edited_df.Select].tolist()
    indices_before_edit = st.session_state[selection_state_key]

    # If the selection has changed, process it
    if selected_indices_after_edit != indices_before_edit:
        if not multi_select:
            # Single-select logic
            if len(selected_indices_after_edit) > 1:
                newly_added = [i for i in selected_indices_after_edit if i not in indices_before_edit]
                st.session_state[selection_state_key] = [newly_added[-1]] if newly_added else selected_indices_after_edit
            else:
                st.session_state[selection_state_key] = selected_indices_after_edit
        else:
            # Multi-select logic
            st.session_state[selection_state_key] = selected_indices_after_edit
        
        st.rerun()

    # Return the dataframe with the selected rows based on the final state
    # Trả về DataFrame đã được chỉnh sửa, chỉ bao gồm các hàng được chọn
    selected_edited_df = edited_df.loc[edited_df.index.isin(st.session_state[selection_state_key])]
    
    # Bỏ cột 'Select' trước khi trả về để có DataFrame sạch
    if 'Select' in selected_edited_df.columns:
        selected_edited_df = selected_edited_df.drop(columns=['Select'])
    
    if not return_selected_row:
        if not selected_edited_df.empty:
            st.markdown("---")
            st.markdown("#### Dữ liệu đã chọn")

            # Xác định các cột bị vô hiệu hóa cho trình chỉnh sửa lựa chọn
            all_data_columns_selected = selected_edited_df.columns.tolist()
            if allow_edit and columns_edit:
                cols_to_disable_selection = [col for col in all_data_columns_selected if col not in columns_edit]
            else:
                cols_to_disable_selection = all_data_columns_selected
            if disabled_columns:
                cols_to_disable_selection = list(set(cols_to_disable_selection + disabled_columns))

            # Tạo khóa duy nhất cho trình chỉnh sửa dựa trên các chỉ mục đã chọn
            selected_indices_str = "_".join(map(str, sorted(selected_edited_df.index.tolist())))

            edited_selection = st.data_editor(
                selected_edited_df,
                key=f"editor_{key}_selected_{selected_indices_str}",
                hide_index=hide_index,
                disabled=cols_to_disable_selection,
                width=width,
                num_rows='fix',
                column_config=column_config
            )

            if table_name is None and table_edit is None:
                st.error("Lỗi: Cần cung cấp `table_name` để thực hiện cập nhật hoặc xóa.")
            else:
                btn = sac.buttons(items=[sac.ButtonsItem(label='Cập nhật thông tin', icon='arrow-counterclockwise', color='#4BC4FF'), sac.ButtonsItem(label='Xóa dữ liệu', icon='trash', color='#FF4B4B')], label='', align='left', index=None, gap=100, key=f"actions_{key}")
                if btn:
                    ids_to_process = edited_selection['ID'].tolist()
                    result = ""
                    target_table = table_edit if table_edit is not None else table_name
                    if btn == 'Xóa dữ liệu':
                        result = ss.delete_data_from_table_by_ids(target_table, ids_to_process, nguoisua=st.session_state.username, thoigiansua=fn.get_vietnam_time(), col_where=column_key_edit)
                    elif btn == 'Cập nhật thông tin':
                        df_to_update = edited_selection.copy()
                        if column_config:
                            for col_name, col_config in column_config.items():
                                is_selectbox = ('SelectboxColumn' in str(type(col_config)))
                                if is_selectbox and col_name in df_to_update.columns:
                                    df_to_update[col_name] = df_to_update[col_name].apply(lambda x: x.split(' | ')[0].strip() if isinstance(x, str) and ' | ' in x else x)
                        for col_name in df_to_update.columns:
                            if col_name not in ['ID', 'Select'] and df_to_update[col_name].astype(str).str.contains(' \\| ').any():
                                df_to_update[col_name] = df_to_update[col_name].apply(lambda x: x.split(' | ')[0].strip() if isinstance(x, str) and ' | ' in x else x)
                        if "Select" in df_to_update.columns:
                            df_to_update = df_to_update.drop(columns=["Select"])
                        
                        # Lọc ra các cột không bị vô hiệu hóa để cập nhật
                        editable_columns = [col for col in df_to_update.columns if col not in cols_to_disable_selection]
                        if column_key_edit not in editable_columns:
                            editable_columns.append(column_key_edit)
                        df_to_update = df_to_update[editable_columns]

                        result = ss.update_database_from_dataframe(table_name=target_table, dataframe=df_to_update, nguoisua=st.session_state.username, column_key=column_key_edit)
                    st.session_state[selection_state_key] = set()
                    show_notification("Lỗi:", result)

    return selected_edited_df


def dataframe_with_selections_df(
    df, table_name, search_columns=None, key=None, title=None, colums_disable=[], column_config=None, width='content',
    download=False, num_rows='fix', image_columns=[], multi_select=True, select_all=None,
    selected=False, output_columns=None, add_select=True, return_all=False, return_selected_rows=False,
    table_edit=None, column_key_edit='ID', col_json=[]):
    """
    Hiển thị một DataFrame với các chức năng lựa chọn, tìm kiếm, phân trang, chỉnh sửa và xóa.
    Hàm này hoạt động trực tiếp trên một DataFrame đầu vào.

    Args:
        df (pd.DataFrame): DataFrame để hiển thị.
        table_name (str): Tên bảng trong CSDL để thực hiện các hành động cập nhật/xóa.
        search_columns (list, optional): Danh sách các cột để tìm kiếm. Mặc định là tất cả các cột.
        key (str): Key duy nhất cho component.
        ... (các tham số khác tương tự dataframe_with_selections)
    """
    results = {
        "df_return_all": None,
        "df_selected_rows": None
    }

    if key is None:
        st.error("Hàm `dataframe_with_selections_df` yêu cầu một `key` duy nhất.")
        return results

    if df.empty:
        st.info('Không có dữ liệu để hiển thị.')
        return results

    if 'ID' not in df.columns:
        st.error("DataFrame đầu vào phải có cột 'ID' để sử dụng chức năng lựa chọn, chỉnh sửa và xóa.")
        return results

    if search_columns is None:
        search_columns = df.columns.tolist()

    # Quản lý trạng thái
    search_state_key = f'dws_df_search_value_{key}'
    selection_state_key = f"dws_df_selection_state_{key}"
    page_num_key = f'dws_df_page_num_{key}'
    page_size_key = f'dws_df_page_size_{key}'

    if search_state_key not in st.session_state:
        st.session_state[search_state_key] = ""
    if page_num_key not in st.session_state:
        st.session_state[page_num_key] = 1
    if page_size_key not in st.session_state:
        st.session_state[page_size_key] = 10

    # Giao diện tìm kiếm
    search_value = st.text_input('Tìm kiếm', value=st.session_state[search_state_key], key=f'search_df_{key}')

    if search_value != st.session_state[search_state_key]:
        st.session_state[search_state_key] = search_value
        st.session_state[page_num_key] = 1  # Reset về trang 1 khi có tìm kiếm mới
        if selection_state_key in st.session_state:
            st.session_state[selection_state_key] = set()
        st.rerun()

    # Lọc DataFrame dựa trên giá trị tìm kiếm
    df_filtered = df
    if search_value:
        # Tạo một mask boolean, True cho mỗi hàng khớp với tìm kiếm
        mask = df_filtered[search_columns].astype(str).apply(
            lambda x: x.str.contains(search_value, case=False, na=False)
        ).any(axis=1)
        df_filtered = df_filtered[mask]

    total_records = len(df_filtered)

    # Giao diện phân trang
    pagination_cols = st.columns([2, 1])
    with pagination_cols[1]:
        page_sizes = [10, 50, 100, 'All']
        # Đảm bảo page_size hiện tại có trong danh sách
        if st.session_state[page_size_key] not in page_sizes:
            page_sizes.append(st.session_state[page_size_key])
            page_sizes.sort()
            
        prev_page_size = st.session_state[page_size_key]
        st.selectbox("Số dòng/trang", options=page_sizes, key=page_size_key, label_visibility='collapsed')
        if st.session_state[page_size_key] != prev_page_size:
            st.session_state[page_num_key] = 1
            st.rerun()

    with pagination_cols[0]:
        # Xử lý 'All' - hiển thị tất cả bản ghi
        actual_page_size = total_records if st.session_state[page_size_key] == 'All' else st.session_state[page_size_key]
        
        if total_records > 0:
            sac.pagination(
                total=total_records,
                page_size=actual_page_size,
                index=st.session_state[page_num_key],
                align='start', jump=True, show_total=True,
                key=f'pagination_df_{key}',
                on_change=lambda: st.session_state.update({page_num_key: st.session_state[f'pagination_df_{key}']})
            )
    
    page_num = st.session_state[page_num_key]
    page_size = st.session_state[page_size_key]
    
    # Cắt DataFrame cho trang hiện tại
    # Xử lý 'All' - hiển thị tất cả
    if page_size == 'All':
        df_paginated = df_filtered
    else:
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        df_paginated = df_filtered.iloc[start_idx:end_idx]

    # --- Phần logic hiển thị và lựa chọn (gần như giữ nguyên từ hàm gốc) ---
    edited_df = df_paginated.copy()
    selected_rows = pd.DataFrame()

    if add_select:
        selection_state_key = f"dws_df_selection_state_{key}"
        if selection_state_key not in st.session_state:
            st.session_state[selection_state_key] = set()

        df_with_selections = df_paginated.copy()
        df_with_selections.insert(0, 'Select', df_with_selections['ID'].isin(st.session_state[selection_state_key]))

        if image_columns:
            # (Giữ nguyên logic xử lý image_columns)
            pass

        if title: st.markdown(f"**{title}**")
        
        ids_on_page = set(df_paginated['ID'])
        if select_all and multi_select and not df_paginated.empty:
            all_on_page_selected = ids_on_page.issubset(st.session_state[selection_state_key])
            select_all_checkbox = st.checkbox("Chọn tất cả trên trang này", value=all_on_page_selected, key=f"select_all_df_{key}")
            if select_all_checkbox and not all_on_page_selected:
                st.session_state[selection_state_key].update(ids_on_page)
                st.rerun()
            elif not select_all_checkbox and all_on_page_selected:
                st.session_state[selection_state_key].difference_update(ids_on_page)
                st.rerun()

        column_config2 = {"Select": st.column_config.CheckboxColumn(required=True, width="small")}
        if column_config: column_config2.update(column_config)

        df_display = df_with_selections
        if output_columns:
            required_cols = ['ID', 'Select']
            output_columns = [col for col in output_columns if col in df_with_selections.columns]
            final_cols = required_cols + [col for col in output_columns if col not in required_cols]
            df_display = df_with_selections[final_cols]
        
        df_hash = hashlib.md5(pd.util.hash_pandas_object(df_display, index=True).values).hexdigest()
        editor_key = f"editor_df_{key}_{df_hash}"
        edited_df_from_editor = st.data_editor(df_display, key=editor_key, hide_index=True, column_config=column_config2,
                                   disabled=df_paginated.columns, width=width, num_rows=num_rows)
        
        # Logic cập nhật trạng thái lựa chọn
        selected_ids_on_current_page = set(edited_df_from_editor['ID'][edited_df_from_editor.Select])
        all_ids_on_current_page = set(df_paginated['ID'])
        if not isinstance(st.session_state[selection_state_key], set):
            st.session_state[selection_state_key] = set(st.session_state[selection_state_key])
        selected_ids_off_current_page = st.session_state[selection_state_key] - all_ids_on_current_page
        new_total_selection = selected_ids_off_current_page.union(selected_ids_on_current_page)
        
        if new_total_selection != st.session_state[selection_state_key]:
            st.session_state[selection_state_key] = new_total_selection
            st.rerun()

        selection_set = st.session_state.get(selection_state_key, set())
        selected_rows = df[df['ID'].astype(str).isin([str(i) for i in selection_set])].copy()

        if not selected_rows.empty and not return_selected_rows:
            st.markdown("---")
            st.markdown("#### Dữ liệu đã chọn")
            selected_ids_str = "_".join(map(str, sorted(list(st.session_state[selection_state_key]))))
            rows_to_display = selected_rows.copy()
            # Nếu có cột JSON và chỉ một hàng được chọn, ẩn cột JSON khỏi bảng editor
            if col_json and len(rows_to_display) == 1:
                # Lấy danh sách các cột json thực sự tồn tại trong dataframe
                existing_json_cols = [c for c in col_json if c in rows_to_display.columns]
                if existing_json_cols:
                    rows_to_display = rows_to_display.drop(columns=existing_json_cols)

            edited_selection = st.data_editor(rows_to_display, key=f"editor_df_{key}_selected_{selected_ids_str}", hide_index=True, disabled=colums_disable,
                                              width=width, num_rows='fix', column_config=column_config)
            
            # Logic để "bung" cột JSON ra để chỉnh sửa
            if col_json and len(selected_rows) == 1:
                st.markdown("---")
                st.markdown("#### Chỉnh sửa chi tiết")
                
                for json_col_name in col_json:
                    if json_col_name in edited_selection.columns:
                        try:
                            json_string = edited_selection[json_col_name].iloc[0]
                            if json_string and isinstance(json_string, str):
                                json_data = json.loads(json_string)
                                st.markdown(f"**{json_col_name}**")
                                num_cols = 4
                                cols = st.columns(num_cols)
                                for i, (item_key, item_value) in enumerate(json_data.items()):
                                    with cols[i % num_cols]:
                                        st.number_input(
                                            label=str(item_key),
                                            value=float(item_value),
                                            key=f"json_{key}_{json_col_name}_{item_key}", # Key để truy cập qua session_state
                                            step=0.1,
                                            format="%.1f"
                                        )
                            else:
                                st.warning(f"Không có dữ liệu JSON trong cột '{json_col_name}' để chỉnh sửa.")
                        except (json.JSONDecodeError, TypeError, ValueError) as e:
                            st.error(f"Lỗi khi đọc dữ liệu JSON từ cột '{json_col_name}': {e}")

            btn = sac.buttons(items=[sac.ButtonsItem(label='Cập nhật thông tin', icon='arrow-counterclockwise', color='#4BC4FF'), sac.ButtonsItem(label='Xóa dữ liệu', icon='trash', color='#FF4B4B')], label='', align='left', index=None, gap=100, key=f"actions_df_{key}")
            if btn:
                ids_to_process = edited_selection['ID'].tolist()
                result = ""
                target_table = table_edit if table_edit is not None else table_name
                if btn == 'Xóa dữ liệu':
                    result = ss.delete_data_from_table_by_ids(target_table, ids_to_process, nguoisua=st.session_state.username, thoigiansua=fn.get_vietnam_time(), col_where=column_key_edit)
                elif btn == 'Cập nhật thông tin':
                    # Gán lại các giá trị đã chỉnh sửa từ data_editor (không chứa cột json)
                    # vào dataframe gốc `selected_rows` để chuẩn bị cập nhật
                    edited_selection_with_json = selected_rows.copy()
                    edited_selection_with_json.update(edited_selection)

                    # Thu thập lại giá trị JSON đã chỉnh sửa từ session_state
                    if col_json and len(edited_selection_with_json) == 1:
                        for json_col_name in col_json:
                            if json_col_name in edited_selection_with_json.columns:
                                try:
                                    original_json_string = edited_selection_with_json[json_col_name].iloc[0]
                                    if original_json_string and isinstance(original_json_string, str):
                                        original_json_data = json.loads(original_json_string)
                                        updated_json_values = {}
                                        for item_key in original_json_data.keys():
                                            session_key = f"json_{key}_{json_col_name}_{item_key}"
                                            if session_key in st.session_state:
                                                updated_json_values[item_key] = st.session_state[session_key]
                                        # Ghi đè cột JSON trong dataframe sắp được cập nhật
                                        edited_selection_with_json.loc[edited_selection_with_json.index[0], json_col_name] = json.dumps(updated_json_values, ensure_ascii=False)
                                except (json.JSONDecodeError, TypeError, ValueError):
                                    pass # Bỏ qua nếu JSON gốc không hợp lệ

                    # Xử lý các cột Selectbox và các cột chuỗi có chứa delimiter
                    for col_name in edited_selection_with_json.columns:
                        if col_name not in ['ID', 'Select']:
                            # Kiểm tra nếu là SelectboxColumn một cách an toàn
                            is_selectbox = False
                            if column_config and col_name in column_config:
                                col_type_str = str(type(column_config[col_name]))
                                if 'SelectboxColumn' in col_type_str:
                                    is_selectbox = True
                            
                            # Áp dụng logic tách chuỗi nếu là selectbox hoặc nếu cột chứa delimiter
                            if is_selectbox or edited_selection_with_json[col_name].astype(str).str.contains(' | ').any():
                                edited_selection_with_json[col_name] = edited_selection_with_json[col_name].apply(lambda x: x.split(' | ')[0].strip() if isinstance(x, str) and ' | ' in x else x)

                    if "Select" in edited_selection_with_json.columns:
                        edited_selection_with_json = edited_selection_with_json.drop(columns=["Select"])

                    # Lọc ra các cột không bị disable để cập nhật
                    df_to_update = edited_selection_with_json.copy()
                    if colums_disable:
                        # Lấy danh sách các cột có thể chỉnh sửa (không nằm trong colums_disable)
                        editable_columns = [col for col in df_to_update.columns if col not in colums_disable]
                        # Luôn giữ lại cột khóa để xác định dòng cần cập nhật
                        if column_key_edit not in editable_columns:
                            editable_columns.append(column_key_edit)
                        df_to_update = df_to_update[editable_columns]

                    result = ss.update_database_from_dataframe(table_name=target_table, dataframe=df_to_update, nguoisua=st.session_state.username, column_key=column_key_edit)
                st.session_state[selection_state_key] = set()
                show_notification("Lỗi:", result)
    else:
        if title: st.markdown(f"**{title}**")
        edited_df = st.data_editor(df_paginated, key=f"editor_df_{key}", hide_index=True, column_config=column_config,
                                   disabled=df.columns, width=width, num_rows=num_rows)

    if download:
        sheetname = fn.sanitize_sheet_name(title if title else 'Data')
        download_multi_sheets([df], sheet_names=[sheetname], filename=f'{sheetname}.xlsx', button_text='Download Excel', key=f'download_df_{key}')

    if return_all:
        results["df_return_all"] = edited_df
    if return_selected_rows:
        results["df_selected_rows"] = selected_rows
        
    return results

def product_selection_grid(all_products_df, key_prefix):
    """
    A reusable component to display a searchable, paginated grid of products
    with an 'add to cart' functionality.
    """
    import os
    from streamlit_image_select import image_select

    NO_IMAGE_PATH = 'images/noimage.jpeg'

    # --- Initialize session state for the component ---
    if f'{key_prefix}_page' not in st.session_state:
        st.session_state[f'{key_prefix}_page'] = 0
    if f'{key_prefix}_per_page' not in st.session_state:
        st.session_state[f'{key_prefix}_per_page'] = 10

    # --- Filters and display options ---
    filter1, filter2 = st.columns([3, 1])
    search_term = filter1.text_input("Tìm kiếm sản phẩm theo tên hoặc mã", key=f"{key_prefix}_search")
    st.session_state[f'{key_prefix}_per_page'] = filter2.selectbox(
        "Số ảnh/Trang", [10, 20, 30, 40],
        index=[10, 20, 30, 40].index(st.session_state[f'{key_prefix}_per_page']),
        key=f"{key_prefix}_per_page_select"
    )
    
    df_products = all_products_df
    if search_term:
        df_products = df_products[
            df_products['Tên sản phẩm'].str.contains(search_term, case=False, na=False) |
            df_products['Mã sản phẩm'].str.contains(search_term, case=False, na=False)
        ]

    # --- Pagination logic ---
    PRODUCTS_PER_PAGE = st.session_state[f'{key_prefix}_per_page']
    start_idx = st.session_state[f'{key_prefix}_page'] * PRODUCTS_PER_PAGE
    end_idx = start_idx + PRODUCTS_PER_PAGE
    total_pages = (len(df_products) - 1) // PRODUCTS_PER_PAGE + 1 if len(df_products) > 0 else 1
    df_page = df_products.iloc[start_idx:end_idx]

    # --- Product grid display ---
    for i in range(0, len(df_page), 5): # 5 columns per row
        cols = st.columns(5)
        for j in range(5):
            if i + j < len(df_page):
                product = df_page.iloc[i+j]
                with cols[j].container(border=True):
                    img_path = product['Ảnh']
                    if not img_path or not os.path.exists(img_path):
                        img_path = NO_IMAGE_PATH
                    
                    image_select(label= f'{product['Tên sản phẩm']}', images=[img_path], width='stretch')
                    
                    c1, c2 = st.columns([1, 1])
                    so_luong = c1.number_input(label='Số lượng', min_value=0.0, step=1.0, label_visibility="collapsed", format="%.1f", key=f"qty_{product['Mã sản phẩm']}")
                    if c2.button("➕ Thêm", key=f"add_{product['Mã sản phẩm']}", width='stretch'):
                        if so_luong > 0:
                            found = False
                            for item in st.session_state.cart:
                                if item['Mã sản phẩm'] == product['Mã sản phẩm']:
                                    item['Số lượng'] += so_luong
                                    found = True
                                    break
                            if not found:
                                st.session_state.cart.append({
                                    "Mã sản phẩm": product['Mã sản phẩm'],
                                    "Tên sản phẩm": product['Tên sản phẩm'],
                                    "Đơn vị tính": product['Đơn vị tính'],
                                    "Số lượng": so_luong
                                })
                            st.toast(f"Đã thêm {product['Tên sản phẩm']}!", icon="✅")
                            st.rerun()
                        else:
                            st.toast("Số lượng phải lớn hơn 0!", icon="🚫")
    
    # --- Pagination buttons ---
    nav1, nav2, nav3 = st.columns([8,1,1])
    
    def prev_page():
        st.session_state[f'{key_prefix}_page'] -= 1
    def next_page():
        st.session_state[f'{key_prefix}_page'] += 1

    nav2.button('⬅️', on_click=prev_page, disabled=(st.session_state[f'{key_prefix}_page'] == 0), width='stretch')
    nav3.button('➡️', on_click=next_page, disabled=(st.session_state[f'{key_prefix}_page'] >= total_pages - 1), width='stretch')
    nav1.caption(f"Trang {st.session_state[f'{key_prefix}_page'] + 1} / {total_pages}")

def product_selection_grid(df_products, key_prefix):
    import os
    from streamlit_image_select import image_select
    
    NO_IMAGE_PATH = 'images/noimage.jpeg'
    
    # --- Khởi tạo session state cho component ---
    if f'{key_prefix}_page' not in st.session_state:
        st.session_state[f'{key_prefix}_page'] = 0
    if f'{key_prefix}_per_page' not in st.session_state:
        st.session_state[f'{key_prefix}_per_page'] = 10

    # --- Bộ lọc và tùy chọn hiển thị ---
    filter1, filter2 = st.columns([3, 1])
    search_term = filter1.text_input("Tìm kiếm sản phẩm theo tên hoặc mã", key=f"{key_prefix}_search")
    st.session_state[f'{key_prefix}_per_page'] = filter2.selectbox(
        "Số ảnh/Trang", [10, 20, 30, 40],
        index=[10, 20, 30, 40].index(st.session_state[f'{key_prefix}_per_page']),
        key=f"{key_prefix}_per_page_select"
    )
    
    if search_term:
        df_products = df_products[
            df_products['Tên sản phẩm'].str.contains(search_term, case=False, na=False) |
            df_products['Mã sản phẩm'].str.contains(search_term, case=False, na=False)
        ]

    # --- Phân trang ---
    PRODUCTS_PER_PAGE = st.session_state[f'{key_prefix}_per_page']
    start_idx = st.session_state[f'{key_prefix}_page'] * PRODUCTS_PER_PAGE
    end_idx = start_idx + PRODUCTS_PER_PAGE
    total_pages = (len(df_products) - 1) // PRODUCTS_PER_PAGE + 1 if len(df_products) > 0 else 1
    df_page = df_products.iloc[start_idx:end_idx]

    # --- Hiển thị lưới sản phẩm ---
    for i in range(0, len(df_page), 5): # 5 cột trên một hàng
        cols = st.columns(5)
        for j in range(5):
            if i + j < len(df_page):
                product = df_page.iloc[i+j]
                with cols[j].container(border=True):
                    img_path = product['Ảnh']
                    if not img_path or not os.path.exists(img_path):
                        img_path = NO_IMAGE_PATH
                    
                    image_select(label= f'{product['Tên sản phẩm']}', images=[img_path], width="stretch")

                    c1, c2 = st.columns([1, 1])
                    so_luong = c1.number_input(label='Số lượng', min_value=0.0, step=1.0, label_visibility="collapsed", format="%.1f", key=f"qty_{product['Mã sản phẩm']}")
                    if c2.button("➕ Thêm", key=f"add_{product['Mã sản phẩm']}", width='stretch'):
                        if so_luong > 0:
                            found = False
                            for item in st.session_state.cart:
                                if item['Mã sản phẩm'] == product['Mã sản phẩm']:
                                    item['Số lượng'] += so_luong
                                    found = True
                                    break
                            if not found:
                                st.session_state.cart.append({
                                    "Mã sản phẩm": product['Mã sản phẩm'],
                                    "Tên sản phẩm": product['Tên sản phẩm'],
                                    "Đơn vị tính": product['Đơn vị tính'],
                                    "Số lượng": so_luong
                                })
                            st.rerun()
                        else:
                            st.toast("Số lượng phải lớn hơn 0!", icon="🚫")
    
    # --- Nút phân trang ---
    nav1, nav2, nav3 = st.columns([8,1,1])
    def prev_page():
        st.session_state[f'{key_prefix}_page'] -= 1
    def next_page():
        st.session_state[f'{key_prefix}_page'] += 1

    nav2.button('⬅️', on_click=prev_page, disabled=(st.session_state[f'{key_prefix}_page'] == 0))
    nav3.button('➡️', on_click=next_page, disabled=(st.session_state[f'{key_prefix}_page'] >= total_pages - 1))
    nav1.caption(f"Trang {st.session_state[f'{key_prefix}_page'] + 1} / {total_pages}")
