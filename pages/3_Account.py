import streamlit as st
import pandas as pd
import altair as alt
import sys
import re
from streamlit_extras.grid import grid
from streamlit_pills import pills
import plotly.express as px

sys.path.append("..")

from src.context import FinContext
from src.st_utils import FinLogger
import src.fwidgets as fw
import src.finutils as fu

st.set_page_config(page_title="Account", layout="wide")
st.title("Account")
st.divider()
context: FinContext = st.session_state['context']
acc_name_list = context.config.acc_name_list()

if not (fw.check_account() and fw.check_subaccount() and fw.check_database()):
    st.stop()

ACC_KEY = "account_test_acc"

selected_acc_index = fw.button_selector(ACC_KEY, acc_name_list)
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
# sub = st.radio("Choose your subaccount", sub_name_list, key=f"Choose-asset-{acc}", label_visibility="collapsed")

tab_css = '''
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size:1.2rem;
    }
</style>
'''
st.markdown(tab_css, unsafe_allow_html=True)
tabs = st.tabs(["Overview", "Add/Update Record"])

with tabs[0]:
    data_df = context.query_asset_df(selected_acc, sub)
    data_df = data_df.sort_values("DATE", ascending=False)
    cols = st.columns([8, 8])
    df = data_df.round(1)
    with cols[0]:
        st.dataframe(df, use_container_width=True, hide_index=True)
    with cols[1]:
        kind = {"NET_WORTH": "NET_WORTH", "INFLOW": "INFLOW", "PROFIT": "PROFIT"}
        kind_sel = st.selectbox("Select kind", kind.keys(), label_visibility="collapsed")
        fig = px.line(df, x="DATE", y=kind[kind_sel], line_shape="spline")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=kind_sel,
            # Hide plotly buttons
            updatemenus=[],
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),  # Adjust top margin
            height=400  # Adjust overall height of the chart
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
with tabs[1]:
    date = fw.year_month_selector_oneline()
    last_row: pd.DataFrame = context.query_last_asset(date, acc, sub)
    cur_row: pd.DataFrame = context.query_subacc_by_date(date, acc, sub, False)
    last_net = 0 if last_row.empty else last_row.iloc[0]["NET_WORTH"]
    fw.show_last_and_cur_record(last_row, cur_row)

    net, inflow, profit = fw.net_inflow_profit_sync_input_with_helper(last_net)
    g: st = grid(4)
    if g.button("Submit", key=f"account_{acc}-{sub}_submit", type="primary", use_container_width=True):
        context.insert_or_update_asset(date, acc, sub, net, inflow, profit)
        fw.net_inflow_profit_sync_input_refresh()
        st.rerun()
    if g.button("Reset", key=f"account_{acc}-{sub}_reset", type="secondary", use_container_width=True):
        fw.net_inflow_profit_sync_input_refresh()
