from typing import Sequence
from streamlit_extras.tags import tagger_component
import streamlit as st
import warnings
import json
import zipfile

warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
from streamlit_extras.grid import grid
from src.context import FinContext
import src.finutils as fu
from src.st_utils import FinLogger


def check_context():
    if "context" not in st.session_state:
        st.switch_page("Home.py")


def check_account():
    context: FinContext = st.session_state['context']
    if not context.config.acc:
        st.warning("You don't have any account, go to Account management page to create one")
        return False
    return True


def check_subaccount():
    context: FinContext = st.session_state['context']
    for acc in context.config.acc:
        if len(context.config.acc[acc].sub_name_list()) == 0:
            st.warning(f"You don't have any subaccount under {acc}, go to Account management page to create one")
            return False
    return True


def check_database():
    context: FinContext = st.session_state['context']
    if not context.validate():
        init_db()
        st.stop()
    return True


def check_all():
    check_context()
    if not check_database():
        st.stop()
    if not check_account():
        st.stop()
    if not check_subaccount():
        st.stop()


@st.dialog("New Account")
def add_account():
    context: FinContext = st.session_state['context']
    edit_on = st.toggle("New Account", key=st.session_state["acc_new_acc_toggle"])
    acc_name = ""
    if not edit_on:
        acc_name = st.selectbox("Select Account", context.config.acc_name_list())
    else:
        acc_name = st.text_input("New Account")

    sub_name = st.text_input("New Subaccount")

    cats = {}
    for k, v in context.config.cat_dict.items():
        cats[k] = st.selectbox(f"Category {k}:", v)

    if st.button("Submit", type="primary", key="acc_new_acc_submit"):
        context.config.add_asset(acc_name, sub_name, cats)
        st.rerun()


@st.dialog("Delete Account")
def delete_account():
    context: FinContext = st.session_state['context']
    acc_name = st.selectbox("Select Account", context.config.acc_name_list())
    sub_name = st.selectbox("Select Subaccount", context.config.subacc_name_list(acc_name))

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


def year_selector(key: str = "year_selector_0", container=st):
    year_list = list(range(2000, 2100))
    cur_year = fu.cur_year()
    index = 0
    if cur_year in year_list:
        index = cur_year - year_list[0]
    return container.selectbox("Year", year_list, index=index, key=key)


def month_radio(key="month_radio_0", container=st):
    month_list = list(range(1, 13))
    cur_month = fu.cur_month()
    index = cur_month - month_list[0]
    # key = f"{key}_{random.random()}"
    return container.radio("Month", month_list, index=index, key=key, horizontal=True)


def year_month_selector(key=0, container=st):
    year = year_selector(key=f"add_asset_dia_year_{key}", container=container)
    month = month_radio(key=f"add_asset_dia_month_{key}", container=container)
    return fu.get_date(year, month)


def year_month_selector_oneline(key=0):
    g: st = grid([1, 7])
    return year_month_selector(0, g)


@st.dialog("RESET DATA TO SAMPLE DATA")
def reset_sample_data_dia():
    st.write("# WARNING: All of your data will be reset and can not recover")
    if st.button("Confirm", key="side_bar_reset_dia_confirm"):
        context: FinContext = st.session_state['context']
        context.initialize_with_sample_data()
        st.rerun()


@st.dialog("CLEAR DATA")
def clear_data_dia():
    st.write("# WARNING: All of your data will be clear and can not recover")
    if st.button("Confirm", key="side_bar_clear_dia_confirm"):
        context: FinContext = st.session_state['context']
        context.config.clear_config()
        context.config.write_config()
        context.init_db()
        st.rerun()


@st.dialog("Load asset data from csv file")
def load_from_csv_dia():
    context: FinContext = st.session_state['context']
    upload_file = st.file_uploader("Choose a csv file")
    if upload_file is not None:
        data_df = pd.read_csv(upload_file)
        valid, err_msg = context.verify_asset_df(data_df)
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
                d.extend([None] * len(context.config.cat_dict))
                acc_data.append(d)

            cols = ["ACCOUNT", "SUBACCOUNT"]
            cols.extend([k for k in context.config.cat_dict])

            if acc_data:
                acc_df = pd.DataFrame(columns=cols, data=acc_data)
                acc_df = editable_accounts(acc_df, key="load_csv_acc_edit_df", container_width=True)
            else:
                st.info("You don't have any missing account in uploaded csv")

        if st.button("Submit", key="load_csv_submit", type="primary"):
            context.df_to_asset(acc_df)
            context.config.add_account_from_df(acc_df)
            st.rerun()

        st.write("Your uploaded file:")
        st.table(data_df)

    else:
        st.warning("You need to upload a csv file")


