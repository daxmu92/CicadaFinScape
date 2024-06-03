import streamlit as st
import warnings
import json

warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
from streamlit_extras.grid import grid
from src.context import FinContext
import src.finsql as finsql
import src.finutils as fu


def check_account():
    context: FinContext = st.session_state['context']
    if not context.acc:
        st.warning("You don't have any account, go to Account management page to create one")
        return False
    return True


def check_subaccount():
    context: FinContext = st.session_state['context']
    for acc in context.acc:
        if len(context.acc[acc].asset_list) == 0:
            st.warning(f"You don't have any subaccount under {acc}, go to Account management page to create one")
            return False
    return True


def check_database():
    context: FinContext = st.session_state['context']
    if context.db_empty():
        st.warning(f"You don't have any data record, go to Account/Cicada journey page to add record")
        return False
    return True


def check_all():
    if not check_account():
        st.stop()
    if not check_subaccount():
        st.stop()
    if not check_database():
        st.stop()


@st.experimental_dialog("New Account")
def add_account():
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


@st.experimental_dialog("Delete Account")
def delete_account():
    context: FinContext = st.session_state['context']
    acc_name = st.selectbox("Select Account", [v.name for k, v in context.acc.items()])
    sub_name = st.selectbox("Select Subaccount", [x.name for x in context.acc[acc_name].asset_list])

    if st.button("DELETE", key="acc_delete_sub_acc_delete"):
        context.delete_asset(acc_name, sub_name)
        st.rerun()

def editable_accounts(df=None, key=0, container_width=False):
    context: FinContext = st.session_state['context']
    col_config = {k: st.column_config.SelectboxColumn(k, options=v) for k, v in context.cat_dict.items()}
    if df is None:
        df = context.account_df()
    col_config.update({col: st.column_config.TextColumn(col, disabled=True) for col in df.columns if col not in context.cat_dict})
    return st.data_editor(df, hide_index=True, column_config=col_config, key=key, use_container_width=container_width)


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

def year_month_selector(key=0):
    year = year_selector(key="add_asset_dia_year")
    month = month_radio(key="add_asset_dia_month")
    date = pd.Period(year=year, month=month, freq="M").strftime("%Y-%m")
    return date


@st.experimental_dialog("RESET DATA TO SAMPLE DATA")
def reset_sample_data_dia():
    st.write("# WARNING: All of your data will be reset and can not recover")
    if st.button("Confirm", key="side_bar_reset_dia_confirm"):
        context: FinContext = st.session_state['context']
        context.initialize_with_sample_data()
        st.rerun()


@st.experimental_dialog("CLEAR DATA")
def clear_data_dia():
    st.write("# WARNING: All of your data will be clear and can not recover")
    if st.button("Confirm", key="side_bar_clear_dia_confirm"):
        context: FinContext = st.session_state['context']
        context.clear_config()
        context.write_config()
        context.init_db()
        st.rerun()


@st.experimental_dialog("Load data from csv file")
def load_from_csv_dia():
    context: FinContext = st.session_state['context']
    upload_file = st.file_uploader("Choose a csv file")
    if upload_file is not None:
        data_df = pd.read_csv(upload_file)
        valid, err_msg = context.verify_df(data_df)
        if not valid:
            st.error(err_msg)
            st.stop()

        acc_df = None
        add_missing_acc = st.toggle("Add missing account/asset", value=True, key="load_csv_dia_toggle")

        if add_missing_acc:
            new_ass: set[tuple] = set()
            for index, row in data_df.iterrows():
                acc_name = row["ACCOUNT"]
                sub_name = row["SUBACCOUNT"]
                if not context.has_asset(acc_name, sub_name):
                    new_ass.add((acc_name, sub_name))

            acc_data = []
            for i in new_ass:
                d = list(i)
                d.extend([None] * len(context.cat_dict))
                acc_data.append(d)

            cols = ["ACCOUNT", "SUBACCOUNT"]
            cols.extend([k for k in context.cat_dict])

            if acc_data:
                acc_df = pd.DataFrame(columns=cols, data=acc_data)
                acc_df = editable_accounts(acc_df, key="load_csv_acc_edit_df", container_width=True)
            else:
                st.info("You don't have any missing account in uploaded csv")

        if st.button("Submit", key="load_csv_submit", type="primary"):
            context.load_from_df(data_df)
            context.add_account_from_df(acc_df)
            st.rerun()

        st.write("Your uploaded file:")
        st.table(data_df)

    else:
        st.warning("You need to upload a csv file")


@st.experimental_dialog("Your database is not valid")
def init_db():
    st.write("# Initialize your database? All of the data in database will be reset and can not recover")
    if st.button("Confirm", key="initial_reset_dia_confirm"):
        context: FinContext = st.session_state['context']
        context.init_db()
        st.rerun()


