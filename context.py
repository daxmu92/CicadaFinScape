import json
import os
import copy
import csv
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from finsql import Account, AssetItem, FinSQL, ASSET_TABLE
from st_utils import FinLogger


class FinContext:

    def __init__(self, config_path, db_path):
        self.config_path = config_path
        self.db_path = db_path
        self.fsql = FinSQL(self.db_path)
        self.config: dict = {}
        self.cat_dict: dict[str, list[str]] = {}
        self.acc: dict[str, Account] = {}
        self.load_config_file(config_path)

    def validate_db(self):
        with self.fsql as s:
            return s.validate_db()

    def clear_config(self):
        self.config = {}
        self.cat_dict = {}
        self.acc = {}

    def load_config(self, config: dict):
        self.clear_config()
        self.config = config
        if "Categories" in self.config:
            self.cat_dict = self.config["Categories"]

        if "Accounts" in self.config:
            for i in self.config["Accounts"]:
                self.acc[i["Name"]] = Account(i["Name"])

        if "Assets" in self.config:
            for i in self.config["Assets"]:
                acc_name = i["Account"]
                if acc_name not in self.acc:
                    FinLogger.exception(f"Doesn't find account f{acc_name}")
                acc = self.acc[acc_name]
                asset = AssetItem(i["Name"], acc)
                acc.add_asset(asset)
                if "Category" in i:
                    for cat, type in i["Category"].items():
                        if cat not in self.cat_dict:
                            FinLogger.exception(f"Found category {cat} is not in category config {self.cat_dict}")
                            continue
                        if (type not in self.cat_dict[cat]) and (type is not None):
                            FinLogger.exception(f"Found type {type} is not in category {cat}")
                            continue
                        asset.add_cat(cat, type)

    def load_config_file(self, config_path):
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            self.load_config(config)
        else:
            config = {"Categories": [], "Accounts": [], "Assets": []}
            self.load_config(config)
            self.write_config()

    def config_dict(self):
        config = {}
        if self.cat_dict:
            config["Categories"] = self.cat_dict
        if self.acc:
            accs = [v.to_json() for k, v in self.acc.items()]
            config["Accounts"] = accs

        assets = []
        for k, v in self.acc.items():
            for asset in v.asset_list:
                assets.append(asset.to_json())
        if assets:
            config["Assets"] = assets
        return config

    def config_json(self):
        return json.dumps(self.config_dict(), indent=4)

    def write_config(self):
        config = self.config_dict()
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)

    def clean_up_cat(self):
        for k, v in self.acc.items():
            for sub in v.asset_list:
                sub.cats = {k: v for k, v in sub.cats.items() if k in self.cat_dict}

    def add_asset(self, acc_name, sub_name, cats: dict):
        if acc_name not in self.acc:
            self.acc[acc_name] = Account(acc_name)

        acc = self.acc[acc_name]
        asset = AssetItem(sub_name, acc)
        for k, v in cats.items():
            asset.add_cat(k, v)
        acc.add_asset(asset)
        self.write_config()

    def acc_name_list(self):
        acc_name_list = [v.name for k, v in self.acc.items()]
        return acc_name_list

    def subacc_name_list(self, acc_name):
        sub_name_list = [x.name for x in self.acc[acc_name].asset_list]
        return sub_name_list

    def init_db(self):
        with self.fsql as s:
            s.clear_db()
            s.initial_db()

    def load_from_csv(self, csv_path):
        with self.fsql as s:
            s.load_from_csv(csv_path)

    def init_db_from_csv(self, csv_path):
        self.init_db()
        self.load_from_csv(csv_path)

    def combine_acc_ass(df):
        df["SUBACCOUNT"] = df['ACCOUNT'] + '-' + df['SUBACCOUNT']
        return df

    def asset_df(self, acc_name, sub_name) -> pd.DataFrame:
        cols = ["DATE", "ACCOUNT", "SUBACCOUNT", "NET_WORTH", "INFLOW", "PROFIT"]
        with self.fsql as s:
            r = s.query_asset(acc_name, sub_name)
            df = pd.DataFrame(r, columns=cols)
        df["SUBACCOUNT"] = df['ACCOUNT'] + '-' + df['SUBACCOUNT']
        df = df[["DATE", "SUBACCOUNT", "NET_WORTH", "INFLOW", "PROFIT"]]
        return df

    def account_df(self):
        cols = ["Account", "Sub-account"]
        cols.extend([k for k in self.cat_dict])
        df = pd.DataFrame(columns=cols)
        for k, v in self.acc.items():
            v.add_to_df(df)
        return df

    def account_from_df(self, df: pd.DataFrame):
        for index, row in df.iterrows():
            acc_name = row["Account"]
            sub_name = row["Name"]
            if acc_name not in self.acc:
                self.acc[acc_name] = Account(acc_name)
            acc = self.acc[acc_name]

            asset = acc.asset(sub_name)
            if asset is None:
                asset = AssetItem(sub_name, acc)
                acc.add_asset(asset)

            for k, v in row.items():
                if k in self.cat_dict:
                    asset.add_cat(k, v)
        self.write_config()

    def add_account_from_df(self, df: pd.DataFrame):
        if df is None:
            return
        for index, row in df.iterrows():
            print(row)
            acc_name = row["ACCOUNT"]
            sub_name = row["SUBACCOUNT"]
            if acc_name not in self.acc:
                self.acc[acc_name] = Account(acc_name)
            acc = self.acc[acc_name]

            asset = acc.asset(sub_name)
            assert (asset is None)

            asset = AssetItem(sub_name, acc)
            acc.add_asset(asset)

            for k, v in row.items():
                if k in self.cat_dict:
                    asset.add_cat(k, v)
        self.write_config()

    def category_df(self):
        cat = [[k, ','.join(v)] for k, v in self.cat_dict.items()]
        cat_df = pd.DataFrame(cat, columns=["Category", "Labels"])
        return cat_df

    def category_from_df(self, df: pd.DataFrame):
        cat_dict = {}
        for index, row in df.iterrows():
            name: str = row["Category"]
            labels: str = row["Labels"]
            cat_dict[name] = labels.split(',')
        self.cat_dict = cat_dict
        self.write_config()
        self.clean_up_cat()

    def query_date(self, date, use_pre_if_not_exist) -> pd.DataFrame:
        if not use_pre_if_not_exist:
            with self.fsql as s:
                r = s.query_date(date)
                df = pd.DataFrame(r, columns=ASSET_TABLE.cols_name())
            return df

        df = pd.DataFrame(columns=ASSET_TABLE.cols_name())
        for acc in self.acc:
            for sub in self.acc[acc].asset_list:
                data = self.query_subacc_by_date(date, acc, sub.name, True)
                df = pd.concat([df, data])
        return df

    def query_total_value(self, date):
        return self.query_date(date, True)["NET_WORTH"].sum()

    def query_subacc_by_date(self, date, acc, sub, use_pre_if_not_exist) -> pd.DataFrame:
        with self.fsql as s:
            r = s.query_subacc_by_date(date, acc, sub)
            if len(r) > 0:
                df = pd.DataFrame(r, columns=ASSET_TABLE.cols_name())
                return df

        if use_pre_if_not_exist:
            return self.query_last_data(date, acc, sub)

        return pd.DataFrame([], columns=ASSET_TABLE.cols_name())

    def query_latest_data(self, acc_name, sub_name) -> pd.DataFrame:
        with self.fsql as f:
            r = f.query_asset(acc_name, sub_name)
            df = pd.DataFrame(r, columns=ASSET_TABLE.cols_name())
        row_id = df["DATE"].idxmax()
        row = df.iloc[[row_id]]
        return row

    def query_last_data(self, date, acc, sub) -> pd.DataFrame:
        with self.fsql as f:
            r = f.query_asset(acc, sub)
            df = pd.DataFrame(r, columns=ASSET_TABLE.cols_name())

        if df[df["DATE"] < date].empty:
            df = pd.DataFrame(columns=ASSET_TABLE.cols_name())
            return df

        closest_row = df.iloc[[df[df["DATE"] < date]["DATE"].idxmax()]]
        return closest_row

    def query_period_data(self, start_date, end_date, cols=ASSET_TABLE.cols_name()) -> pd.DataFrame:
        with self.fsql as s:
            r = s.query_period_all(start_date, end_date)
            df = pd.DataFrame(r, columns=cols)
        return df

    def query_period_data_by_acc_ass_list(self, start_date, end_date, acc_ass_list: list[tuple], cols=ASSET_TABLE.cols_name()) -> pd.DataFrame:
        with self.fsql as s:
            r = s.query_period(start_date, end_date, acc_ass_list)
            df = pd.DataFrame(r, columns=cols)
        return df

    def get_date_range(self) -> tuple[str, str]:
        with self.fsql as f:
            r = f.query_col(["DATE"])
            df = pd.DataFrame(r, columns=["DATE"])
        earliest = df["DATE"].min()
        latest = df["DATE"].max()
        return earliest, latest

    def get_latest_date(self):
        e, l = self.get_date_range()
        return l

    def get_earliest_date(self):
        e, l = self.get_date_range()
        return e

    def get_asset(self, acc_name, sub_name):
        if acc_name not in self.acc:
            return None
        acc = self.acc[acc_name]
        return acc.asset(sub_name)

    def has_asset(self, acc_name, sub_name):
        return self.get_asset(acc_name, sub_name) is not None

    def query_exist(self, date, acc, sub):
        with self.fsql as s:
            return s.query_data_exist(date, acc, sub)

    def insert_asset(self, date, acc_name, sub_name, networth, invest, profit):
        insert_data = {x.name: y for x, y in zip(ASSET_TABLE.ess_cols(), [date, acc_name, sub_name, networth, invest, profit])}
        with self.fsql as s:
            s.insert_asset(insert_data)
            s.commit()

    def insert_or_update(self, date, acc, sub, net, inflow, profit):
        if self.query_exist(date, acc, sub):
            self.update_data(date, acc, sub, net, inflow, profit)
        else:
            self.insert_asset(date, acc, sub, net, inflow, profit)

    def delete_data(self, date, acc_name, sub_name):
        filter = {"DATE": date, "ACCOUNT": acc_name, "SUBACCOUNT": sub_name}
        with self.fsql as s:
            s.delete_data(filter)
            s.commit()

    def update_data(self, date, acc_name, sub_name, networth, invest, profit):
        filter = {"DATE": date, "ACCOUNT": acc_name, "SUBACCOUNT": sub_name}
        update_data = {"NET_WORTH": networth, "INFLOW": invest, "PROFIT": profit}
        with self.fsql as s:
            s.update_data(filter, update_data)
            s.commit()

    def delete_asset(self, acc_name, sub_name):
        with self.fsql as s:
            s.delete_asset(acc_name, sub_name)

        if acc_name not in self.acc:
            return
        acc = self.acc[acc_name]
        acc.asset_list = [x for x in acc.asset_list if x.name != sub_name]
        self.write_config()

    def load_from_df(self, df: pd.DataFrame):
        print(df.columns.to_list())
        print(ASSET_TABLE.cols_name())
        assert (df.columns.to_list() == ASSET_TABLE.cols_name())
        for index, row in df.iterrows():
            print(row.to_list())
            self.insert_asset(*row.to_list())

    def get_all_data_csv(self):
        cols = ASSET_TABLE.cols_name()
        with self.fsql as s:
            r = s.query_all_asset()
            df = pd.DataFrame(r, columns=cols)
        return df.to_csv(index=False).encode("utf-8")

    def asset_table(self):
        cols = ASSET_TABLE.cols_name()
        with self.fsql as s:
            r = s.query_all_asset()
            df = pd.DataFrame(r, columns=cols)

        df["SUBACCOUNT"] = df['ACCOUNT'] + '-' + df['SUBACCOUNT']
        df = df[["DATE", "ACCOUNT", "SUBACCOUNT", "NET_WORTH"]]
        return df

    def overview_chart(self):
        df = self.asset_table()
        df_sum = df.copy()
        df_sum = df_sum.groupby("DATE")["NET_WORTH"].sum().reset_index()
        df_sum.rename(columns={"NET_WORTH": "TOTAL_NET_WORTH"}, inplace=True)
        fig = px.line(df, x='DATE', y='NET_WORTH', color="SUBACCOUNT")
        # TODO - add secondary y
        # fig = go.Figure(fig)
        # fig.add_trace(
        #     go.Bar(x=df_sum["DATE"], y=df_sum["TOTAL_NET_WORTH"], name="TOTAL"),
        #     secondary_y=True
        # )
        # fig.update_layout(title_text="Wealth Overview")
        # fig.update_yaxes(title_text="<b>primary</b> Per Asset Net Worth", secondary_y=False)
        # fig.update_yaxes(title_text="<b>secondary</b> Total Net Worth", secondary_y=True)
        fig.add_bar(x=df_sum["DATE"], y=df_sum["TOTAL_NET_WORTH"], name="TOTAL")
        return fig

    def overview_area_chart(self):
        df = self.asset_table()
        fig = px.area(df, x="DATE", y="NET_WORTH", color="ACCOUNT", line_group="SUBACCOUNT")
        return fig

    def allocation_pie(self, date=None):
        date = self.get_latest_date() if date is None else date
        df = self.query_date(date, True)
        df = FinContext.combine_acc_ass(df)
        fig = px.pie(df, values="NET_WORTH", names="SUBACCOUNT", title=f"{date} Account Allocation")
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
        if cat not in self.cat_dict:
            FinLogger.exception(f"{cat} is not in category config")

        # remove invalid data
        print(df)
        df = df[df.apply(is_valid_data, axis=1)]
        print(df)

        # assign categories
        df[cat] = df.apply(assign_cat, axis=1)

        # generate chart
        df_sum = df.groupby(cat)["NET_WORTH"].sum().reset_index()
        fig = px.pie(df_sum, values="NET_WORTH", names=cat, title=f"{date} CATEGORY {cat} Distribution")
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
        config_path = os.path.join(curr_dir, "sample_config.json")
        self.load_config_file(config_path)
        self.write_config()

        with self.fsql as s:
            s.clear_db()
            s.initial_db()

        period_range = pd.period_range(start="3/1/2020", end="2/1/2024", freq='M')
        with self.fsql as s:
            seed = 0
            for k, v in self.acc.items():
                for sub in v.asset_list:
                    r = sub.cats["Risk"] if "Risk" in sub.cats else "Low"
                    data: list[list] = generate_data(period_range, r, seed)
                    seed += 1
                    for i in data:
                        d = list(i)
                        d.insert(1, sub.name)
                        d.insert(1, v.name)
                        insert_data = {x.name: y for x, y in zip(ASSET_TABLE.ess_cols(), d)}
                        s.insert_asset(insert_data)
            s.commit()
