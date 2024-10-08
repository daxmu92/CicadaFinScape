import sys
import streamlit as st
import pandas as pd
import re

sys.path.append("..")
from src.context import FinContext
import src.fwidgets as fw
import src.finutils as fu

context: FinContext = st.session_state['context']

keys = ["acc_cat_df_key", "acc_acc_toggle", "acc_new_acc_toggle"]


def incre_str(s):
    return re.sub(r'(?:(\d+))?$', lambda x: '_0' if x.group(1) is None else str(int(x.group(1)) + 1), s)


def s_incre(s):
    st.session_state[s] = incre_str(st.session_state[s])


def k_incre_all():
    for key in keys:
        s_incre(key)


def k_init_all():
    for key in keys:
        if key not in st.session_state:
            st.session_state[key] = f"{key}_0"


k_init_all()

st.set_page_config(page_title="Account Overview",)
st.title("Account Overview")
st.divider()

# Accounts
st.subheader("Accounts overview")
edit_on = st.toggle("Edit Category", key=st.session_state["acc_acc_toggle"])
if not edit_on:
    st.table(context.config.account_df())
else:
    col_config = {k: st.column_config.SelectboxColumn(k, options=v) for k, v in context.config.cat_dict.items()}
    account_df = context.config.account_df()
    col_config.update({col: st.column_config.TextColumn(col, disabled=True) for col in account_df.columns if col not in context.config.cat_dict})
    df = st.data_editor(account_df, hide_index=True, column_config=col_config, use_container_width=True)
    cols = st.columns(3)
    with cols[0]:
        st.button("Submit",
                  on_click=context.config.account_from_df,
                  args=(context, df),
                  type="primary",
                  key="acc_acc_df_submit",
                  use_container_width=True)

# category
st.subheader("Account Categories")
cat_df = context.config.category_df()

# TODO - use list editor
col_config = {col: st.column_config.TextColumn(col, required=True) for col in cat_df.columns}
df = st.data_editor(cat_df,
                    hide_index=True,
                    num_rows="dynamic",
                    column_config=col_config,
                    key=st.session_state['acc_cat_df_key'],
                    use_container_width=True)
col1, col2 = st.columns(2)
with col1:
    if st.button("Submit", type="primary", key="acc_cat_df_submit", use_container_width=True):
        context.config.category_from_df(df)
with col2:
    if st.button("Reset", use_container_width=True):
        k_incre_all()
        st.rerun()
