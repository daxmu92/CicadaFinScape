import sys
import streamlit as st
import pandas as pd
import re
sys.path.append("..")
from context import FinContext
context:FinContext = st.session_state['context']

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

st.set_page_config(
    page_title="Account Management",
)
st.sidebar.header("Account Management")
st.header("Account Management")
st.subheader("Account Categories")

# category
cat_df = context.category_df()

# TODO - use list editor
df = st.data_editor(
    cat_df,
    hide_index=True,
    num_rows="dynamic",
    key = st.session_state['acc_cat_df_key']
)
col1, col2= st.columns([2,11])
with col1:
    st.button("Submit", on_click=FinContext.category_from_df, args=(context, df), type="primary", key="acc_cat_df_submit")
with col2:
    if st.button("Reset"):
        k_incre_all()
        st.rerun()

@st.experimental_dialog("New asset")
def add_asset():
    context:FinContext = st.session_state['context']
    edit_on = st.toggle("New Account", key = st.session_state["acc_new_acc_toggle"])
    acc_name = ""
    if not edit_on:
        acc_name = st.selectbox("Select Account", [v.name for k,v in context.acc.items()])
    else:
        acc_name = st.text_input("New Account")
    
    asset_name = st.text_input("New Asset")

    cats = {}
    for k,v in context.cat_dict.items():
        cats[k] = st.selectbox(f"Category {k}:", v)
    
    if st.button("Submit", on_click=FinContext.add_asset, args=(context, acc_name, asset_name, cats), type="primary", key="acc_new_acc_submit"):
        st.rerun()
    
# Accounts
st.subheader("Accounts")
edit_on = st.toggle("Edit", key = st.session_state["acc_acc_toggle"])
if not edit_on:
    st.table(context.account_df())
    if st.button("Add asset", type="primary", key="acc_add_asset"):
        add_asset()
else:
    col_config = {k : st.column_config.SelectboxColumn(k, options=v) for k,v in context.cat_dict.items()}
    account_df = context.account_df()
    col_config.update({col: st.column_config.TextColumn(col, disabled=True) for col in account_df.columns if col not in context.cat_dict})
    df = st.data_editor (
        account_df,
        hide_index=True,
        column_config=col_config
    )
    st.button("Submit", on_click=FinContext.account_from_df, args=(context, df), type="primary", key="acc_acc_df_submit")