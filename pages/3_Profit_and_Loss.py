import streamlit as st
import sys
import pandas as pd

sys.path.append("..")
from context import FinContext
from st_utils import FinWidgets
import fwidgets as fw
import finutils as fu

context: FinContext = st.session_state['context']

st.set_page_config(page_title="Profit and Loss")
st.sidebar.header("Profit and Loss")
st.header("Profit and Loss")

s, e = context.get_date_range()
date_list = fu.date_list(s, e)
start_date, end_date = st.select_slider("Select a period", options=date_list, value=(s, e))

profit_waterfall = context.profit_waterfall(start_date, end_date)
st.plotly_chart(profit_waterfall, theme="streamlit", use_container_width=True)
