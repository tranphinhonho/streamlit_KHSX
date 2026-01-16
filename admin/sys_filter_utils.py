import pandas as pd
import streamlit as st
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype
)
import warnings
import admin.sys_functions as fn
def filter_dataframe(df: pd.DataFrame,columns_to_search=[],format='%Y-%m-%d',step=None,number_value=None,key=fn.get_timestamp()) -> pd.DataFrame:
    # modify = st.checkbox("Add filters")
    # if not modify:
    #     return df

    df = df.copy()
    for col in df.columns:
        if is_object_dtype(df[col]):
            # Tắt cảnh báo
            warnings.filterwarnings("ignore")
            try:
                df[col] = pd.to_datetime(df[col],format=format)
            except Exception:
                pass
        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()
    with modification_container:
        to_filter_columns = st.multiselect("**Lọc dữ liệu theo:**", df.columns,default=columns_to_search,key=key)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):


                if step is None:
                    step=(_max - _min) / 100
                _min, _max = float(df[column].min()), float(df[column].max())

                if number_value is None:
                    number_value=_min

                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=float(_min),
                    max_value=float(_max),
                    value=(number_value, _max),
                    step=float(step),
                )
                df = df[df[column].between(*user_num_input)]

            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(df[column].min(), df[column].max()),
                )
                if len(user_date_input) == 2:
                    start_date, end_date = tuple(map(pd.to_datetime, user_date_input))
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(f"Substring or regex in {column}")
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]
    return df
