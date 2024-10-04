from __future__ import annotations
from collections import OrderedDict
import json
import os
import pandas as pd
from src.st_utils import FinLogger

class AssetItem:

    def __init__(self, name: str, acc: Account):
        self.acc = acc
        self.name = name
        self.cats: dict[str, str] = {}

    def add_cat(self, cat: str, type: str):
        self.cats[cat] = type

    def to_json(self):
        return {"Name": self.name, "Account": self.acc.name, "Category": self.cats}

    def to_df(self):
        data = {
            "ACCOUNT": self.acc.name,
            "SUBACCOUNT": self.name,
        }
        data.update(self.cats)
        data = {k: [v] for k, v in data.items()}
        return pd.DataFrame.from_dict(data)

    def add_to_df(self, df: pd.DataFrame):
        data = {
            "ACCOUNT": self.acc.name,
            "SUBACCOUNT": self.name,
        }
        data.update(self.cats)
        data = [data[x] if x in data else None for x in df.columns]
        df.loc[len(df)] = data


class Account:

    def __init__(self, name: str):
        self.name = name
        self.assets: OrderedDict[str, AssetItem] = OrderedDict()

    def add_asset(self, asset: AssetItem):
        self.assets[asset.name] = asset

    def to_json(self):
        return {"Name": self.name}

    def to_df(self) -> pd.DataFrame:
        df = pd.DataFrame()
        for asset in self.assets.values():
            df = pd.concat([df, asset.to_df()])
        print(df)
        return df

    def add_to_df(self, df: pd.DataFrame):
        for asset in self.assets.values():
            asset.add_to_df(df)

    def __getitem__(self, sub_name: str) -> AssetItem:
        if sub_name not in self.assets:
            return None
        return self.assets[sub_name]

    def __setitem__(self, sub_name: str, asset: AssetItem):
        self.assets[sub_name] = asset

    def sub_name_list(self) -> list[str]:
        return list(self.assets.keys())


class FinConfig:

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: dict = {}
        self.cat_dict: dict[str, list[str]] = {}
        self.acc: dict[str, Account] = {}
        self.load_config_file(config_path)

    def clear_config(self) -> None:
        self.config = {}
        self.cat_dict = {}
        self.acc = {}

    def load_from_dict(self, config: dict):
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

    def load_config_file(self, config_path: str):
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            self.load_from_dict(config)
        else:
            config = {"Categories": [], "Accounts": [], "Assets": []}
            self.load_from_dict(config)
            self.write_config()

    def to_dict(self) -> dict:
        config = {}
        if self.cat_dict:
            config["Categories"] = self.cat_dict
        if self.acc:
            accs = [v.to_json() for k, v in self.acc.items()]
            config["Accounts"] = accs

        assets = []
        for k, v in self.acc.items():
            for asset in v.assets.values():
                assets.append(asset.to_json())

        if assets:
            config["Assets"] = assets
        return config

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

    def write_config(self):
        config = self.to_dict()
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)

    def clean_up_cat(self):
        for k, v in self.acc.items():
            for sub in v.assets.values():
                sub.cats = {k: v for k, v in sub.cats.items() if k in self.cat_dict}

    def add_asset(self, acc_name: str, sub_name: str, cats: dict):
        if acc_name not in self.acc:
            self.acc[acc_name] = Account(acc_name)

        acc = self.acc[acc_name]
        asset = AssetItem(sub_name, acc)
        for k, v in cats.items():
            asset.add_cat(k, v)
        acc.add_asset(asset)
        self.write_config()

    def get_asset(self, acc_name: str, sub_name: str) -> AssetItem:
        if acc_name not in self.acc:
            return None
        acc = self.acc[acc_name]
        return acc[sub_name]

    def delete_asset(self, acc_name: str, sub_name: str) -> None:
        if acc_name not in self.acc:
            return
        acc = self.acc[acc_name]
        if sub_name not in acc.assets:
            return
        del acc.assets[sub_name]
        self.write_config()

    def acc_name_list(self) -> list[str]:
        return [v.name for v in self.acc.values()]

    def subacc_name_list(self, acc_name: str) -> list[str]:
        return self.acc[acc_name].sub_name_list()

    def account_df(self) -> pd.DataFrame:
        cols = ["ACCOUNT", "SUBACCOUNT"]
        cols.extend([k for k in self.cat_dict])
        df = pd.DataFrame(columns=cols)
        for k, v in self.acc.items():
            v.add_to_df(df)
        return df

    def account_from_df(self, df: pd.DataFrame):
        for index, row in df.iterrows():
            acc_name = row["ACCOUNT"]
            sub_name = row["SUBACCOUNT"]
            if acc_name not in self.acc:
                self.acc[acc_name] = Account(acc_name)
            acc = self.acc[acc_name]

            asset = acc[sub_name]
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

            asset = acc[sub_name]
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
        for _, row in df.iterrows():
            name: str = row["Category"]
            labels: str = row["Labels"]
            cat_dict[name] = labels.split(',')
        self.cat_dict = cat_dict
        self.write_config()
        self.clean_up_cat()
