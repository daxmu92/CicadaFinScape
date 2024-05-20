from datetime import datetime
import pandas as pd


def cur_date():
    current_time = datetime.now()
    timestamp_string = current_time.strftime("%Y-%m-%d")
    return timestamp_string


def cur_year():
    current_time = datetime.now()
    year = int(current_time.strftime("%Y"))
    return year


def cur_month():
    current_time = datetime.now()
    month = int(current_time.strftime("%m"))
    return month


def norm_date(date):
    p = pd.Period(date, freq='M')
    return p.strftime("%Y-%m")
