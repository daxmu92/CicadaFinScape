import streamlit as st
import pandas as pd
import sys
from streamlit_extras.grid import grid
from streamlit_pills import pills
import plotly.express as px
import src.finchart as fc

sys.path.append("..")

from src.context import FinContext
from src.st_utils import FinLogger
import src.fwidgets as fw
import src.finutils as fu

st.set_page_config(page_title="Recording", layout="wide")
st.title("Recording")
st.divider()
fw.check_context()

context: FinContext = st.session_state['context']

# cur_year = fu.cur_year()
# index = fw.get_year_list().index(cur_year)
# year = st.selectbox("Select year", fw.get_year_list(), index=index, label_visibility="collapsed")
# month = fw.month_selector("recording_month_selector", 6, fu.cur_month())
# date = fu.get_date(year, month)

g: st = grid([2, 2, 8])
cat_to_record = g.selectbox("Category", ["ASSET", "TRANSACTION"], label_visibility="visible")
date = fw.year_month_selector("recording_year_month_selector", g)
# st.write("#### ")
# st.divider()


if cat_to_record == "ASSET":
    acc_name_list = context.config.acc_name_list()
    if not (fw.check_account() and fw.check_subaccount() and fw.check_database()):
        st.stop()
    
    ACC_KEY = "account_test_acc"
    selected_acc_index = fw.button_selector(ACC_KEY, acc_name_list, 6)
    selected_acc = acc_name_list[selected_acc_index]
    
    acc = selected_acc
    sub_name_list = context.config.subacc_name_list(selected_acc)
    if not sub_name_list:
        st.write(f"### You don't have any asset under account {acc}.")
        if st.button("Add asset", type="primary", key="ass_add_asset"):
            fw.add_account()
        st.stop()
    
    
    def format_func(name: str):
        return f"# {name}"
    sub = pills("Select your sub account", sub_name_list, format_func=format_func, label_visibility="collapsed")
    
    cols = st.columns([8, 8])
    with cols[1]:
        data_df = context.query_asset(acc=selected_acc, sub=sub)
        data_df = data_df.sort_values("DATE", ascending=False).round(1)
        kind = {"NET_WORTH": "NET_WORTH", "INFLOW": "INFLOW", "PROFIT": "PROFIT"}
        kind_sel = st.radio("Select kind", kind.keys(), index=0, key=f"recording_kind_radio", horizontal=True, label_visibility="collapsed")
        fig = fc.asset_line(data_df, kind[kind_sel])
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with cols[0]:
        last_row: pd.DataFrame = context.query_last_asset(date, acc, sub)
        cur_row: pd.DataFrame = context.query_subacc_by_date(date, acc, sub, False)
        last_net = 0 if last_row.empty else last_row.iloc[0]["NET_WORTH"]
        st.write("#### Last 2 records:")
        fw.show_last_and_cur_record(last_row, cur_row)
    
        net, inflow, profit = fw.net_inflow_profit_sync_input_with_helper(last_net)
        g: st = grid(4)
        if g.button("Submit", key=f"account_{acc}-{sub}_submit", type="primary", use_container_width=True):
            context.insert_or_update_asset(date, acc, sub, net, inflow, profit)
            fw.net_inflow_profit_sync_input_refresh()
            st.rerun()
        if g.button("Reset", key=f"account_{acc}-{sub}_reset", type="secondary", use_container_width=True):
            fw.net_inflow_profit_sync_input_refresh()

if cat_to_record == "TRANSACTION":
    tran_df = context.query_tran(date).copy()

    cols = st.columns(2)
    with cols[0]:
        st.write("#### Money flow records:")
        col_configs = {k: st.column_config.TextColumn(k, disabled=True) for k in tran_df.columns}
        tran_df["Select"] = False
        check_col_config = st.column_config.CheckboxColumn("Select", default=False)
        col_configs["Select"] = check_col_config
        df = st.data_editor(tran_df, hide_index=True, key="money_flow_df", use_container_width=True, column_config=col_configs)
        id_list = df.loc[df["Select"]]["ID"].tolist()
        row: st = grid(2, vertical_align="bottom")
        if row.button("**Add money flow record**", key="add_new_money_flow_button", use_container_width=True, type="primary"):
            fw.clear_add_money_flow_dia_state()
            fw.add_money_flow_dia(date)
        if row.button("**Delet selected record**", key="delete_money_flow_button", use_container_width=True):
            fw.delete_selected_money_flow_dia(id_list)
    with cols[1]:
        total_inflow = context.query_total_inflow(date)
        fig, config = fc.io_flow_chart(tran_df, total_inflow)
        st.plotly_chart(fig, use_container_width=True, config=config)
    
    