import streamlit as st
from context import FinContext


@st.experimental_dialog("New asset")
def add_asset():
    context: FinContext = st.session_state['context']
    edit_on = st.toggle("New Account", key=st.session_state["acc_new_acc_toggle"])
    acc_name = ""
    if not edit_on:
        acc_name = st.selectbox("Select Account", [v.name for k, v in context.acc.items()])
    else:
        acc_name = st.text_input("New Account")

    asset_name = st.text_input("New Asset")

    cats = {}
    for k, v in context.cat_dict.items():
        cats[k] = st.selectbox(f"Category {k}:", v)

    if st.button("Submit", on_click=FinContext.add_asset, args=(context, acc_name, asset_name, cats), type="primary", key="acc_new_acc_submit"):
        st.rerun()
