import json
import os
import io
import zipfile
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

from src.findata import *
from src.findatasql import *
import src.finutils as fu
from src.st_utils import FinLogger
from src.finconfig import AssetItem, FinConfig


class FinContext:

    def __init__(self, config_path: str, db_path: str):
        self.config = FinConfig(config_path)
        self.data = FinDataContext(db_path)

    def validate(self):
        return self.data.validate()

    def init_db(self):
        self.data.clear_db()
        self.data.init_db()

    def reset_asset(self):
        self.data.reset_asset_table()

    def reset_tran(self):
        self.data.reset_tran_table()

    def combine_acc_ass(df: pd.DataFrame) -> pd.DataFrame:
        df["SUBACCOUNT"] = df['ACCOUNT'] + '-' + df['SUBACCOUNT']
        return df

    def query_asset(self, date: str = "", acc: str = "", sub: str = "") -> pd.DataFrame:
        return self.data.query_asset(date, acc, sub)

    def query_asset_info(self) -> pd.DataFrame:
        return self.data.query_asset_info()

    def query_tran_info(self) -> pd.DataFrame:
        return self.data.query_tran_info()

    def query_subacc_by_date(self, date: str, acc: str, sub: str, use_pre_net_if_not_exist: bool = True) -> pd.DataFrame:
        df: pd.DataFrame = self.data.query_asset(date, acc, sub)
        if not df.empty:
            return df

        if use_pre_net_if_not_exist:
            df = self.data.query_last_asset(date, acc, sub)
            df.loc[df["DATE"] != date, "PROFIT"] = 0
        return df

    def query_date(self, date: str, use_pre_net_if_not_exist: bool = True) -> pd.DataFrame:
        if not use_pre_net_if_not_exist:
            return self.data.query_asset(date)

        df = pd.DataFrame(columns=self.data.get_asset_cols_name())
        for acc in self.config.acc:
            for sub in self.config.acc[acc].sub_name_list():
                data = self.query_subacc_by_date(date, acc, sub, use_pre_net_if_not_exist)
                df = pd.concat([df, data])
        return df

    def query_total_worth(self, date: str) -> float:
        return self.query_date(date, True)["NET_WORTH"].sum()

    def query_total_profit(self, date: str) -> float:
        return self.query_date(date, True)["PROFIT"].sum()

    def query_total_inflow(self, date: str) -> float:
        return self.query_date(date, True)["INFLOW"].sum()

    def query_last_asset(self, date: str, acc: str, sub: str) -> pd.DataFrame:
        return self.data.query_last_asset(date, acc, sub)

    def query_period_data(self, start_date: str, end_date: str, fill_missing: bool = False) -> pd.DataFrame:
        if not fill_missing:
            return self.data.query_period_asset(start_date, end_date)

        def fill_missing_date(df: pd.DataFrame):
            # fill missing date, fill missing "NET_WORTH" with previous's "NET_WORTH"
            # fill missing profit and inflow with 0
            s, e = self.get_date_range()
            date_range = fu.date_list(s, e)
            df = df.set_index('DATE')
            df = df.reindex(date_range)
            df['NET_WORTH'] = df['NET_WORTH'].ffill()
            df['ACCOUNT'] = df['ACCOUNT'].ffill()
            df['SUBACCOUNT'] = df['SUBACCOUNT'].ffill()
            df['PROFIT'] = df['PROFIT'].fillna(0)
            df['INFLOW'] = df['INFLOW'].fillna(0)
            df = df.reset_index().rename(columns={'index': 'DATE'})
            return df

        df_list = []
        for acc in self.config.acc:
            for sub in self.config.acc[acc].sub_name_list():
                sub_df = self.data.query_asset(acc=acc, sub=sub)
                sub_df = fill_missing_date(sub_df)
                df_list.append(sub_df)
        df = pd.concat(df_list)
        df = df[df["DATE"].between(start_date, end_date)]
        return df

    def query_period_tran(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.data.query_period_tran(start_date, end_date)

    def get_date_range(self) -> tuple[str, str]:
        return self.data.query_date_range()

    def get_latest_date(self) -> str:
        _, l = self.get_date_range()
        return l

    def get_earliest_date(self) -> str:
        e, _ = self.get_date_range()
        return e

    def get_asset(self, acc_name: str, sub_name: str) -> AssetItem:
        return self.config.get_asset(acc_name, sub_name)

    def has_asset(self, acc_name: str, sub_name: str) -> bool:
        return self.get_asset(acc_name, sub_name) is not None

    def insert_asset(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float):
        self.data.insert_or_update_asset(date, acc, sub, net, inflow, profit)

    def insert_or_update_asset(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float):
        self.data.insert_or_update_asset(date, acc, sub, net, inflow, profit)

    def delete_asset_data(self, date: str, acc_name: str, sub_name: str):
        self.data.delete_asset_data(date, acc_name, sub_name)

    def update_asset_data(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float):
        self.data.update_asset(date, acc, sub, net, inflow, profit)

    def delete_asset(self, acc_name: str, sub_name: str):
        self.data.delete_asset(acc_name, sub_name)
        self.config.delete_asset(acc_name, sub_name)

    def verify_asset_df(self, df: pd.DataFrame) -> tuple[bool, str]:
        asset_cols = self.data.get_asset_cols_name()
        if df.columns.to_list() != asset_cols:
            col_str = ", ".join(asset_cols)
            return False, f"Your data format doesn't match requirment, required columns: [{col_str}]"
        return True, ""

    def insert_tran(self, date, type, value, cat, note):
        self.data.insert_tran(date, type, value, cat, note)

    def delete_tran(self, id):
        self.data.delete_tran(id)

    def query_tran(self, date: str = "", type: str = "", cat: str = "") -> pd.DataFrame:
        return self.data.query_tran(date, type, cat)

    def get_tran_tags(self) -> list[str]:
        return self.data.get_tran_tags()

    def reindex_tran_id(self):
        self.data.reindex_tran_id()

    def df_to_tran(self, df: pd.DataFrame, append: bool = False):
        self.data.df_to_tran(df, append)

    def df_to_asset(self, df: pd.DataFrame, append: bool = False):
        self.data.df_to_asset(df, append)

    def income_outlay_df(self) -> pd.DataFrame:
        asset_df = self.data.query_asset()
        inflow_df = asset_df[["DATE", "INFLOW"]]
        inflow_df = inflow_df.groupby("DATE").sum().reset_index()
        tran_df = self.query_tran()
        income_df = tran_df[tran_df["TYPE"] == "INCOME"].groupby("DATE").sum().reset_index()
        income_df = income_df[["DATE", "VALUE"]]
        io_df = pd.merge(inflow_df, income_df, on="DATE", how="left")
        io_df["INCOME"] = io_df["VALUE"].fillna(0)
        io_df["OUTLAY"] = io_df["INCOME"] - io_df["INFLOW"]
        return io_df[["DATE", "INFLOW", "INCOME", "OUTLAY"]]

    def get_asset_data(self):
        return self.data.query_asset().to_csv(index=False).encode("utf-8")

    def get_tran_data(self):
        return self.data.query_tran().to_csv(index=False).encode("utf-8")

    def get_zip_data(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip:
            asset_buffer = io.BytesIO(self.get_asset_data())
            zip.writestr("asset.txt", asset_buffer.getvalue())
            tran_buffer = io.BytesIO(self.get_tran_data())
            zip.writestr("flow.txt", tran_buffer.getvalue())
            zip.writestr("config.json", self.config.to_json())
        return zip_buffer.getvalue()

    def load_from_zip_data(self, file):
        with zipfile.ZipFile(file, "r") as z:
            files = z.namelist()
            assert "asset.txt" in files and "flow.txt" in files and "config.json" in files

            with z.open("config.json") as config:
                self.config.load_from_dict(json.load(config))
                self.config.write_config()

            with z.open("asset.txt") as asset_file:
                data_df = pd.read_csv(asset_file)
                valid, err_msg = self.verify_asset_df(data_df)
                FinLogger.expect_and_stop(valid, err_msg)
                self.data.df_to_asset(data_df)

            with z.open("flow.txt") as flow_file:
                flow_df = pd.read_csv(flow_file)
                self.data.df_to_tran(flow_df)

    def asset_table(self):
        return self.data.query_asset()

    def overview_chart(self):
        df = self.asset_table()
        df_sum = df.copy()
        df_sum = df_sum.groupby("DATE")["NET_WORTH"].sum().reset_index()
        df_sum.rename(columns={"NET_WORTH": "TOTAL_NET_WORTH"}, inplace=True)
        fig = px.line(df, x='DATE', y='NET_WORTH', color="SUBACCOUNT")
        fig.add_bar(x=df_sum["DATE"], y=df_sum["TOTAL_NET_WORTH"], name="TOTAL")
        return fig

    def overview_area_chart(self):
        df = self.asset_table()
        fig = px.area(df, x="DATE", y="NET_WORTH", color="ACCOUNT", line_group="SUBACCOUNT")
        return fig

    def category_pie(self, cat: str, date: str = None):

        def is_valid_data(row):
            acc_name = row["ACCOUNT"]
            sub_name = row["SUBACCOUNT"]
            return self.has_asset(acc_name, sub_name)

        def assign_cat(row):
            acc_name = row["ACCOUNT"]
            sub_name = row["SUBACCOUNT"]
            asset: AssetItem = self.get_asset(acc_name, sub_name)
            return asset.cats.get(cat)

        # get the latest data
        date = self.get_latest_date() if date is None else date
        df = self.query_date(date, True)
        if cat not in self.config.cat_dict:
            FinLogger.exception(f"{cat} is not in category config")

        # remove invalid data
        df = df[df.apply(is_valid_data, axis=1)]

        # assign categories
        df[cat] = df.apply(assign_cat, axis=1)

        # generate chart
        df_sum = df.groupby(cat)["NET_WORTH"].sum().reset_index()

        # fig = px.pie(df_sum, values="NET_WORTH", names=cat, title=f"{date} CATEGORY {cat} Distribution")
        fig = go.Figure(go.Pie(labels=df_sum[cat], values=df_sum["NET_WORTH"], textinfo='label+value+percent', showlegend=False))
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        return fig

    def profit_waterfall(self, start_date, end_date):
        df = self.query_period_data(start_date, end_date)
        df_sum = df.groupby("DATE")["PROFIT"].sum().reset_index()

        layout = {
            "xaxis": {
                "rangeselector": {
                    "buttons": [
                        {
                            "count": 1,
                            "label": "1m",
                            "step": "month",
                            "stepmode": "backward",
                        },
                        {
                            "count": 6,
                            "label": "6m",
                            "step": "month",
                            "stepmode": "backward",
                        },
                        {
                            "count": 1,
                            "label": "YTD",
                            "step": "year",
                            "stepmode": "todate",
                        },
                        {
                            "count": 1,
                            "label": "1y",
                            "step": "year",
                            "stepmode": "backward",
                        },
                        {
                            "count": 3,
                            "label": "3y",
                            "step": "year",
                            "stepmode": "backward",
                        },
                        {
                            "step": "all"
                        },
                    ]
                },
                "rangeslider": {
                    "visible": True
                }
            },
            "yaxis": {
                "fixedrange": False,
                "autorange": True,
            },
        }
        fig = go.Figure(go.Waterfall(
            x=df_sum["DATE"],
            y=df_sum["PROFIT"],
        ), layout=layout)
        return fig

    def profit_calendar(self):
        # TODO https://calendar-component.streamlit.app/
        pass
        #df = self.query_period_data(start_date, end_date)
        #df_sum = df.groupby("DATE")["PROFIT"].sum().reset_index()

    def initialize_with_sample_data(self):

        def generate_data(range: list[pd.Period], risk, seed):
            np.random.seed(seed)
            init_value = np.random.uniform(5000, 100000)
            invest_low = np.random.uniform(200, 3000)
            invest_high = np.random.uniform(invest_low, invest_low * 5)
            invest_list = np.random.uniform(invest_low, invest_high, len(range - 1))

            profit_percent_limit = np.random.uniform(0.2, 0.8)
            profit_percent_list = np.random.uniform(-profit_percent_limit, profit_percent_limit, len(range - 1))

            last_value = (range[0].strftime("%Y-%m"), init_value, 0, 0)
            r = [last_value]
            for i, p in enumerate(range[1:]):
                profit = last_value[1] * profit_percent_list[i]
                invest = invest_list[i]
                net_worth = last_value[1] + invest + profit
                last_value = (p.strftime("%Y-%m"), net_worth, invest, profit)
                r.append(last_value)
            return r

        curr_path = __file__
        curr_dir = os.path.dirname(curr_path)
        root_dir = str(Path(curr_dir).parent)
        sample_path = ["samples", "sample_config.json"]
        config_path = os.path.join(root_dir, *sample_path)
        self.config.load_config_file(config_path)
        self.config.write_config()

        self.data.clear_db()
        self.data.init_db()

        start = fu.norm_date("2020-3")
        end = max(fu.norm_date(fu.cur_date()), fu.norm_date("2024-2"))
        period_range = pd.period_range(start=start, end=end, freq='M')

        data_list = []
        seed = 0
        for _, acc in self.config.acc.items():
            for _, sub in acc.assets.items():
                r = sub.cats["Risk"] if "Risk" in sub.cats else "Low"
                data: list[list] = generate_data(period_range, r, seed)
                seed += 1
                for i in data:
                    d = list(i)
                    d.insert(1, sub.name)
                    d.insert(1, acc.name)
                    data_list.append(d)
        self.data.df_to_asset(pd.DataFrame(data_list))