@st.dialog("Load zipped data")
def load_from_zipped_dia():
    st.warning("Load from zipped data will clear up all of yours data!")
    context: FinContext = st.session_state['context']
    upload_file = st.file_uploader("Choose a zip file")
    if upload_file is not None:
        file_list = ["asset.txt", "flow.txt", "config.json"]
        with zipfile.ZipFile(upload_file, "r") as z:
            files = z.namelist()
            for f in file_list:
                FinLogger.expect_and_stop(f in files, f"Doesn't find {f} in uploaded zip")
        if st.button("Submit", key="load_zipped_file_submit", type="primary", use_container_width=True):
            context.config.clear_config()
            context.config.write_config()
            context.init_db()
            context.load_from_zip_data(upload_file)
            st.rerun()
    else:
        st.button("Submit", key="load_zipped_file_submit_disable", type="secondary", use_container_width=True, disabled=True)


@st.dialog("Unsupported function")
def unsupported_dia(err_msg):
    st.info(f"Sorry, {err_msg} is not supported yet")


@st.dialog("Your database is not valid")
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
        g: st = grid(3, vertical_align="bottom")
        net = g.number_input("NET_WORTH", key="ass_add_ass_record_period_input0", value=last_net, on_change=update, args=("input0",))
        inflow = g.number_input("INFLOW", key="ass_add_ass_record_period_input1", on_change=update, args=("input1",))
        profit = g.number_input("PROFIT", key="ass_add_ass_record_period_input2", on_change=update, args=("input2",))
    else:
        g: st = grid(3, vertical_align="bottom")
        net = g.number_input("NET_WORTH", key="ass_add_ass_record_period_input0")
        inflow = g.number_input("INFLOW", key="ass_add_ass_record_period_input1")
        profit = g.number_input("PROFIT", key="ass_add_ass_record_period_input2")

    return net, inflow, profit


def record_input_helper(key="record_input_helper", default=0, on_change=None):
    key_of_num_record = f"{key}_num_record"
    if key_of_num_record not in st.session_state:
        st.session_state[key_of_num_record] = 1
    num_record = st.session_state[key_of_num_record]

    def update(total_key, single_key, number_key, exchange_key, is_total_input):
        if not is_total_input:
            st.session_state[total_key] = st.session_state[single_key] * st.session_state[number_key] * st.session_state[exchange_key]
        else:
            st.session_state[single_key] = st.session_state[total_key]
            st.session_state[number_key] = 1
            st.session_state[exchange_key] = 1
        if on_change is not None:
            pass
            # on_change(net)

    total_net_worth = 0
    for i in range(num_record):
        g: st = grid(4)
        total_key = f"{key}_total_value_{i}"
        single_key = f"{key}_single_value_{i}"
        number_key = f"{key}_number_{i}"
        exchange_key = f"{key}_exchange_{i}"

        default_total = default if i == 0 else 0

        update_args = (total_key, single_key, number_key, exchange_key, True)
        value = g.number_input("Value", key=total_key, value=default_total, on_change=update, args=update_args)
        # update(*update_args)
        update_args = (total_key, single_key, number_key, exchange_key, False)
        single_value = g.number_input("Unit value", key=single_key, on_change=update, args=update_args, value=default_total)
        number = g.number_input("Number of unit", key=number_key, on_change=update, args=update_args, value=1.0)
        exchange = g.number_input("Exchange", key=exchange_key, on_change=update, args=update_args, value=1.0)
        total_net_worth += value

    return total_net_worth


def record_input_helper_clear(key="record_input_helper"):
    key_of_num_record = f"{key}_num_record"
    st.session_state.pop(key_of_num_record, None)
    i = 0
    total_key = f"{key}_total_value_{i}"
    single_key = f"{key}_single_value_{i}"
    number_key = f"{key}_number_{i}"
    exchange_key = f"{key}_exchange_{i}"
    for k in [total_key, single_key, number_key, exchange_key]:
        st.session_state.pop(k, None)


