import streamlit as st
import pandas as pd
import sys
import re
from streamlit_extras.grid import grid
from streamlit_pills import pills

sys.path.append("..")

from src.context import FinContext
from src.finsql import ASSET_TABLE
from src.st_utils import FinLogger
import src.fwidgets as fw
import src.finutils as fu

st.set_page_config(page_title="Account", layout="wide")
st.title("Account")
st.divider()
context: FinContext = st.session_state['context']
acc_name_list = context.acc_name_list()

if not fw.check_account():
    st.stop()
if not fw.check_subaccount():
    st.stop()

ACC_KEY = "account_test_acc"


def clear_cicada_record_cache():
    st.session_state.pop(ACC_KEY, None)


def get_acc():
    if ACC_KEY not in st.session_state:
        st.session_state[ACC_KEY] = 0
    accid = st.session_state.get(ACC_KEY)
    if accid not in range(len(acc_name_list)):
        accid = 0
    acc_name = acc_name_list[accid]
    return acc_name


def set_acc(acc, key):
    st.session_state[ACC_KEY] = acc_name_list.index(acc)
    st.session_state[button_key] = fu.incre_str(st.session_state[button_key])


def format_func(name: str):
    return f"# {name}"


num_of_acc = len(acc_name_list)
GRID_COL_NUMBER = 7
grid_numbers = [GRID_COL_NUMBER] * (num_of_acc // GRID_COL_NUMBER + 1)
g: st = grid(*grid_numbers)

selected_acc = get_acc()
for acc in acc_name_list:
    t = "primary" if acc == selected_acc else "secondary"
    button_key = f"account_selection_{acc}"
    st.session_state[button_key] = f"{button_key}_value_0"
    g.button(acc, key=st.session_state[button_key], use_container_width=True, type=t, on_click=set_acc, args=(acc, button_key))

selected_acc = get_acc()

acc = selected_acc
sub_name_list = context.subacc_name_list(selected_acc)
if not sub_name_list:
    st.write(f"### You don't have any asset under account {acc}.")
    if st.button("Add asset", type="primary", key="ass_add_asset"):
        fw.add_account()
    st.stop()

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

# if st.toggle("Add/Update record", key=f"add_or_update_record_toggle_{acc}"):
with tabs[0]:
    data_df = context.asset_df(selected_acc, sub)
    data_df.sort_values("DATE", ascending=False, inplace=True)
    st.table(data_df)
with tabs[1]:
    date = fw.year_month_selector_oneline()
    last_row: pd.DataFrame = context.query_last_data(date, acc, sub)
    cur_row: pd.DataFrame = context.query_subacc_by_date(date, acc, sub, False)
    last_net = 0 if last_row.empty else last_row.iloc[0]["NET_WORTH"]
    fw.show_last_and_cur_record(last_row, cur_row)

    # net, invest, profit = fw.net_inflow_profit_sync_input(last_net)
    net, invest, profit = fw.net_inflow_profit_sync_input_with_helper(last_net)
    g: st = grid(4)
    if g.button("Submit", key=f"account_{acc}-{sub}_submit", type="primary", use_container_width=True):
        context.insert_or_update(date, acc, sub, net, invest, profit)
        st.rerun()

# # return True if the iter take effect
# def acc_move(is_next) -> bool:
#     accid = st.session_state.get(ACC_KEY)
#     if accid is None:
#         FinLogger.should_not_reach_here()
#
#     if is_next:
#         accid += 1
#     else:
#         accid -= 1
#
#     if accid not in range(len(acc_name_list)):
#         return False
#
#     st.session_state[ACC_KEY] = accid
#     return True
# def iter_to_next() -> bool:
#     return acc_move(True)
# def iter_to_prev() -> bool:
#     return acc_move(False)
