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
    fw.confirm_dia(FinContext.reset_asset, (context,), "**You are reseting your Asset table**")

if g_reset.button("**Reset Money flow Table**", key="reset_tran_table_button", use_container_width=True):
    fw.confirm_dia(FinContext.reset_tran, (context,), "You are reseting your Money flow table")

if g_reset.button("**Clear all Data**", use_container_width=True):
    fw.clear_data_dia()

if g_reset.button("**Reset to Sample data**", key="side_bar_reset_button", use_container_width=True):
    fw.reset_sample_data_dia()

st.write("#### Download/Upload your data")
g_file: st = grid(1, [1, 1], vertical_align="bottom")
select_list = ["All(zip)", "Asset data", "Money flow", "Account config"]
selected = g_file.selectbox("Select data you want to download", select_list, key="cicada_tool_select_download_data")

if selected == select_list[0]:
    selected_data = context.get_zip_data()
    file_name = f"cfs-data-{fu.cur_date()}.zip"
    mime = None
elif selected == select_list[1]:
    selected_data = context.get_asset_data()
    file_name = f"cfs-asset-data-{fu.cur_date()}.txt"
    mime = "text/csv"
elif selected == select_list[2]:
    selected_data = context.get_tran_data()
    file_name = f"cfs-tran-data-{fu.cur_date()}.txt"
    mime = "text/csv"
elif selected == select_list[3]:
    selected_data = context.config.to_json()
    file_name = f"cfs-account-config-{fu.cur_date()}.json"
    mime = "application/json"

g_file.download_button(label="**Download your data**", data=selected_data, file_name=file_name, mime=mime, type="primary", use_container_width=True)

load_dias = [fw.load_from_zipped_dia, fw.load_from_csv_dia, None, None]
if g_file.button("**Upload your file**", key="upload files", use_container_width=True):
    dia = load_dias[select_list.index(selected)]
    if dia is None:
        fw.unsupported_dia(f"Upload {selected}")
    else:
        dia()

st.write("#### Query table attributes")
g_query_table: st = grid(2, vertical_align="bottom")
table_name = g_query_table.selectbox("Select a table", [finsql.ASSET_TABLE.name(), finsql.TRAN_TABLE.name()])
if g_query_table.button("**Query table info**", key="query_table_info_button", use_container_width=True):
    if table_name == finsql.ASSET_TABLE.name():
        st.write(context.query_asset_info())
    else:
        st.write(context.query_tran_info())