def net_inflow_profit_sync_input_refresh():
    st.session_state["ass_add_ass_record_refresh"] = True


def net_inflow_profit_sync_input_with_helper(last_net):

    def update(last_change, net_worth):
        net_change = net_worth - last_net
        if last_change == "input1":
            st.session_state["ass_add_ass_record_period_input2"] = net_change - st.session_state["ass_add_ass_record_period_input1"]
        elif last_change == "input2":
            st.session_state["ass_add_ass_record_period_input1"] = net_change - st.session_state["ass_add_ass_record_period_input2"]
        else:
            st.exception(RuntimeError("should not reach here"))
        return

    def refresh(net):
        if "ass_add_ass_record_refresh" not in st.session_state:
            st.session_state["ass_add_ass_record_refresh"] = False
        if st.session_state["ass_add_ass_record_refresh"]:
            st.session_state["ass_add_ass_record_refresh"] = False
            if "ass_add_ass_record_period_input1" in st.session_state and "ass_add_ass_record_period_input2" in st.session_state:
                st.session_state["ass_add_ass_record_period_input1"] = 0
                update("input1", net)

    def net_worth_update(net):
        inflow = st.session_state.get("ass_add_ass_record_period_input1", 0)
        st.session_state["ass_add_ass_record_period_input2"] = net - inflow

    # if st.toggle("Helper", value=True, key="ass_add_ass_record_toggle"):
    if True:
        net = record_input_helper("net_worth", default=last_net, on_change=net_worth_update)
        g: st = grid(4, vertical_align="bottom")
        st.session_state["ass_add_ass_record_period_input_0"] = net
        refresh(net)
        g.number_input("NET WORTH", key="ass_add_ass_record_period_input_0", disabled=True, value=net)
        increase = net - last_net
        inflow = g.number_input("INFLOW", key="ass_add_ass_record_period_input1", on_change=update, args=("input1", net), value=0)
        profit = g.number_input("PROFIT", key="ass_add_ass_record_period_input2", on_change=update, args=("input2", net), value=increase)
    else:
        g: st = grid(4, vertical_align="bottom")
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
        st.table(info_df)
    else:
        st.info(f"Doesn't find previous record")


@st.dialog("ADD OR UPDATE SUBACCOUNT RECORD")
def insert_or_update_record_dia(acc: str, sub: str):
    date = year_month_selector()

    context: FinContext = st.session_state["context"]
    last_row: pd.DataFrame = context.query_last_data(date, acc, sub)
    cur_row: pd.DataFrame = context.query_subacc_by_date(date, acc, sub, False)
    last_net = 0 if last_row.empty else last_row.iloc[0]["NET_WORTH"]

    show_last_and_cur_record(last_row, cur_row)

    net, invest, profit = net_inflow_profit_sync_input(last_net)

    if st.button("Submit", key="ass_add_ass_record_button", type="primary"):
        context.insert_or_update_asset(date, acc, sub, net, invest, profit)
        st.rerun()


@st.dialog("DELETE SUBACCOUNT")
def delete_subaccount_dia(acc: str, sub: str):
    st.write(f"## WARNING!")
    st.write(f"**You are DELETING your asset {sub} under {acc}, this will clear your data in database**")

    if st.button("DELETE", key="delete_dialog_delete", on_click=FinContext.delete_asset, args=(st.session_state["context"], acc, sub)):
        st.rerun()

    if st.button("Cancel", key="delete_dialog_cancel", type="primary"):
        st.rerun()


