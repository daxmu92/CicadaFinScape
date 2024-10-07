from datetime import datetime
from typing import Sequence
import pandas as pd
import re


def cur_date() -> str:
    current_time = datetime.now()
    timestamp_string = current_time.strftime("%Y-%m-%d")
    return timestamp_string


def cur_year() -> int:
    current_time = datetime.now()
    year = int(current_time.strftime("%Y"))
    return year


def cur_month() -> int:
    current_time = datetime.now()
    month = int(current_time.strftime("%m"))
    return month


def norm_date(date: str) -> str:
    p = pd.Period(date, freq='M')
    return p.strftime("%Y-%m")


def digit_date(date: str) -> int:
    p = pd.Period(date, freq='M')
    return int(p.strftime("%Y%m"))


def prev_date(date: str) -> str:
    p = pd.Period(date, freq='M')
    p = p - 1
    return p.strftime("%Y-%m")


def next_date(date: str) -> str:
    p = pd.Period(date, freq='M')
    p = p + 1
    return p.strftime("%Y-%m")


def get_date(year: int, month: int) -> str:
    return pd.Period(year=year, month=month, freq="M").strftime("%Y-%m")


def date_list(start_date: str, end_date: str) -> list[str]:
    period_range = pd.period_range(start=start_date, end=end_date, freq='M')
    return [p.strftime("%Y-%m") for p in period_range]


def year_list(start_date: str, end_date: str) -> list[int]:
    period_range = pd.period_range(start=start_date, end=end_date, freq='Y')
    year_list = [int(p.strftime("%Y")) for p in period_range]
    return year_list


def round_df(df: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    return df.round({c: 1 for c in cols})


def format_dec_df(df: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    return df.style.format({c: "{:.1f}" for c in cols})


def incre_str(s: str) -> str:
    return re.sub(r'(?:(\d+))?$', lambda x: '_0' if x.group(1) is None else str(int(x.group(1)) + 1), s)


def norm_number(v, digits: int = 2):
    return round(v, digits)


def month_list() -> list[str]:
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def gen_txt_with_arrow(num: int):
    if num > 0:
        return f"▲ {num}"
    else:
        return f"▼ {num}"


def gen_txt_with_color_and_arrow(num: int):
    if num > 0:
        return f":red[▲ {num}]"
    else:
        return f":green[▼ {num}]"
