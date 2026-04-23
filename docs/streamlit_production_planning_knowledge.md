# 🏭 Kiến thức Streamlit hỗ trợ Kế hoạch Sản xuất Hàng ngày

> **Nguồn**: Tổng hợp từ [Streamlit Community Forum](https://discuss.streamlit.io/) và các nguồn tài liệu liên quan
> 
> **Ngày tạo**: 30/01/2026

---

## 📋 Mục lục

1. [Dashboard Lập lịch sản xuất (APS)](#1-dashboard-lập-lịch-sản-xuất-aps---advanced-planning--scheduling)
2. [Dashboard Phân tích tầng sản xuất (OEE)](#2-dashboard-phân-tích-tầng-sản-xuất-shop-floor-analytics--oee)
3. [Dashboard Dự báo nhu cầu & Tồn kho](#3-dashboard-dự-báo-nhu-cầu--tồn-kho)
4. [Template & Ví dụ tham khảo](#4-các-templateví-dụ-tham-khảo-trên-github)
5. [Tech Stack đề xuất](#5-đề-xuất-tech-stack)
6. [Áp dụng cho dự án B7KHSX](#6-áp-dụng-cho-dự-án-b7khsx)
7. [Code mẫu](#7-code-mẫu)

---

## 1. Dashboard Lập lịch sản xuất (APS - Advanced Planning & Scheduling)

### Tổng quan

Dashboard APS giúp trực quan hóa lịch sản xuất, tối ưu hóa thời gian và nguồn lực.

### Các thành phần chính

| Tính năng | Thư viện/Tool | Mô tả |
|-----------|---------------|-------|
| **Gantt Chart** | `plotly.figure_factory.create_gantt` hoặc `st-gantt-chart` | Hiển thị lịch sản xuất theo thời gian, dễ theo dõi tiến độ |
| **Tối ưu hóa lịch trình** | Google OR-Tools, PuLP | Sử dụng solver để tối ưu thứ tự sản xuất, giảm thời gian chờ máy |
| **Drag-and-drop** | Custom components | Cho phép kéo thả để điều chỉnh lịch sản xuất |
| **What-if Analysis** | Python + Streamlit | Phân tích kịch bản "nếu như" khi thay đổi kế hoạch |

### Cài đặt thư viện

```bash
pip install plotly
pip install streamlit-gantt-chart
pip install ortools  # Google OR-Tools
pip install pulp     # PuLP solver
```

### Ưu điểm của Gantt Chart trong sản xuất

- ✅ Trực quan hóa timeline sản xuất
- ✅ Dễ dàng nhận diện bottleneck (điểm nghẽn)
- ✅ So sánh kế hoạch vs thực tế
- ✅ Phát hiện trùng lặp/xung đột lịch máy

---

## 2. Dashboard Phân tích tầng sản xuất (Shop Floor Analytics & OEE)

### Chỉ số OEE (Overall Equipment Effectiveness)

OEE là chỉ số đánh giá hiệu quả tổng thể của thiết bị, được tính bằng:

```
OEE = Availability × Performance × Quality
```

| Chỉ số | Công thức | Ứng dụng trong KH sản xuất |
|--------|-----------|----------------------------|
| **Availability** | (Thời gian chạy thực / Thời gian kế hoạch) × 100% | Tỉ lệ máy hoạt động, giúp lập kế hoạch bảo trì |
| **Performance** | (Tốc độ thực / Tốc độ thiết kế) × 100% | So sánh T/h thực vs T/h thiết kế |
| **Quality** | (Sản phẩm đạt / Tổng sản phẩm) × 100% | Tỉ lệ sản phẩm đạt chất lượng |

### Visualizations đề xuất

| Loại biểu đồ | Thư viện | Ứng dụng |
|--------------|----------|----------|
| **Gauge Charts** | Plotly | Hiển thị OEE realtime |
| **Heatmaps** | Plotly, Seaborn | Thời gian ngừng máy theo giờ/ngày |
| **Pareto Charts** | Plotly | Phân loại nguyên nhân lỗi |
| **Line Charts** | Plotly | Trend OEE theo thời gian |

### Nguồn dữ liệu phổ biến

- **Database**: PostgreSQL, MySQL, SQLite
- **IoT**: MQTT brokers cho dữ liệu sensor realtime
- **Cloud**: Snowflake, BigQuery
- **Files**: Excel, CSV

---

## 3. Dashboard Dự báo nhu cầu & Tồn kho

### Thành phần và thư viện

| Thành phần | Thư viện | Ứng dụng |
|------------|----------|----------|
| **Dự báo nhu cầu** | `prophet`, `statsmodels` | Dự đoán sản lượng cần sản xuất |
| **Time Series Analysis** | `pandas`, `numpy` | Phân tích xu hướng lịch sử |
| **Safety Stock Calculation** | Python | Tính mức tồn kho an toàn |
| **Manual Adjustments** | `st.data_editor` | ⭐ Chỉnh sửa kế hoạch sản xuất thủ công |

### Cài đặt

```bash
pip install prophet
pip install statsmodels
```

### Công thức tính Safety Stock

```python
import numpy as np

def calculate_safety_stock(demand_history, service_level=0.95, lead_time_days=3):
    """
    Tính mức tồn kho an toàn
    
    Args:
        demand_history: List hoặc array nhu cầu trong quá khứ
        service_level: Mức dịch vụ mong muốn (0.95 = 95%)
        lead_time_days: Thời gian chờ hàng (ngày)
    
    Returns:
        float: Mức tồn kho an toàn
    """
    from scipy import stats
    
    std_demand = np.std(demand_history)
    z_score = stats.norm.ppf(service_level)
    safety_stock = z_score * std_demand * np.sqrt(lead_time_days)
    
    return safety_stock
```

---

## 4. Các Template/Ví dụ tham khảo trên GitHub

### Repositories quan trọng

| Project | Link | Mô tả |
|---------|------|-------|
| **Production Scheduling Optimization** | [GitHub](https://github.com/vcerun/production-scheduling-streamlit) | App tối ưu lịch sản xuất với OR-Tools |
| **Factory Operation Dashboard** | [GitHub](https://github.com/adrien-be/factory-dashboard) | Dashboard trạng thái máy & throughput |
| **Supply Chain Control Tower** | [GitHub](https://github.com/streamlit/template-supply-chain-dashboard) | Dashboard chuỗi cung ứng đa site |
| **Streamlit Manufacturing Gallery** | [streamlit.io/gallery](https://streamlit.io/gallery?category=manufacturing) | Các demo về manufacturing |

### Streamlit Community Resources

- **Forum chính**: [discuss.streamlit.io](https://discuss.streamlit.io/)
- **Documentation**: [docs.streamlit.io](https://docs.streamlit.io/)
- **Components Gallery**: [streamlit.io/components](https://streamlit.io/components)

---

## 5. Đề xuất Tech Stack

### Stack chuẩn cho Production Planning Dashboard

```
┌─────────────────────────────────────────┐
│           FRONTEND (UI Layer)           │
│  • Streamlit                            │
│  • Custom CSS for styling               │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│         VISUALIZATION Layer             │
│  • Plotly (Gantt, Charts, Gauges)       │
│  • Altair (Statistical charts)          │
│  • st-aggrid (Advanced tables)          │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│         OPTIMIZATION Layer              │
│  • Google OR-Tools (Job-shop scheduling)│
│  • PuLP (Linear programming)            │
│  • SciPy (Optimization algorithms)      │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           DATA Layer                    │
│  • Pandas / Polars (Data manipulation)  │
│  • SQLAlchemy (Database ORM)            │
│  • openpyxl (Excel I/O)                 │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│          DATABASE Layer                 │
│  • SQLite (Local/Small scale)           │
│  • PostgreSQL (Production)              │
│  • Snowflake (Cloud/Analytics)          │
└─────────────────────────────────────────┘
```

### Cài đặt đầy đủ

```bash
# Core
pip install streamlit pandas numpy

# Visualization
pip install plotly altair streamlit-aggrid

# Optimization
pip install ortools pulp scipy

# Database
pip install sqlalchemy openpyxl

# Forecasting (optional)
pip install prophet statsmodels
```

---

## 6. Áp dụng cho dự án B7KHSX

### Các module hiện có

Dựa trên cấu trúc dự án B7KHSX:

| Module | Chức năng hiện tại | Cải tiến đề xuất |
|--------|-------------------|------------------|
| **Plan** | Kế hoạch sản xuất | Thêm Gantt Chart, tối ưu hóa thứ tự |
| **Pellet Plan** | Kế hoạch cám viên | Tích hợp dữ liệu T/h từ vận hành |
| **StockHomNay** | Tồn kho đầu ngày | Thêm dự báo nhu cầu, cảnh báo mức tồn |
| **Pellet Capacity** | Năng suất máy Pellet | Dashboard OEE, so sánh hiệu suất |

### Đề xuất cải tiến chi tiết

#### 6.1. Thêm Gantt Chart cho lịch sản xuất

```python
import plotly.figure_factory as ff
import streamlit as st

def create_production_gantt(df_schedule):
    """
    Tạo Gantt chart cho lịch sản xuất
    
    Args:
        df_schedule: DataFrame với columns: Task, Start, Finish, Resource
    """
    fig = ff.create_gantt(
        df_schedule,
        colors=None,
        index_col='Resource',
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True,
        title='Lịch sản xuất hàng ngày'
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
```

#### 6.2. Sử dụng st.data_editor cho chỉnh sửa kế hoạch

```python
import streamlit as st
import pandas as pd

def editable_production_plan():
    """Cho phép chỉnh sửa kế hoạch sản xuất trực tiếp"""
    
    # Load data
    df_plan = pd.DataFrame({
        'Mã sản phẩm': ['6951XS87', '6952AB12', '6953CD34'],
        'Số lượng (kg)': [5000, 3000, 7000],
        'Máy sản xuất': ['PL1', 'PL2', 'PL3'],
        'Batch': [10, 6, 14],
        'Ưu tiên': [1, 2, 3]
    })
    
    # Editable table
    edited_df = st.data_editor(
        df_plan,
        num_rows="dynamic",  # Cho phép thêm/xóa dòng
        column_config={
            "Số lượng (kg)": st.column_config.NumberColumn(
                min_value=0,
                max_value=100000,
                step=100,
            ),
            "Máy sản xuất": st.column_config.SelectboxColumn(
                options=['PL1', 'PL2', 'PL3', 'PL4', 'PL5', 'PL6', 'PL7']
            ),
            "Ưu tiên": st.column_config.NumberColumn(
                min_value=1,
                max_value=10,
            )
        },
        hide_index=True,
    )
    
    return edited_df
```

#### 6.3. Tính toán OEE từ dữ liệu T/h

```python
def calculate_machine_oee(df_throughput, design_capacity_th=8.0):
    """
    Tính OEE cho máy Pellet
    
    Args:
        df_throughput: DataFrame với columns: Ngày, Số máy, T/h thực tế, Giờ chạy
        design_capacity_th: Năng suất thiết kế (T/h)
    """
    
    # Performance = Actual speed / Design speed
    df_throughput['Performance'] = df_throughput['T/h thực tế'] / design_capacity_th * 100
    
    # Availability = Actual running time / Planned time (giả sử 24h)
    df_throughput['Availability'] = df_throughput['Giờ chạy'] / 24 * 100
    
    # Quality (giả sử từ dữ liệu QC - cần bổ sung)
    df_throughput['Quality'] = 98  # placeholder
    
    # OEE
    df_throughput['OEE'] = (
        df_throughput['Availability'] * 
        df_throughput['Performance'] * 
        df_throughput['Quality']
    ) / 10000
    
    return df_throughput
```

#### 6.4. Dashboard tổng hợp với Plotly

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_oee_dashboard(oee_value, availability, performance, quality):
    """Tạo dashboard OEE với gauge charts"""
    
    fig = make_subplots(
        rows=1, cols=4,
        specs=[[{'type': 'indicator'}] * 4],
        subplot_titles=['OEE', 'Availability', 'Performance', 'Quality']
    )
    
    # OEE Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=oee_value,
        title={'text': "OEE (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 60], 'color': "red"},
                {'range': [60, 75], 'color': "yellow"},
                {'range': [75, 100], 'color': "green"}
            ],
        }
    ), row=1, col=1)
    
    # Similar gauges for other metrics...
    
    fig.update_layout(height=300)
    return fig
```

---

## 7. Code mẫu

### 7.1. Trang Kế hoạch Sản xuất hoàn chỉnh

```python
# PagesKDE/ProductionPlan.py

import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
from datetime import datetime, timedelta

def render_production_plan_page():
    st.title("📊 Kế hoạch Sản xuất Hàng ngày")
    
    # Date selector
    selected_date = st.date_input(
        "Chọn ngày sản xuất",
        value=datetime.now()
    )
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Danh sách kế hoạch", 
        "📊 Gantt Chart", 
        "📈 Thống kê"
    ])
    
    with tab1:
        st.subheader("Kế hoạch sản xuất")
        # Editable table
        df_plan = load_production_plan(selected_date)
        edited_df = st.data_editor(df_plan, num_rows="dynamic")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Lưu kế hoạch", type="primary"):
                save_production_plan(edited_df, selected_date)
                st.success("Đã lưu kế hoạch!")
        with col2:
            if st.button("🔄 Tối ưu hóa thứ tự"):
                optimized_df = optimize_schedule(edited_df)
                st.rerun()
    
    with tab2:
        st.subheader("Lịch sản xuất - Gantt Chart")
        if not df_plan.empty:
            gantt_data = prepare_gantt_data(df_plan)
            fig = ff.create_gantt(
                gantt_data,
                index_col='Resource',
                show_colorbar=True,
                group_tasks=True
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Thống kê sản xuất")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Tổng sản lượng", f"{df_plan['Số lượng'].sum():,.0f} kg")
        with col2:
            st.metric("Số mã sản phẩm", len(df_plan))
        with col3:
            st.metric("Số máy hoạt động", df_plan['Máy'].nunique())
        with col4:
            st.metric("Tổng batch", df_plan['Batch'].sum())
```

### 7.2. Component tái sử dụng

```python
# components/production_widgets.py

import streamlit as st
import plotly.graph_objects as go

def oee_gauge(value, title="OEE"):
    """Widget hiển thị OEE dạng gauge"""
    
    color = "green" if value >= 75 else "yellow" if value >= 60 else "red"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        delta={'reference': 85},  # Target OEE
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def production_summary_cards(total_qty, product_count, efficiency, on_time_rate):
    """Widget hiển thị các KPI sản xuất"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Tổng sản lượng",
            value=f"{total_qty:,.0f} kg",
            delta="+5%"
        )
    
    with col2:
        st.metric(
            label="Số sản phẩm",
            value=product_count,
            delta="+2"
        )
    
    with col3:
        st.metric(
            label="Hiệu suất",
            value=f"{efficiency:.1f}%",
            delta="-2.1%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Đúng tiến độ",
            value=f"{on_time_rate:.1f}%",
            delta="+3%"
        )
```

---

## 📚 Tài liệu tham khảo thêm

### Streamlit Official

- [Streamlit Documentation](https://docs.streamlit.io/)
- [st.data_editor](https://docs.streamlit.io/library/api-reference/data/st.data_editor)
- [Plotly Charts in Streamlit](https://docs.streamlit.io/library/api-reference/charts/st.plotly_chart)

### Manufacturing & Planning

- [Google OR-Tools Documentation](https://developers.google.com/optimization)
- [PuLP Documentation](https://coin-or.github.io/pulp/)
- [OEE Calculation Guide](https://www.oee.com/calculating-oee.html)

### Community Discussions

- [Streamlit Forum - Show the Community](https://discuss.streamlit.io/c/streamlit-examples/9)
- [Streamlit Forum - Custom Components](https://discuss.streamlit.io/c/streamlit-components/18)

---

> **Lưu ý**: File này được tạo tự động từ việc tìm kiếm thông tin trên Streamlit Community Forum.
> Cập nhật lần cuối: 30/01/2026
