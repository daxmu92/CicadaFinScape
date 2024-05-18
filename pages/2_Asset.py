import sys
import streamlit as st
import pandas as pd
import re
sys.path.append("..")
from context import FinContext
from st_utils import FinWidgets
import fwidgets as fw
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
    context:FinContext = st.session_state["context"]
    date = st.date_input("Date", key="add_asset_dia_date")
    period_str = pd.Period(date, freq="M").strftime("%Y-%m")
    last_row = context.query_last_data(acc_name, asset_name, period_str)
    if last_row is not None:
        print(last_row)
        last_date = last_row["DATE"]
        last_net = last_row["NET_WORTH"]
        last_invest = last_row["MONTH_INVESTMENT"]
        last_profit = last_row["MONTH_PROFIT"]
        st.write(f"The previous record: \nDATE: {last_date}, NET_WORTH: {last_net}, INVEST: {last_invest}, PROFIT: {last_profit}")
    else:
        last_net = 0
        last_invest = 0
        last_profit = 0
        st.write(f"Doesn't find previous record")

    if st.toggle("Auto fill", value = True, key = "ass_add_ass_record_toggle"):
        def update(last_change):
            if "ass_add_ass_record_period_input0" not in st.session_state:
                return
            if last_change == "ass_add_ass_record_period_input1":
                st.session_state["ass_add_ass_record_period_input2"] = st.session_state["ass_add_ass_record_period_input0"] - st.session_state["ass_add_ass_record_period_input1"]
            elif last_change == "ass_add_ass_record_period_input2":
                st.session_state["ass_add_ass_record_period_input1"] = st.session_state["ass_add_ass_record_period_input0"] - st.session_state["ass_add_ass_record_period_input2"]
            else:
                st.exception(RuntimeError("should not reach here"))
            return

        net = st.number_input("NET_WORTH", key="ass_add_ass_record_period_input0")
        invest = st.number_input("PERIOD_INVEST", key="ass_add_ass_record_period_input1", on_change=update, args=("ass_add_ass_record_period_input1",))
        profit = st.number_input("PERIOD_PROFIT", key="ass_add_ass_record_period_input2", on_change=update, args=("ass_add_ass_record_period_input2",))
    else:
        net = st.number_input("NET_WORTH", key="ass_add_ass_record_period_input0")
        invest = st.number_input("PERIOD_INVEST", key="ass_add_ass_record_period_input1")
        profit = st.number_input("PERIOD_PROFIT", key="ass_add_ass_record_period_input2")
    
    if st.button("Submit", key = "ass_add_ass_record_button", type="primary"):
        context.insert_asset(date, acc_name, asset_name, net, invest, profit)
        st.rerun()

acc_name_list = [v.name for k,v in context.acc.items()]
acc_name = st.selectbox("Account", acc_name_list)
acc = context.acc[acc_name]

assets_name = [x.name for x in acc.asset_list]

if not assets_name:
    st.write(f"### You don't have any asset under account {acc_name}.")
    if st.button("Add asset", type="primary", key="ass_add_asset"):
        fw.add_asset()
    st.stop()
    
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

