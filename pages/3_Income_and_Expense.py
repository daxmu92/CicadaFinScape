import streamlit as st
import sys
from streamlit_extras.grid import grid

sys.path.append("..")
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu
import src.finchart as fc

st.set_page_config(page_title="Income and Expense", layout="wide")
st.title("Income and Expense")
st.divider()
fw.check_all()

context: FinContext = st.session_state['context']

cur_year = fu.cur_year()
index = fw.get_year_list().index(cur_year)
year = st.selectbox("Select year", fw.get_year_list(), index=index, label_visibility="collapsed")
month = fw.month_selector("income_and_expense_month_selector", 6, fu.cur_month())

date = fu.get_date(year, month)
tran_df = context.query_tran(date).copy()

tabs = st.tabs(["Overview", "Add/Update Record"])

with tabs[0]:
    total_inflow = context.query_total_inflow(date)
    cols = st.columns(2)
    with cols[0]:
        fig, config = fc.io_flow_chart(tran_df, total_inflow)
        st.plotly_chart(fig, use_container_width=True, config=config)

    with cols[1]:
        total_income = tran_df[tran_df["TYPE"] == "INCOME"]["VALUE"].sum()
        tracked_outlay = tran_df[tran_df["TYPE"] == "OUTLAY"]["VALUE"].sum()
        total_outlay = total_income - total_inflow
        untracked_outlay = total_outlay - tracked_outlay
        st.write(f"###   Total income: {total_income}")
        st.write(f"###   Tracked outlay: {tracked_outlay}")
        st.write(f"###   Untracked outlay: {untracked_outlay}")
        st.write(f"###   Total outlay: {total_outlay}")

with tabs[1]:
    col_configs = {k: st.column_config.TextColumn(k, disabled=True) for k in tran_df.columns}
    tran_df["Select"] = False
    check_col_config = st.column_config.CheckboxColumn("Select", default=False)
    col_configs["Select"] = check_col_config
    df = st.data_editor(tran_df, hide_index=True, key="money_flow_df", use_container_width=True, column_config=col_configs)
    id_list = df.loc[df["Select"]]["ID"].tolist()

    row: st = grid(2, vertical_align="bottom")
    if row.button("**Add money flow record**", key="add_new_money_flow_button", use_container_width=True, type="primary"):
        fw.add_money_flow_dia()
    if row.button("**Delet selected record**", key="delete_money_flow_button", use_container_width=True):
        fw.delete_selected_money_flow_dia(id_list)

st.divider()
