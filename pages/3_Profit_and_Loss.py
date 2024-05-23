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

e, l = context.get_date_range()
profit_waterfall = context.profit_waterfall(e, l)
st.plotly_chart(profit_waterfall, theme="streamlit", use_container_width=True)
