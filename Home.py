import os
import pandas as pd
import streamlit as st

import finsql as finsql
from context import FinContext
import fwidgets as fw
import finutils as fu

st.set_page_config(page_title="Cicada Financial Scape", page_icon="👋")
st.sidebar.header("Home")
with st.sidebar:
    if st.button("Reset to Sample data", key="side_bar_reset_button"):
        fw.reset_sample_data_dia()
    if st.button("Load from csv", key="side_bar_load_from_csv"):
        fw.load_from_csv_dia()

curr_path = __file__
curr_dir = os.path.dirname(curr_path)
data_dir = os.path.join(curr_dir, "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir, mode=0o777, exist_ok=True)
    os.chmod(data_dir, 0o777)

config_path = os.path.join(data_dir, "config.json")
csv_path = os.path.join(data_dir, "data.csv")
db_path = os.path.join(data_dir, "test.db")

# Init context
context = FinContext(config_path, db_path)
st.session_state['context'] = context

st.write("# Welcome to Cicada Financial Scape!")
st.divider()

if not context.validate_db():
    fw.init_db()
    st.stop()

with st.sidebar:
    st.download_button(label="Download your data", data=context.get_all_data_csv(), file_name=f"cfs-data-{fu.cur_date()}.txt", mime="text/csv")
    if st.button("Clear Data"):
        fw.clear_data_dia()

overview_chart = context.overview_area_chart()
st.write("#### Total worth: ")
st.plotly_chart(overview_chart, theme="streamlit", use_container_width=True)

allocation_pie = context.allocation_pie()
st.write("#### Asset Allocation: ")
st.plotly_chart(allocation_pie, theme="streamlit", use_container_width=True)

cat_list = list(context.cat_dict.keys())
st.write("### Category distribution: ")
if not cat_list:
    st.info("You haven't specify any category")
else:
    tabs = st.tabs(cat_list)
    for i, tab in enumerate(tabs):
        with tab:
            category_pie = context.category_pie(cat_list[i])
            st.plotly_chart(category_pie, theme="streamlit", use_container_width=True)