def net_inflow_profit_sync_input(last_net):

    def update(last_change):
        if "ass_add_ass_record_period_input0" not in st.session_state:
            return
        net_change = st.session_state["ass_add_ass_record_period_input0"] - last_net
        if last_change == "input0":
            st.session_state["ass_add_ass_record_period_input2"] = net_change - st.session_state["ass_add_ass_record_period_input1"]
        elif last_change == "input1":
            st.session_state["ass_add_ass_record_period_input2"] = net_change - st.session_state["ass_add_ass_record_period_input1"]
        elif last_change == "input2":
            st.session_state["ass_add_ass_record_period_input1"] = net_change - st.session_state["ass_add_ass_record_period_input2"]
        else:
            st.exception(RuntimeError("should not reach here"))
        return

    if st.toggle("Auto fill", value=True, key="ass_add_ass_record_toggle"):
        g = grid(3, vertical_align="bottom")
        net = g.number_input("NET_WORTH", key="ass_add_ass_record_period_input0", value=last_net, on_change=update, args=("input0",))
        inflow = g.number_input("INFLOW", key="ass_add_ass_record_period_input1", on_change=update, args=("input1",))
        profit = g.number_input("PROFIT", key="ass_add_ass_record_period_input2", on_change=update, args=("input2",))
    else:
        g = grid(3, vertical_align="bottom")
        net = g.number_input("NET_WORTH", key="ass_add_ass_record_period_input0")
        inflow = g.number_input("INFLOW", key="ass_add_ass_record_period_input1")
        profit = g.number_input("PROFIT", key="ass_add_ass_record_period_input2")

    return net, inflow, profit


def show_last_and_cur_record(last_row: pd.DataFrame, cur_row: pd.DataFrame):
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


@st.experimental_dialog("ADD OR UPDATE SUBACCOUNT RECORD")
def insert_or_update_record_dia(acc, sub):
    date = year_month_selector()

    context: FinContext = st.session_state["context"]
    last_row: pd.DataFrame = context.query_last_data(date, acc, sub)
    cur_row: pd.DataFrame = context.query_subacc_by_date(date, acc, sub, False)
    last_net = 0 if last_row.empty else last_row.iloc[0]["NET_WORTH"]

    show_last_and_cur_record(last_row, cur_row)

    net, invest, profit = net_inflow_profit_sync_input(last_net)

    if st.button("Submit", key="ass_add_ass_record_button", type="primary"):
        context.insert_or_update(date, acc, sub, net, invest, profit)
        st.rerun()

@st.experimental_dialog("DELETE SUBACCOUNT")
def delete_subaccount_dia(acc_name, sub_name):
    st.write(f"## WARNING!")
    st.write(f"**You are DELETING your asset {sub_name} under {acc_name}, this will clear your data in database**")

    if st.button("DELETE", key="delete_dialog_delete", on_click=FinContext.delete_asset, args=(st.session_state["context"], acc_name, sub_name)):
        st.rerun()

    if st.button("Cancel", key="delete_dialog_cancel", type="primary"):
        st.rerun()


@st.experimental_dialog("DELETE SELECTED DATA")
def delete_selected_data_dia(acc_name, sub_name, date_list: list):
    context: FinContext = st.session_state["context"]
    st.write(f"## WARNING!")
    st.write(f"**You are DELETING your data under asset {sub_name}, this will remove your data in database**")
    date_list_str = ", ".join(date_list)
    st.write(f"Date will be removed: {date_list_str}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("DELETE", key="delete_dialog_delete", use_container_width=True):
            for date in date_list:
                context.delete_data(date, acc_name, sub_name)
            st.rerun()

    with col2:
        if st.button("Cancel", key="delete_dialog_cancel", type="primary", use_container_width=True):
            st.rerun()


def get_st_color_str_by_pos(value, pos_color="green", neg_color="red"):
    color = f":{pos_color}-background" if value >= 0 else f":{neg_color}-background"
    return color


@st.experimental_dialog("ADD A MONEY FLOW")
def add_money_flow_dia():
    context: FinContext = st.session_state["context"]
    date = year_month_selector()
    tran_type = st.selectbox("Type", [finsql.TRAN_INCOME_NAME, finsql.TRAN_OUTLAY_NAME], key="add_money_flow_type_input")
    value = st.number_input("Value", key="add_money_flow_number_input")
    cat = st.text_input("Category", key="add_money_flow_cat_input")
    note = st.text_input("Note", key="add_money_flow_note_input")
    if st.button("Submit"):
        context.insert_tran(date, tran_type, value, cat, note)
        st.rerun()


@st.experimental_dialog("Confirm")
def confirm_dia(func, args, info):
    st.warning(info)
    if st.button("Confirm", key="confirm_dia_button"):
        func(*args)
        st.rerun()


@st.experimental_dialog("Delete selected money flow record")
def delete_selected_money_flow_dia(id_list: list[int]):
    context: FinContext = st.session_state["context"]
    st.warning("**You are DELETING your money flow record:**")
    df = context.query_tran_all()
    df = df[df[finsql.COL_TRAN_ID.name].isin(id_list)]
    st.table(df)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("DELETE", key="delete_money_flow_dialog_delete", use_container_width=True):
            for id in id_list:
                context.delete_tran(id)
            st.rerun()

    with col2:
        if st.button("Cancel", key="delete_money_flow_dialog_cancel", type="primary", use_container_width=True):
            st.rerun()


def get_date_list():
    context: FinContext = st.session_state["context"]
    cur_date = fu.norm_date(fu.cur_date())
    s, e = context.get_date_range()
    date_list = fu.date_list(s, max(cur_date, e))
    return date_list


@st.experimental_dialog("Load Accounts config from json file")
def load_acc_config_from_json_dia():
    context: FinContext = st.session_state["context"]
    upload_file = st.file_uploader("Choose a json file")
    if upload_file is not None:
        config = json.load(upload_file)
        if st.button("Submit", key="load_config_from_json_submit", type="primary"):
            context.load_config(config)
            context.write_config()
            st.rerun()
        st.json(config, expanded=True)
    else:
        st.warning("You need to upload a config json file")
