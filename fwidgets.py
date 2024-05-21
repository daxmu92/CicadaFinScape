import streamlit as st
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

    asset_name = st.text_input("New Asset")

    cats = {}
    for k, v in context.cat_dict.items():
        cats[k] = st.selectbox(f"Category {k}:", v)

    if st.button("Submit", on_click=FinContext.add_asset, args=(context, acc_name, asset_name, cats), type="primary", key="acc_new_acc_submit"):
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
