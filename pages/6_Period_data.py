import streamlit as st
from streamlit_extras.grid import grid
import sys
import pandas as pd

sys.path.append("..")
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu
import src.finchart as fc

st.set_page_config(page_title="Period Data", layout="wide")
st.title("Period Data")
st.divider()
fw.check_all()

context: FinContext = st.session_state['context']

views = ["Asset", "Portfolio", "Cash Flow"]
view = st.selectbox("View", views, index=0, label_visibility="collapsed", key="period_data_view_selector")

s, e = context.get_date_range()
date_list = fu.date_list(s, e)
start_date, end_date = st.select_slider("Select a period", options=date_list, value=(s, e))

preset_candidates = ["5 years", "3 years", "1 year", "This year", "Custom"]
preset_result = fw.button_selector("period_data_preset_selector", preset_candidates, 5, 4, preset_candidates)

if view == "Asset":
    df = context.query_period_data(start_date, end_date)
    df = df.groupby("DATE").sum().reset_index()
    # accumulate profit
    df["PROFIT"] = df["PROFIT"].cumsum()
    # # accumulate inflow
    df["INFLOW"] = df["INFLOW"].cumsum()
    st.plotly_chart(fc.asset_view_chart(df), use_container_width=True)

elif view == "Portfolio":
    pass
elif view == "Cash Flow":
    pass
