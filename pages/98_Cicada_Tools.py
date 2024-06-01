import streamlit as st
import pandas as pd
import streamlit as st
import sys
from streamlit_extras.grid import grid
from streamlit_extras.row import row

sys.path.append("..")
import src.finsql as finsql
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu

context: FinContext = st.session_state['context']

st.set_page_config(page_title="Cicada Tools")
st.title("Cicada Tools")
st.divider()

st.write("#### Reset your data")
g_reset: st = grid(2, 2, vertical_align="bottom")
if g_reset.button("**Reset Asset Table**", key="reset_asset_table_button", use_container_width=True):
    fw.confirm_dia(FinContext.reset_asset_table, (context,), "**You are reseting your Asset table**")

if g_reset.button("**Reset Money flow Table**", key="reset_tran_table_button", use_container_width=True):
    fw.confirm_dia(FinContext.reset_tran_table, (context,), "You are reseting your Money flow table")

if g_reset.button("**Clear all Data**", use_container_width=True):
    fw.clear_data_dia()

if g_reset.button("**Reset to Sample data**", key="side_bar_reset_button", use_container_width=True):
    fw.reset_sample_data_dia()

st.write("#### Download/Upload your data")
g_file: st = grid(2, 2, vertical_align="bottom")
g_file.download_button(label="**Download your data**",
                       data=context.get_all_data_csv(),
                       file_name=f"cfs-data-{fu.cur_date()}.txt",
                       mime="text/csv",
                       use_container_width=True)
if g_file.button("**Upload csv file**", key="side_bar_load_from_csv", use_container_width=True):
    fw.load_from_csv_dia()

g_file.download_button("**Download your accounts config**",
                       data=context.config_json(),
                       file_name=f"cfs-accounts-config-{fu.cur_date()}.json",
                       mime="application/json",
                       use_container_width=True)
if g_file.button("**Upload your accounts config**", key="side_bar_upload_config_buttong", use_container_width=True):
    fw.load_acc_config_from_json_dia()

st.write("#### Query table attributes")
g_query_table: st = grid(2, vertical_align="bottom")
table_name = g_query_table.selectbox("Select a table", [finsql.ASSET_TABLE.name(), finsql.TRAN_TABLE.name()])
if g_query_table.button("**Query table info**", key="query_table_info_button", use_container_width=True):
    if table_name == finsql.ASSET_TABLE.name():
        st.write(context.query_table_info(finsql.ASSET_TABLE))
    else:
        st.write(context.query_table_info(finsql.TRAN_TABLE))
