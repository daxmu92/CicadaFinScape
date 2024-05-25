import streamlit as st
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from context import FinContext

class FinLogger:

    def exception(s: str):
        print(s)
        e = RuntimeError(s)
        st.exception(e)

    def should_not_reach_here():
        return FinLogger.error("Should not reach here, report a issue: https://github.com/daxmu92/CicadaFinScape")

    def error(s):
        print(s)
        return st.error(s)

    def warn(s):
        print(s)
        return st.warning(s)

    def expect(b, s=""):
        if not b:
            print(s)
            e = RuntimeError(s)
            return st.exception(e)
