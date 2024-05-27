import streamlit as st
import pandas as pd
import streamlit as st
import sys
from streamlit_extras.grid import grid

sys.path.append("..")
import finsql as finsql
from context import FinContext
import fwidgets as fw
import finutils as fu

context: FinContext = st.session_state['context']

st.set_page_config(page_title="Cicada Tools")
st.title("Cicada Tools")
st.divider()

g: st = grid(2, [2, 1], vertical_align="bottom")
if g.button("Reset Asset Table", key="reset_asset_table_button", use_container_width=True):
    fw.confirm_dia(FinContext.reset_asset_table, (context,), "You are reseting your Asset table")

if g.button("Reset Money flow Table", key="reset_tran_table_button", use_container_width=True):
    fw.confirm_dia(FinContext.reset_tran_table, (context,), "You are reseting your Money flow table")

table_name = g.selectbox("Select a table", [finsql.ASSET_TABLE.name(), finsql.TRAN_TABLE.name()])
if g.button("Query table info", key="query_table_info_button", use_container_width=True):
    if table_name == finsql.ASSET_TABLE.name():
        st.write(context.query_table_info(finsql.ASSET_TABLE))
    else:
        st.write(context.query_table_info(finsql.TRAN_TABLE))
