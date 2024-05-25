import streamlit as st
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from context import FinContext

class FinLogger:

    def error(s: str):
        print(s)
        e = RuntimeError(s)
        st.exception(e)

    def warn(s):
        print(s)
        st.warning(s)

    def expect(b, s=""):
        if not b:
            print(s)
            e = RuntimeError(s)
            st.exception(e)
