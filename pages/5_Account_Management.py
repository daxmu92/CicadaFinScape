import sys
import streamlit as st
import pandas as pd
import re
import json

sys.path.append("..")
from context import FinContext
import fwidgets as fw
import finutils as fu

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

st.set_page_config(page_title="Account Management",)
st.title("Account Management")
st.divider()
st.subheader("Account Categories")


@st.experimental_dialog("Load Accounts config from json file")
def load_acc_config_from_json_dia():
    upload_file = st.file_uploader("Choose a json file")
    if upload_file is not None:
        config = json.load(upload_file)
        if st.button("Submit", key="load_config_from_json_submit", type="primary"):
            context.load_config(config)
            context.write_config()
            st.rerun()
        st.json(config, expanded=True)
    else:
        st.warning("You need to upload a config json file")


with st.sidebar:
    st.download_button("Download your accounts config",
                       data=context.config_json(),
                       file_name=f"cfs-accounts-config-{fu.cur_date()}.json",
                       mime="application/json",
                       use_container_width=True)
    if st.button("Upload your accounts config", key="side_bar_upload_config_buttong", use_container_width=True):
        load_acc_config_from_json_dia()
    if st.button("Add account", type="primary", key="acc_add_asset", use_container_width=True):
        fw.add_account()
    if st.button("Delete account", key="acc_delete_asset", use_container_width=True):
        fw.delete_account()

# category
cat_df = context.category_df()

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
    st.button("Submit", on_click=FinContext.category_from_df, args=(context, df), type="primary", key="acc_cat_df_submit", use_container_width=True)
with col2:
    if st.button("Reset", use_container_width=True):
        k_incre_all()
        st.rerun()

# Accounts
st.subheader("Accounts")
edit_on = st.toggle("Edit", key=st.session_state["acc_acc_toggle"])
if not edit_on:
    st.table(context.account_df())
else:
    col_config = {k: st.column_config.SelectboxColumn(k, options=v) for k, v in context.cat_dict.items()}
    account_df = context.account_df()
    col_config.update({col: st.column_config.TextColumn(col, disabled=True) for col in account_df.columns if col not in context.cat_dict})
    df = st.data_editor(account_df, hide_index=True, column_config=col_config, use_container_width=True)
    cols = st.columns(3)
    with cols[0]:
        st.button("Submit",
                  on_click=FinContext.account_from_df,
                  args=(context, df),
                  type="primary",
                  key="acc_acc_df_submit",
                  use_container_width=True)
