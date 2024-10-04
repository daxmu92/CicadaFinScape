import pandas as pd
import streamlit as st
import sys
from streamlit_extras.grid import grid

sys.path.append("..")
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu

context: FinContext = st.session_state['context']

st.set_page_config(page_title="Income and Expense")
st.title("Income and Expense")
st.divider()

tran_df = context.query_tran()
enable_edit = st.toggle("Edit", False, key="income_and_expense_toggle")
if enable_edit:
    col_configs = {k: st.column_config.TextColumn(k, disabled=False) for k in tran_df.columns}
    col_configs["TYPE"] = st.column_config.SelectboxColumn("TYPE", options=["INCOME", "OUTLAY"])
    col_configs["DATE"] = st.column_config.SelectboxColumn("DATE", options=fw.get_date_list(), required=True)
    col_configs["ID"] = st.column_config.TextColumn(disabled=True)
    col_configs["VALUE"] = st.column_config.NumberColumn(required=True)
    df = st.data_editor(tran_df, hide_index=True, key="money_flow_df", use_container_width=True, column_config=col_configs, num_rows="dynamic")
    cols = st.columns(2)
    with cols[0]:
        if st.button("Submit", key="add_new_money_flow_submit_button", use_container_width=True, type="primary"):
            context.df_to_tran(df)
            st.rerun()
    with cols[1]:
        if st.button("Cancel", key="add_money_flow_cancel_button", use_container_width=True):
            st.session_state["income_and_expense_toggle"] = False
            st.rerun()
else:
    col_configs = {k: st.column_config.TextColumn(k, disabled=True) for k in tran_df.columns}
    tran_df["Select"] = False
    check_col_config = st.column_config.CheckboxColumn("Select", default=False)
    col_configs["Select"] = check_col_config
    df = st.data_editor(tran_df, hide_index=True, key="money_flow_df", use_container_width=True, column_config=col_configs)
    id_list = df.loc[df["Select"]]["ID"].tolist()

    cols = st.columns(2)
    with cols[0]:
        if st.button("**Add money flow record**", key="add_new_money_flow_button", use_container_width=True, type="primary"):
            fw.add_money_flow_dia()
    with cols[1]:
        if st.button("**Delet selected record**", key="delete_money_flow_button", use_container_width=True):
            fw.delete_selected_money_flow_dia(id_list)

io_df = context.income_outlay_df()
df = io_df.style.format(precision=1)
st.table(df)
