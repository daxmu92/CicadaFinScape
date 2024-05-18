import csv
import pandas as pd
import streamlit as st
import os

import finsql as finsql
from context import FinContext

import streamlit as st

st.set_page_config(
    page_title="Cicada Financial Scape",
    page_icon="👋"
)

st.write("# Welcome to Cicada Financial Scape!")
st.sidebar.success("Sidebar")

curr_path = __file__
curr_dir = os.path.dirname(curr_path)
data_dir = os.path.join(curr_dir, "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir, mode=0o777, exist_ok = True)
    os.chmod(data_dir, 0o777)

config_path = os.path.join(data_dir, "config.json")
csv_path = os.path.join(data_dir, "data.csv")
db_path = os.path.join(data_dir, "test.db")

# Init context
context = FinContext(config_path, db_path)
st.session_state['context'] = context

@st.experimental_dialog("Your database is not valid")
def init_db():
    st.write("# Initialize your database? All of the data in database will be reset and can not recover")
    if st.button("Confirm", key = "initial_reset_dia_confirm"):
        context:FinContext = st.session_state['context']
        context.init_db()
        st.rerun()

if not context.validate_db():
    init_db()
    st.stop()

@st.experimental_dialog("RESET DATA TO SAMPLE DATA")
def reset_sample_data_dia():
    st.write("# WARNING: All of your data will be reset and can not recover")
    if st.button("Confirm", key = "side_bar_reset_dia_confirm"):
        context:FinContext = st.session_state['context']
        context.initialize_with_sample_data()
        st.rerun()

@st.experimental_dialog("Load data from csv file")
def load_from_csv_dia():
    upload_file = st.file_uploader("Choose a csv file")
    if upload_file is not None:
        df = pd.read_csv(upload_file)
            
        st.write("Your uploaded file:")
        st.table(df)
        if st.button("Submit", key = "load_csv_submit", type="primary"):
            context.load_from_df(df)
            st.rerun()
    else:
        st.warning("You need to upload a csv file")

with st.sidebar:
    if st.button("Reset to Sample data", key="side_bar_reset_button"):
        reset_sample_data_dia()
    if st.button("Load from csv", key = "side_bar_load_from_csv"):
        load_from_csv_dia()

overview_chart = context.overview_chart()
st.plotly_chart(overview_chart, theme="streamlit", use_container_width=True)

allocation_pie = context.allocation_pie()
st.plotly_chart(allocation_pie, theme="streamlit", use_container_width=True)

cat_list = list(context.cat_dict.keys())
tabs = st.tabs(cat_list)
for i,tab in enumerate(tabs):
    with tab:
        category_pie = context.category_pie(cat_list[i])
        st.plotly_chart(category_pie, theme="streamlit", use_container_width=True)