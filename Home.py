import os
import pandas as pd
import streamlit as st
from streamlit_extras.grid import grid

from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu

st.set_page_config(page_title="Cicada Financial Scape", page_icon=":clipboard:", layout="wide")
curr_path = __file__
curr_dir = os.path.dirname(curr_path)
data_dir = os.path.join(curr_dir, "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir, mode=0o777, exist_ok=True)
    os.chmod(data_dir, 0o777)

config_path = os.path.join(data_dir, "config.json")
csv_path = os.path.join(data_dir, "data.csv")
db_path = os.path.join(data_dir, "test.db")

# Init context
context = FinContext(config_path, db_path)
st.session_state['context'] = context

st.title("Welcome to Cicada Financial Scape!")
st.divider()

if not context.validate():
    fw.init_db()
    st.stop()

fw.check_all()

cur_date = fu.norm_date(fu.cur_date())
date_list = fw.get_date_list()
g: st = grid([12, 1, 1])


def update_selected_date(previous):
    print(previous)
    if previous:
        prev = fu.prev_date(st.session_state["home_select_date_slider"])
        if prev in date_list:
            st.session_state["home_select_date_slider"] = prev
    else:
        next = fu.next_date(st.session_state["home_select_date_slider"])
        if next in date_list:
            st.session_state["home_select_date_slider"] = next


selected_date = g.select_slider("Select a Date", options=date_list, value=cur_date, label_visibility="collapsed", key="home_select_date_slider")
g.button("<", use_container_width=True, key="home_select_date_slider_previous_button", on_click=update_selected_date, args=(True,))
g.button("\>", use_container_width=True, key="home_select_date_slider_next_button", on_click=update_selected_date, args=(False,))

total_worth = context.query_total_worth(selected_date)
prev_date = fu.prev_date(selected_date)
previous_worth = context.query_total_worth(prev_date)
net_growth = total_worth - previous_worth
total_profit = context.query_total_profit(selected_date)

# col1, col2 = st.columns(2)
# with col1:
# st.write(f"### Total worth: :blue-background[{total_worth:,.1f}]")
#
# with col2:
# growth_color = ":green-background" if net_growth >= 0 else ":red-background"
# st.write(f"### Net growth: {growth_color}[{net_growth:,.1f}]")

col1, col2 = st.columns(2)
with col1:
    allocation_pie = context.allocation_pie(selected_date)
    st.plotly_chart(allocation_pie, theme="streamlit", use_container_width=True)
with col2:
    st.write("###  ")
    st.write("###  ")
    st.write("###  ")
    st.write(f"### DATE: :grey-background[{selected_date}]")
    st.write(f"### Total worth: :blue-background[{total_worth:,.1f}]")
    st.write(f"### Net growth: {fw.get_st_color_str_by_pos(net_growth)}[{net_growth:,.1f}]")
    st.write(f"### Profit: {fw.get_st_color_str_by_pos(total_profit)}[{total_profit:,.1f}]")

# overview_chart = context.overview_area_chart()
# st.plotly_chart(overview_chart, theme="streamlit", use_container_width=True)

cat_list = list(context.config.cat_dict.keys())
st.write("### Category distribution: ")
if not cat_list:
    st.info("You haven't specify any category")
else:
    tabs = st.tabs(cat_list)
    for i, tab in enumerate(tabs):
        with tab:
            category_pie = context.category_pie(cat_list[i])
            st.plotly_chart(category_pie, theme="streamlit", use_container_width=True)
