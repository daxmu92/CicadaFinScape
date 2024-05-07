import json
import csv
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from finsql import Account,AssetItem,FinSQL,ASSET_TABLE

class FinContext:
    def __init__(self, config_path, db_path):
        self.config_path = config_path
        self.db_path = db_path
        with open(config_path) as f:
            self.config = json.load(f)
        self.cats:dict = {}
        self.acc:dict[str,Account] = {}
        self.fsql = FinSQL(self.db_path)

        print(self.config)

        if "Categories" in self.config:
            self.cats = self.config["Categories"]
        
        if "Accounts" in self.config:
            for i in self.config["Accounts"]:
                self.acc[i["name"]] = Account(i["name"])
        
        if "Assets" in self.config:
            for i in self.config["Assets"]:
                acc_name = i["account"]
                assert(acc_name in self.acc)
                acc = self.acc[acc_name]
                asset = AssetItem(i["name"], acc)
                if "Category" in i:
                    for cat,type in i["Category"].items():
                        assert(cat in self.cats and type in self.cats[cat])
                        asset.add_cat(cat,type)
                acc.add_asset(asset)
    
    def write_config(self):
        config = {}
        if self.cats:
            config["Categories"] = self.cats
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
            json.dump(config, f)
    
    def init_db_from_csv(self, csv_path):
        with self.fsql as s:
            s.clear_db()
            s.initial_db()
            s.load_from_csv(csv_path)
    
    def asset_table(self):
        cols = ["DATE", "ACCOUNT", "NAME", "NET_WORTH", "MONTH_INVEST", "MONTH_PROFIT"]
        with self.fsql as s:
            r = s.query_all_asset()
            print(r)
            df = pd.DataFrame(r, columns=cols)

        df["ASSET"] = df['ACCOUNT'] + '-' + df['NAME']
        df = df[["DATE", "ASSET", "NET_WORTH"]]
        return df
    
    def asset_chart(self):
        df = self.asset_table()
        df_sum = df.copy()
        df_sum = df_sum.groupby("DATE")["NET_WORTH"].sum().reset_index()
        print(df_sum)
        fig = px.line(df, x='DATE', y='NET_WORTH', color="ASSET")
        fig.add_bar(x=df_sum["DATE"], y=df_sum["NET_WORTH"], name="TOTAL")
        return fig
    
    def account_df(self):
        df = pd.DataFrame()
        for k,v in self.acc.items():
            print(k)
            print(v)
            df = pd.concat([df,v.to_df()])
        return df
        