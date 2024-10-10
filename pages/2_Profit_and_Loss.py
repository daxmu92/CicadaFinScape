import streamlit as st
import sys
import pandas as pd

sys.path.append("..")
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu
import src.finchart as fc

st.set_page_config(page_title="Profit and Loss", layout="wide")
st.title("Profit and Loss")
st.divider()
fw.check_all()

context: FinContext = st.session_state['context']

cur_year = fu.cur_year()
index = fw.get_year_list().index(cur_year)
year = st.selectbox("Select year", fw.get_year_list(), index=index, label_visibility="collapsed", key="profit_and_loss_year_selector")

year_data = context.query_period_data(fu.get_date(year, 1), fu.get_date(year, 12)).groupby("DATE").sum()
total_profit = round(year_data["PROFIT"].sum(), 1)
st.write(f"Total profit: {fu.gen_txt_with_color_and_arrow(total_profit)}")
profit_list = [round(x, 1) for x in year_data["PROFIT"].tolist()]

month_list = fu.month_list()
candidate_txt_list = [f"# {m}\n{fu.gen_txt_with_color_and_arrow(profit)}" for m, profit in zip(month_list, profit_list)]
selected_txt_list = [f"# {m}\n{fu.gen_txt_with_arrow(profit)}" for m, profit in zip(month_list, profit_list)]
month = fw.button_selector("profit_and_loss_month_selector", candidate_txt_list, 6, fu.cur_month() - 1, selected_txt_list) + 1
selected_date = fu.get_date(year, month)

df = context.query_asset(date=selected_date)
st.plotly_chart(fc.profit_bar(df), use_container_width=True)

st.write("## \n" * 3)

st.divider()
