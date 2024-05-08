import sys
import streamlit as st
import pandas as pd
import re
sys.path.append("..")
from context import FinContext
from st_utils import FinWidgets
context:FinContext = st.session_state['context']

st.set_page_config(page_title="Asset")
st.sidebar.header("Asset")
st.header("Asset")

@st.experimental_dialog("DELETE ASSET")
def delete_asset_dia(acc_name, ass_name):
    st.write(f"## WARNING!")
    st.write(f"**You are DELETING your asset {ass_name} under {acc_name}, this will clear your data in database**")
    
    if st.button("DELETE", key = "delete_dialog_delete", on_click=FinContext.delete_asset, args=(st.session_state["context"], acc_name, asset_name)):
       st.rerun()
       
    if st.button("Cancel", key = "delete_dialog_cancel", type="primary"):
        st.rerun()

@st.experimental_dialog("ADD ASSET RECORD")
def add_asset_record_dia(acc_name, asset_name):
    context = st.session_state["context"]
    date = st.date_input("Date", key="add_asset_dia_date")


acc_name_list = [v.name for k,v in context.acc.items()]
acc_name = st.selectbox("Account", acc_name_list)
acc = context.acc[acc_name]

assets_name = [x.name for x in acc.asset_list]
tabs = st.tabs(assets_name)
for index,tab in enumerate(tabs):
    with tab:
        asset_name = assets_name[index]
        acc_ass = f"{acc_name}-{asset_name}"
        asset_df = context.asset_df(acc_name, asset_name)
        print(asset_df)
        df = st.data_editor (
            asset_df,
            hide_index=True,
            key = acc_ass + "-df"
        )
        if st.button("Add record", key = f"{acc_ass}-add"):
            add_asset_record_dia(acc_name, asset_name)
        
        if st.button("DELETE ASSET", key = acc_ass + "-delete"):
            delete_asset_dia(acc_name,asset_name)

