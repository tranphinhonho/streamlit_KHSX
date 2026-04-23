# -*- coding: utf-8 -*-
"""
Mixer - Theo dõi chất lượng Mixer
Đây là module theo dõi chất lượng cho công đoạn Mixer
"""

import streamlit as st
from admin.sys_kde_components import *
import sqlite3
from datetime import datetime
import pandas as pd

def app(selected):
    st.header("🔧 Theo dõi chất lượng Mixer")
    
    st.info("🚧 Tính năng đang được phát triển...")
    
    tab1, tab2 = st.tabs(["📥 Nhập dữ liệu", "📋 Danh sách"])
    
    with tab1:
        st.subheader("📥 Nhập dữ liệu Mixer")
        st.warning("⚠️ Chưa có dữ liệu. Tính năng sẽ được cập nhật sau.")
    
    with tab2:
        st.subheader("📋 Danh sách dữ liệu Mixer")
        st.info("Chưa có dữ liệu")