@st.dialog("DELETE SELECTED DATA")
def delete_selected_data_dia(acc: str, sub: str, date_list: list[str]):
    context: FinContext = st.session_state["context"]
    st.write(f"## WARNING!")
    st.write(f"**You are DELETING your data under asset {sub}, this will remove your data in database**")
    date_list_str = ", ".join(date_list)
    st.write(f"Date will be removed: {date_list_str}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("DELETE", key="delete_dialog_delete", use_container_width=True):
            for date in date_list:
                context.delete_asset_data(date, acc, sub)
            st.rerun()

    with col2:
        if st.button("Cancel", key="delete_dialog_cancel", type="primary", use_container_width=True):
            st.rerun()


def get_st_color_str_by_pos(value, pos_color: str = "green", neg_color: str = "red") -> str:
    color = f":{pos_color}-background" if value >= 0 else f":{neg_color}-background"
    return color


def clear_add_money_flow_dia_state():
    st.session_state["add_money_flow_new_tags"] = []


@st.dialog("ADD A MONEY FLOW", width="large")
def add_money_flow_dia(date: str):
    context: FinContext = st.session_state["context"]
    tran_type = st.selectbox("Type", ["INCOME", "OUTLAY"], key="add_money_flow_type_input")
    value = st.number_input("Value", key="add_money_flow_number_input")
    tag_candidates = context.get_tran_tags()
    tags = st.multiselect("Tags", tag_candidates, key="add_money_flow_cat_input")

    if "add_money_flow_new_tags" not in st.session_state:
        st.session_state["add_money_flow_new_tags"] = []
    new_tags: list[str] = st.session_state["add_money_flow_new_tags"]
    g: st = grid([3, 1], vertical_align="bottom")
    new_tag = g.text_input("New tags", key="add_money_flow_new_tags_text_input")
    if g.button("Add", key="add_money_flow_new_tags_add_button", use_container_width=True):
        new_tags.append(new_tag)
    # st.write("Tags will be added: ", ", ".join(new_tags))
    tagger_component("Tags will be added: ", new_tags)

    note = st.text_input("Note", key="add_money_flow_note_input")
    if st.button("Submit", key="add_money_flow_submit_button", use_container_width=True, type="primary"):
        new_tags = set(new_tags)
        new_tags = [x for x in new_tags if x not in tags]
        context.insert_tran(date, tran_type, value, ",".join(tags + new_tags), note)
        clear_add_money_flow_dia_state()
        st.rerun()


@st.dialog("Confirm")
def confirm_dia(func, args, info):
    st.warning(info)
    if st.button("Confirm", key="confirm_dia_button"):
        func(*args)
        st.rerun()


@st.dialog("Delete selected money flow record")
def delete_selected_money_flow_dia(id_list: list[int]):
    context: FinContext = st.session_state["context"]
    st.warning("**You are DELETING your money flow record:**")
    df = context.query_tran()
    df = df[df["ID"].isin(id_list)]
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


def get_date_list() -> list[str]:
    context: FinContext = st.session_state["context"]
    cur_date = fu.norm_date(fu.cur_date())
    s, e = context.get_date_range()
    date_list = fu.date_list(s, max(cur_date, e))
    return date_list


def get_year_list() -> list[int]:
    context: FinContext = st.session_state["context"]
    s, e = context.get_date_range()
    year_list = fu.year_list(s, e)
    return year_list


@st.dialog("Load Accounts config from json file")
def load_acc_config_from_json_dia():
    context: FinContext = st.session_state["context"]
    upload_file = st.file_uploader("Choose a json file")
    if upload_file is not None:
        config = json.load(upload_file)
        if st.button("Submit", key="load_config_from_json_submit", type="primary"):
            context.config.load_from_dict(config)
            context.config.write_config()
            st.rerun()
        st.json(config, expanded=True)
    else:
        st.warning("You need to upload a config json file")


def button_selector(key: str, candidate_list: Sequence[str], col_number: int = 4, default: int = 0, selected_txt : Sequence[str] = []) -> int:

    def get_selected_index() -> int:
        if key not in st.session_state:
            st.session_state[key] = default
        index = st.session_state.get(key)
        if index not in range(len(candidate_list)):
            index = default
        return index

    def set_selected(index: int, button_key: str):
        st.session_state[key] = index
        st.session_state[button_key] = fu.incre_str(st.session_state[button_key])

    if selected_txt:
        assert len(selected_txt) == len(candidate_list)
    else:
        selected_txt = candidate_list

    num = len(candidate_list)
    grid_numbers = [col_number] * (num // col_number + 1)
    g: st = grid(*grid_numbers)

    for index, name in enumerate(candidate_list):
        button_key = f"{key}_{name}"
        t = "secondary"
        button_txt = name
        if index == get_selected_index():
            t = "primary"
            button_txt = selected_txt[index]
        st.session_state[button_key] = f"{button_key}_value_0"
        g.button(button_txt, key=st.session_state[button_key], use_container_width=True, type=t, on_click=set_selected, args=(index, button_key))

    return get_selected_index()


def month_selector(key: str, col_number=4, default: int = 1) -> int:
    assert default in range(1, 13)
    return button_selector(key, fu.month_list(), col_number, default - 1, fu.month_list()) + 1
