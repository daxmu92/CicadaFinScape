import pandas as pd
import streamlit as st
import sys
from streamlit_extras.grid import grid

sys.path.append("..")
import src.finsql as finsql
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu

context: FinContext = st.session_state['context']

st.set_page_config(page_title="Income and Expense")
st.title("Income and Expense")
st.divider()

tran_df = context.query_tran_all()

enable_edit = st.toggle("Edit", False, key="income_and_expense_toggle")
if enable_edit:
    col_configs = {k: st.column_config.TextColumn(k, disabled=False) for k in tran_df.columns}
    col_configs[finsql.COL_TRAN_TYPE.name] = st.column_config.SelectboxColumn(finsql.COL_TRAN_TYPE.name, options=["Income", "Outlay"])
    col_configs[finsql.COL_DATE.name] = st.column_config.SelectboxColumn(finsql.COL_DATE.name, options=fw.get_date_list(), required=True)
    col_configs[finsql.COL_TRAN_ID.name] = st.column_config.TextColumn(disabled=True)
    col_configs[finsql.COL_TRAN_VALUE.name] = st.column_config.NumberColumn(required=True)
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
