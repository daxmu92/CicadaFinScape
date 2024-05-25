import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import sys

sys.path.append("..")

from context import FinContext
from finsql import ASSET_TABLE
from st_utils import FinLogger
import fwidgets as fw
import finutils as fu

st.title("Start a Cicada record journey")
st.divider()
context: FinContext = st.session_state['context']

acc_name_list = context.acc_name_list()
if len(acc_name_list) == 0:
    st.info("You don't have any account, go to account management page to create")
    st.stop()


def clear_cicada_record_cache():
    st.session_state.pop("cicada_record_journey_date", None)
    st.session_state.pop("cicada_record_journey_accid", None)
    st.session_state.pop("cicada_record_journey_subid", None)


# return True if the iter is end
def iter_to_next() -> bool:
    accid = st.session_state.get("cicada_record_journey_accid")
    if accid is None:
        FinLogger.should_not_reach_here()
    subid = st.session_state.get("cicada_record_journey_subid")
    if subid is None:
        FinLogger.should_not_reach_here()

    acc_name = acc_name_list[accid]
    sub_name_list = context.subacc_name_list(acc_name)

    subid += 1
    if subid == len(sub_name_list):
        accid += 1
        subid = 0

    if accid == len(acc_name_list):
        return True

    st.session_state["cicada_record_journey_accid"] = accid
    st.session_state["cicada_record_journey_subid"] = subid
    return False


def get_acc():
    if "cicada_record_journey_accid" not in st.session_state:
        st.session_state["cicada_record_journey_accid"] = 0
    if "cicada_record_journey_subid" not in st.session_state:
        st.session_state["cicada_record_journey_subid"] = 0

    accid = st.session_state.get("cicada_record_journey_accid")
    subid = st.session_state.get("cicada_record_journey_subid")
    acc_name = acc_name_list[accid]
    sub_name_list = context.subacc_name_list(acc_name)

    if len(sub_name_list) == 0:
        FinLogger.error(f"You don't have sub account under {acc_name}, please add one")
        FinLogger.should_not_reach_here()

    sub_name = sub_name_list[subid]

    return acc_name, sub_name


if "cicada_record_journey_date" not in st.session_state:
    st.info("Select a date")
    date = fw.year_month_selector()
    if st.button("Start", key="cicada_record_journey_start_button"):
        st.session_state["cicada_record_journey_date"] = date
        st.rerun()
    st.stop()

date = st.session_state["cicada_record_journey_date"]
acc, sub = get_acc()

last_row: pd.DataFrame = context.query_last_data(date, acc, sub)
cur_row: pd.DataFrame = context.query_subacc_by_date(date, acc, sub, False)
last_net = 0 if last_row.empty else last_row.iloc[0]["NET_WORTH"]

st.write(f"### :green-background[{acc}]-:orange-background[{sub}]:")
fw.show_last_and_cur_record(last_row, cur_row)

net, invest, profit = fw.net_inflow_profit_sync_input(last_net)


def new_record_menu_onchange(key):
    st.write(f"Calling {key}")
    # selection = st.session_state[key]
    selection = key
    if selection == "Submit":
        context.insert_or_update(date, acc, sub, net, invest, profit)
        end = iter_to_next()
        if end:
            clear_cicada_record_cache()
    elif selection == "Skip":
        end = iter_to_next()
        if end:
            clear_cicada_record_cache()
    elif selection == "Cancel":
        clear_cicada_record_cache()
    st.rerun()


col1, col2, col3 = st.columns([20, 18, 6])
with col1:
    if st.button("Submit", key=f"new_record_journey_menu_submit", type="primary"):
        new_record_menu_onchange("Submit")
with col2:
    if st.button("Skip", key=f"new_record_journey_menu_skip"):
        new_record_menu_onchange("Skip")
with col3:
    if st.button("Cancel", key=f"new_record_journey_menu_cancel"):
        new_record_menu_onchange("Cancel")

# TODO - use menu when https://github.com/victoryhb/streamlit-option-menu/issues/70 fixed
# journey_menu = option_menu(None, ["Submit", "Skip", "Cancel"],
#                         icons=['send', 'chevron-double-right', "x-square"],
#                         on_change=new_record_menu_onchange, key='new_record_journey_menu', orientation="horizontal", default_index=-1)
