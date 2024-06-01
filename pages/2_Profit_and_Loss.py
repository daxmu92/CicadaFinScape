import streamlit as st
import sys
import pandas as pd

sys.path.append("..")
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu

context: FinContext = st.session_state['context']

st.set_page_config(page_title="Profit and Loss")
st.title("Profit and Loss")
st.divider()

fw.check_all()

s, e = context.get_date_range()
date_list = fu.date_list(s, e)
start_date, end_date = st.select_slider("Select a period", options=date_list, value=(s, e))

profit_waterfall = context.profit_waterfall(start_date, end_date)
st.plotly_chart(profit_waterfall, theme="streamlit", use_container_width=True)
