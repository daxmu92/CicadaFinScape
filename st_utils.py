import streamlit as st
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from context import FinContext

class FinWidgets:
    def account_select(context:'FinContext', key = ""):
        return st.selectbox("Select Account", [v.name for k,v in context.acc.items()])

class FinLogger:
    def error(s:str):
        e = RuntimeError(s)
        st.exception(e)
    def warn(s):
        st.warning(s)
        