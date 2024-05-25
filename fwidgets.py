import streamlit as st
import pandas as pd
from context import FinContext
import finutils as fu


@st.experimental_dialog("New asset")
def add_asset():
    context: FinContext = st.session_state['context']
    edit_on = st.toggle("New Account", key=st.session_state["acc_new_acc_toggle"])
    acc_name = ""
    if not edit_on:
        acc_name = st.selectbox("Select Account", [v.name for k, v in context.acc.items()])
    else:
        acc_name = st.text_input("New Account")

    sub_name = st.text_input("New Subaccount")

    cats = {}
    for k, v in context.cat_dict.items():
        cats[k] = st.selectbox(f"Category {k}:", v)

    if st.button("Submit", on_click=FinContext.add_asset, args=(context, acc_name, sub_name, cats), type="primary", key="acc_new_acc_submit"):
        st.rerun()


def editable_accounts(df=None, key=0):
    context: FinContext = st.session_state['context']
    col_config = {k: st.column_config.SelectboxColumn(k, options=v) for k, v in context.cat_dict.items()}
    if df is None:
        df = context.account_df()
    col_config.update({col: st.column_config.TextColumn(col, disabled=True) for col in df.columns if col not in context.cat_dict})
    return st.data_editor(df, hide_index=True, column_config=col_config, key=key)


def year_selector(key=0):
    year_list = list(range(2000, 2100))
    cur_year = fu.cur_year()
    index = 0
    if cur_year in year_list:
        index = cur_year - year_list[0]
    return st.selectbox("Year", year_list, index=index, key=key)


def month_radio(key=0):
    month_list = list(range(1, 13))
    cur_month = fu.cur_month()
    index = cur_month - month_list[0]
    return st.radio("Month", month_list, index=index, key=key, horizontal=True)


@st.experimental_dialog("ADD OR UPDATE SUBACCOUNT RECORD")
def insert_or_update_record_dia(acc_name, sub_name):
    context: FinContext = st.session_state["context"]
    year = year_selector(key="add_asset_dia_year")
    month = month_radio(key="add_asset_dia_month")
    date = pd.Period(year=year, month=month, freq="M").strftime("%Y-%m")

    last_row: pd.DataFrame = context.query_last_data(date, acc_name, sub_name)
    cur_row: pd.DataFrame = context.query_subacc_by_date(date, acc_name, sub_name, False)
    last_net = 0 if last_row.empty else last_row.iloc[0]["NET_WORTH"]

    info_df = pd.concat([last_row, cur_row], ignore_index=True)
    info_df = info_df[["DATE", "NET_WORTH", "INFLOW", "PROFIT"]]

    info_str = ""
    if (not last_row.empty) and (not cur_row.empty):
        info_str = f"Found existing data and previous record:"
    elif not last_row.empty:
        info_str = f"The previous record:"
    elif not cur_row.empty:
        info_str = f"Found existing data:"

    if not info_df.empty:
        info_df = fu.format_dec_df(info_df, ["NET_WORTH", "INFLOW", "PROFIT"])
        st.info(info_str)
        st.table(info_df)
    else:
        st.info(f"Doesn't find previous record")

    if st.toggle("Auto fill", value=True, key="ass_add_ass_record_toggle"):

        def update(last_change):
            if "ass_add_ass_record_period_input0" not in st.session_state:
                return
            net_change = st.session_state["ass_add_ass_record_period_input0"] - last_net
            print(net_change)
            if last_change == "ass_add_ass_record_period_input1":
                st.session_state["ass_add_ass_record_period_input2"] = net_change - st.session_state["ass_add_ass_record_period_input1"]
            elif last_change == "ass_add_ass_record_period_input2":
                st.session_state["ass_add_ass_record_period_input1"] = net_change - st.session_state["ass_add_ass_record_period_input2"]
            else:
                st.exception(RuntimeError("should not reach here"))
            return

        net = st.number_input("NET_WORTH", key="ass_add_ass_record_period_input0")
        invest = st.number_input("INFLOW", key="ass_add_ass_record_period_input1", on_change=update, args=("ass_add_ass_record_period_input1",))
        profit = st.number_input("PROFIT", key="ass_add_ass_record_period_input2", on_change=update, args=("ass_add_ass_record_period_input2",))
    else:
        net = st.number_input("NET_WORTH", key="ass_add_ass_record_period_input0")
        invest = st.number_input("INFLOW", key="ass_add_ass_record_period_input1")
        profit = st.number_input("PROFIT", key="ass_add_ass_record_period_input2")

    if st.button("Submit", key="ass_add_ass_record_button", type="primary"):
        context.insert_or_update(date, acc_name, sub_name, net, invest, profit)
        st.rerun()
