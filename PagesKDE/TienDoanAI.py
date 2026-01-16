import streamlit as st
from admin.sys_kde_components import *
import json
import google.generativeai as genai
import pandas as pd

def load_gemini_config():
    """Đọc cấu hình Gemini từ config.json"""
    with open('admin/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get('api_key_gemini'), config.get('model-flash', 'gemini-2.5-flash')

def call_ai_model_to_predict(lenh_dat_hang, df_san_pham):
    """
    Gọi Gemini API để phân tích lệnh đặt hàng và tìm sản phẩm phù hợp
    
    Args:
        lenh_dat_hang: Chuỗi văn bản lệnh đặt hàng
        df_san_pham: DataFrame chứa danh sách sản phẩm (Code cám, Tên cám)
    
    Returns:
        DataFrame với 3 cột: Code cám, Tên cám, Số lượng
    """
    try:
        # Đọc cấu hình
        api_key, model_name = load_gemini_config()
        
        # Cấu hình Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Tạo danh sách sản phẩm dạng text để gửi cho AI
        san_pham_list = df_san_pham.to_dict('records')
        
        san_pham_text = "\n".join([f"- Code: {sp['Code cám']}, Tên: {sp['Tên cám']}" for sp in san_pham_list])
        # print( san_pham_text)
        # Tạo prompt
        prompt = f"""
Bạn là trợ lý AI chuyên phân tích đơn đặt hàng thức ăn chăn nuôi.

DANH SÁCH SẢN PHẨM CÓ SẴN:
{san_pham_text}

LỆNH ĐẶT HÀNG:
{lenh_dat_hang}

NHIỆM VỤ:
1. Phân tích lệnh đặt hàng và tìm các sản phẩm phù hợp nhất từ danh sách
2. Xác định số lượng cho mỗi sản phẩm (nếu có, không có thì để 0)
3. Tìm kiếm gần đúng dựa trên: Code cám, Tên cám (có thể viết tắt, sai chính tả)

YÊU CẦU ĐẦU RA:
Trả về CHÍNH XÁC theo định dạng JSON như sau, KHÔNG thêm text nào khác:
{{
  "products": [
    {{"code": "Code cám", "ten": "Tên cám đầy đủ", "so_luong": số_lượng}},
    ...
  ]
}}

CHÚ Ý:
- Nếu không tìm thấy sản phẩm nào phù hợp, trả về list rỗng: {{"products": []}}
- Số lượng phải là số nguyên hoặc số thực, không có đơn vị
- Chỉ chọn sản phẩm từ danh sách đã cho
"""
        
        # Gọi API
        with st.spinner('🤖 Đang xử lý với AI...'):
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Loại bỏ markdown code block nếu có
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # Parse JSON
            result_json = json.loads(result_text)
            products = result_json.get('products', [])
            
            if not products:
                st.warning("⚠️ AI không tìm thấy sản phẩm phù hợp trong lệnh đặt hàng.")
                return pd.DataFrame(columns=['Code cám', 'Tên cám', 'Số lượng'])
            
            # Chuyển đổi thành DataFrame
            df_result = pd.DataFrame([
                {
                    'Code cám': p.get('code', ''),
                    'Tên cám': p.get('ten', ''),
                    'Số lượng': p.get('so_luong', 0)
                }
                for p in products
            ])
            
            return df_result
            
    except json.JSONDecodeError as e:
        st.error(f"❌ Lỗi parse JSON từ AI: {e}\n\nResponse: {result_text}")
        return pd.DataFrame(columns=['Code cám', 'Tên cám', 'Số lượng'])
    except Exception as e:
        st.error(f"❌ Lỗi khi gọi AI: {str(e)}")
        return pd.DataFrame(columns=['Code cám', 'Tên cám', 'Số lượng'])

def app(selected):
    st.header("Tiên Đoán AI")
    
    
    lenhdathang = st.text_area("Nhập lệnh đặt hàng:")
    
    df = ss.get_columns_data(
        table_name='SanPham',
        columns=['Code cám', 'Tên cám'],
        data_type='dataframe',
        col_where={'Đã xóa': ('=', 0)}
    )
    
    st.markdown("##### Danh sách Sản Phẩm")
    # st.dataframe(df, width='content')
    
    submit = st.button("🤖 Gọi AI để dự đoán sản phẩm", type="primary")
    
    if submit:
        if not lenhdathang.strip():
            st.warning("⚠️ Vui lòng nhập lệnh đặt hàng!")
        else:
            # Gọi AI để phân tích
            df_result = call_ai_model_to_predict(lenhdathang, df)
            
            if not df_result.empty:
                st.success("✅ Đã phân tích thành công!")
                st.markdown("##### 📋 Sản phẩm được AI dự đoán:")
                st.dataframe(
                    df_result,
                    width='content',
                    column_config={
                        "Code cám": st.column_config.TextColumn("Code cám", width="medium"),
                        "Tên cám": st.column_config.TextColumn("Tên cám", width="large"),
                        "Số lượng": st.column_config.NumberColumn("Số lượng", format="%.2f")
                    }
                )
                
                # Hiển thị tổng số sản phẩm
                st.metric("Tổng số loại sản phẩm", len(df_result))
            else:
                st.info("ℹ️ Không tìm thấy sản phẩm phù hợp.")
                
    
    
    
    