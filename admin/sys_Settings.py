import streamlit as st
import admin.app_config as config
import re
    
# Dictionary để cung cấp mô tả thân thiện cho các key cấu hình
CONFIG_DESCRIPTIONS = {
    "project_name": "Tên dự án",
    "style_container_bg": "Màu nền Sidebar",
    "style_icon_color": "Màu Icon Menu",
    "style_icon_font_size": "Cỡ chữ Icon Menu",
    "style_nav_link_font_size": "Cỡ chữ Chức năng",
    "style_nav_link_color": "Màu chữ Chức năng (chưa chọn)",
    "style_nav_link_hover_color": "Màu nền khi hover",
    "style_nav_link_selected_bg": "Màu nền khi được chọn",
    "style_nav_link_selected_color": "Màu chữ Chức năng (đã chọn)",
    "style_menu_icon": "Icon tiêu đề",
    "style_font_family": "Font chữ Menu",
}

def is_hex_color(color_string):
    """Kiểm tra xem một chuỗi có phải là mã màu hex hợp lệ hay không."""
    if not isinstance(color_string, str):
        return False
    return bool(re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color_string))

def app(selected_tab):
    st.header(f"Quản lý Cài đặt Hệ thống")

    try:
        all_configs = config.get_all_configs()
    except Exception as e:
        st.error(f"Không thể tải danh sách cấu hình: {e}")
        all_configs = {}

    if not all_configs:
        st.info("Hiện tại chưa có cấu hình nào trong hệ thống.")
        # ... (phần thêm cấu hình mới giữ nguyên)
        return

    with st.form("settings_form"):
        st.subheader("Chỉnh sửa các cấu hình")
        
        updated_values = {}
        
        # Nhóm các key lại để dễ quản lý layout
        general_keys = ['project_name', 'style_menu_icon']
        # Lấy tất cả các key style còn lại, trừ menu_icon đã được chuyển lên trên
        style_keys = [k for k in all_configs.keys() if k.startswith('style_') and k != 'style_menu_icon']

        # --- Cài đặt chung ---
        if any(k in all_configs for k in general_keys):
            st.markdown("---")
            st.markdown("##### Cài đặt chung")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                key = 'project_name'
                if key in all_configs:
                    value = all_configs.get(key, '')
                    label = CONFIG_DESCRIPTIONS.get(key, key)
                    updated_values[key] = st.text_input(label, value=value, key=f"config_{key}")
            with col2:
                key = 'style_menu_icon'
                if key in all_configs:
                    value = all_configs.get(key, '')
                    label = CONFIG_DESCRIPTIONS.get(key, key)
                    updated_values[key] = st.text_input(label, value=value, key=f"config_{key}")
            with col3:
                # Thêm khoảng trống để căn chỉnh chiều cao và đặt link
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("[Tham khảo Icon](https://icons.getbootstrap.com/)", unsafe_allow_html=True)

        # --- Cài đặt giao diện ---
        if style_keys:
            st.markdown("---")
            st.markdown("##### Cài đặt giao diện Sidebar")
            col1, col2 = st.columns(2)
            
            for i, key in enumerate(sorted(style_keys)):
                with col1 if i % 2 == 0 else col2:
                    value = all_configs.get(key, '')
                    label = CONFIG_DESCRIPTIONS.get(key, key)
                    
                    if 'color' in key or 'bg' in key:
                        safe_color = value if is_hex_color(value) else "#000000"
                        if not is_hex_color(value):
                            st.warning(f"Giá trị '{value}' của '{label}' không hợp lệ, tạm dùng màu đen.")
                        updated_values[key] = st.color_picker(label, value=safe_color, key=f"config_{key}")
                    elif key == 'style_font_family':
                        fonts = ["sans-serif", "serif", "monospace", "Arial", "Times New Roman", "Courier New", "Verdana"]
                        # Tìm index của font hiện tại, nếu không có thì mặc định là 0
                        current_index = fonts.index(value) if value in fonts else 0
                        updated_values[key] = st.selectbox(label, options=fonts, index=current_index, key=f"config_{key}")
                    else:
                        updated_values[key] = st.text_input(label, value=value, key=f"config_{key}")

        st.markdown("<br>", unsafe_allow_html=True)
        save_button = st.form_submit_button("Lưu thay đổi")

        if save_button:
            try:
                # ... (phần xử lý lưu giữ nguyên)
                success_count = 0
                error_count = 0
                for key, new_value in updated_values.items():
                    if new_value != all_configs.get(key):
                        if config.set_config(key, new_value):
                            success_count += 1
                        else:
                            error_count += 1
                
                if success_count > 0:
                    st.success(f"Đã cập nhật thành công {success_count} cấu hình!")
                if error_count > 0:
                    st.error(f"Cập nhật thất bại {error_count} cấu hình.")
                
                if success_count > 0 and error_count == 0:
                    st.balloons()
                
                st.rerun()

            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi lưu cấu hình: {e}")
