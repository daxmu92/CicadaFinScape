import json
import os
import copy
import csv
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from finsql import Account,AssetItem,FinSQL,ASSET_TABLE
from st_utils import FinLogger


class FinContext:
    def __init__(self, config_path, db_path):
        self.config_path = config_path
        self.db_path = db_path
        self.fsql = FinSQL(self.db_path)
        self.config:dict = {}
        self.cat_dict:dict[str, list[str]] = {}
        self.acc:dict[str,Account] = {}
        self.load_config_file(config_path)
    
    def validate_db(self):
        with self.fsql as s:
            return s.validate_db()
        
    
    def clear_config(self):
        self.config.clear()
        self.cat_dict.clear()
        self.acc.clear()

    def load_config(self, config:dict):
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
                    FinLogger.error(f"Doesn't find account f{acc_name}")
                acc = self.acc[acc_name]
                asset = AssetItem(i["Name"], acc)
                acc.add_asset(asset)
                if "Category" in i:
                    for cat,type in i["Category"].items():
                        if cat not in self.cat_dict:
                            FinLogger.error(f"Found category {cat} is not in category config {self.cat_dict}")
                            continue
                        if (type not in self.cat_dict[cat]) and (type is not None):
                            FinLogger.error(f"Found type {type} is not in category {cat}")
                            continue
                        asset.add_cat(cat,type)

    def load_config_file(self, config_path):
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            self.load_config(config)
        else:
            config = {
                "Categories" : [],
                "Accounts" : [],
                "Assets": []
            }
            self.load_config(config)
            self.write_config()
    
    def write_config(self):
        config = {}
        if self.cat_dict:
            config["Categories"] = self.cat_dict
        if self.acc:
            accs = [v.to_json() for k,v in self.acc.items()]
            config["Accounts"] = accs
        
        assets = []
        for k,v in self.acc.items():
            for asset in v.asset_list:
                assets.append(asset.to_json())
        if assets:
            config["Assets"] = assets
            
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)

    def clean_up_cat(self):
        for k,v in self.acc.items():
            for ass in v.asset_list:
                ass.cats = {k:v for k,v in ass.cats.items() if k in self.cat_dict}
    
    def add_asset(self, acc_name, asset_name, cats:dict):
        if acc_name not in self.acc:
            self.acc[acc_name] = Account(acc_name)
        
        acc = self.acc[acc_name]
        asset = AssetItem(asset_name, acc)
        for k,v in cats.items():
            asset.add_cat(k,v)
        acc.add_asset(asset)
        self.write_config()
    
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
        df["ASSET"] = df['ACCOUNT'] + '-' + df['NAME']
        return df

    def asset_df(self, acc_name, asset_name):
        cols = ["DATE", "ACCOUNT", "NAME", "NET_WORTH", "MONTH_INVEST", "MONTH_PROFIT"]
        with self.fsql as s:
            r = s.query_asset(acc_name, asset_name)
            df = pd.DataFrame(r, columns=cols)
        df["ASSET"] = df['ACCOUNT'] + '-' + df['NAME']
        df = df[["DATE", "ASSET", "NET_WORTH", "MONTH_INVEST", "MONTH_PROFIT"]]
        return df

    def account_df(self):
        cols = ["Account", "Name"]
        cols.extend([k for k in self.cat_dict])
        df = pd.DataFrame(columns=cols)
        for k,v in self.acc.items():
            v.add_to_df(df)
        return df

    def account_from_df(self, df:pd.DataFrame):
        for index, row in df.iterrows():
            acc_name = row["Account"]
            asset_name = row["Name"]
            if acc_name not in self.acc:
                self.acc[acc_name] = Account(acc_name)
            acc = self.acc[acc_name]
            
            asset = acc.asset(asset_name)
            if asset is None:
                asset = AssetItem(asset_name, acc)
                acc.add_asset(asset)
            
            for k,v in row.items():
                if k in self.cat_dict:
                    asset.add_cat(k, v)
        self.write_config()
    
    def category_df(self):
        cat = [[k, ','.join(v)] for k,v in self.cat_dict.items()]
        cat_df = pd.DataFrame(cat, columns=["Category", "Labels"])
        return cat_df
    
    def category_from_df(self, df:pd.DataFrame):
        cat_dict = {}
        for index, row in df.iterrows():
            name:str = row["Category"]
            labels:str = row["Labels"]
            cat_dict[name] = labels.split(',')
        self.cat_dict = cat_dict
        self.write_config()
        self.clean_up_cat()
    
    def query_date(self, date):
        with self.fsql as s:
            r = s.query_date(date)
            df = pd.DataFrame(r, columns=ASSET_TABLE.cols_name())
        return df

    def query_latest_data(self, acc_name, ass_name):
        with self.fsql as f:
            r = f.query_asset(acc_name, ass_name)
            df = pd.DataFrame(r, columns=ASSET_TABLE.cols_name())
        row_id = df["DATE"].idxmax()
        row = df.iloc[row_id]
        return row
    
    def query_last_data(self, acc_name, ass_name, date):
        with self.fsql as f:
            r = f.query_asset(acc_name, ass_name)
            df = pd.DataFrame(r, columns=ASSET_TABLE.cols_name())

        closest_row = df.iloc[df[df["DATE"] < date]["DATE"].idxmax()]
        return closest_row
    
    def get_latest_date(self):
        with self.fsql as f:
            r = f.query_col(["DATE"])
            df = pd.DataFrame(r, columns=["DATE"])
        latest = df["DATE"].max()
        return latest

    def get_asset(self, acc_name, asset_name):
        if acc_name not in self.acc:
            return None
        acc = self.acc[acc_name]
        return acc.asset(asset_name)

    def has_asset(self, acc_name, asset_name):
        return self.get_asset(acc_name, asset_name) is not None

    def insert_asset(self, date, acc_name, ass_name, networth, invest, profit):
        insert_data = {x.name:y for x,y in zip(ASSET_TABLE.ess_cols(), [date, acc_name, ass_name, networth, invest, profit])}
        with self.fsql as s:
            s.insert_asset(insert_data)
            s.commit()
    
    def delete_asset(self, acc_name, asset_name):
        with self.fsql as s:
            s.delete_asset(acc_name, asset_name)

        if acc_name not in self.acc:
            return
        acc = self.acc[acc_name]
        acc.asset_list = [x for x in acc.asset_list if x.name != asset_name]
        self.write_config()
    
    def load_from_df(self, df:pd.DataFrame):
        print(df.columns.to_list())
        print(ASSET_TABLE.cols_name())
        assert(df.columns.to_list() == ASSET_TABLE.cols_name())
        for index, row in df.iterrows():
            print(row.to_list())
            self.insert_asset(*row.to_list())
    
    def asset_table(self):
        #cols = ["DATE", "ACCOUNT", "NAME", "NET_WORTH", "MONTH_INVEST", "MONTH_PROFIT"]
        cols = ASSET_TABLE.cols_name()
        with self.fsql as s:
            r = s.query_all_asset()
            df = pd.DataFrame(r, columns=cols)

        df["ASSET"] = df['ACCOUNT'] + '-' + df['NAME']
        df = df[["DATE", "ASSET", "NET_WORTH"]]
        return df
    
    def overview_chart(self):
        df = self.asset_table()
        df_sum = df.copy()
        df_sum = df_sum.groupby("DATE")["NET_WORTH"].sum().reset_index()
        df_sum.rename(columns={"NET_WORTH": "TOTAL_NET_WORTH"}, inplace=True)
        fig = px.line(df, x='DATE', y='NET_WORTH', color="ASSET")
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

    def allocation_pie(self, date = None):
        date = self.get_latest_date() if date is None else date
        df = self.query_date(date)
        df = FinContext.combine_acc_ass(df)
        fig = px.pie(df, values="NET_WORTH", names="ASSET", title=f"{date} Asset Allocation")
        return fig
    
    def category_pie(self, cat:str, date:str = None):
        def is_valid_data(row):
            acc_name = row["ACCOUNT"]
            ass_name = row["NAME"]
            return self.has_asset(acc_name, ass_name)
        
        def assign_cat(row):
            acc_name = row["ACCOUNT"]
            ass_name = row["NAME"]
            asset:AssetItem = self.get_asset(acc_name, ass_name)
            return asset.cats.get(cat)

        # get the latest data
        date = self.get_latest_date() if date is None else date
        df = self.query_date(date)
        if cat not in self.cat_dict:
            FinLogger.error(f"{cat} is not in category config")

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
    
    def initialize_with_sample_data(self):
        def generate_data(range:list[pd.Period], risk, seed):
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
        
        period_range = pd.period_range(start = "3/1/2020", end = "2/1/2024", freq='M')
        with self.fsql as s:
            seed = 0
            for k,v in self.acc.items():
                for ass in v.asset_list:
                    r = ass.cats["Risk"] if "Risk" in ass.cats else "Low"
                    data:list[list] = generate_data(period_range, r, seed)
                    seed += 1
                    for i in data:
                        d = list(i)
                        d.insert(1, ass.name)
                        d.insert(1, v.name)
                        insert_data = {x.name:y for x,y in zip(ASSET_TABLE.ess_cols(), d)}
                        s.insert_asset(insert_data)
            s.commit()
    
                        
