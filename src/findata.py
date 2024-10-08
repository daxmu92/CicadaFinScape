from typing import Sequence
import pandas as pd
import streamlit as st

import src.findatasql as fsql
import src.finutils as fu


class FinBaseData():

    def __init__(self, db: fsql.FinDataSQL, table_name="ACCOUNT"):
        self._name = table_name
        self._db = db
        self._df: pd.DataFrame = None
        self._table: fsql.SQLTableDef = None

    def validate(self):
        if self._df is None:
            with self._db as db:
                tables = db.get_tables()
            if self._name not in [x[0] for x in tables]:
                return False
            self._df = self.load_from_db()

        return True

    def load_from_db(self):
        with self._db as db:
            r = db.query_all(self._table)

        cols = self._table.cols_name()
        self._df = pd.DataFrame(r, columns=cols)

    def reset(self):
        with self._db as db:
            db.drop_table(self._table)
            db.create_table(self._table)
            db.commit()

    def _query(self, filter: dict) -> pd.DataFrame:
        return self._df.loc[(self._df[list(filter)] == pd.Series(filter)).all(axis=1)]

    def _query_period(self, period_filter: dict[str, tuple[any, any]], filter: dict[str, any]) -> pd.DataFrame:
        df = self._query(filter)
        for col, (start, end) in period_filter.items():
            df = df[df[col].between(start, end)]
        return df

    def load_from_df(self, df: pd.DataFrame, append: bool = False):
        if not append:
            self.reset()

        with self._db as db:
            for _, row in df.iterrows():
                db.insert_data(row.to_dict(), self._table)
            db.commit()
        self.load_from_db()


class FinAssetData(FinBaseData):

    def __init__(self, db: fsql.FinDataSQL, table_name="SUBACCOUNT"):
        self._name = table_name
        self._db = db
        self._df: pd.DataFrame = None
        self._table = FinAssetData.get_table_def()

    def get_table_def() -> fsql.SQLTableDef:
        COL_DATE = fsql.SQLColDef("DATE", "TEXT", "NOT NULL", fu.norm_date)
        COL_ACCOUNT = fsql.SQLColDef("ACCOUNT", "TEXT", "NOT NULL")
        COL_NAME = fsql.SQLColDef("SUBACCOUNT", "TEXT", "NOT NULL")
        COL_NET_WORTH = fsql.SQLColDef("NET_WORTH", "REAL", "NOT NULL", fu.norm_number)
        COL_INFLOW = fsql.SQLColDef("INFLOW", "REAL", "NOT NULL", fu.norm_number)
        COL_PROFIT = fsql.SQLColDef("PROFIT", "REAL", "NOT NULL", fu.norm_number)
        ASSET_TABLE = fsql.SQLTableDef("SUBACCOUNT", [COL_DATE, COL_ACCOUNT, COL_NAME, COL_NET_WORTH, COL_INFLOW, COL_PROFIT])
        return ASSET_TABLE

    def insert_data(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float):
        data = {x.name: y for x, y in zip(self._table.cols(), [date, acc, sub, net, inflow, profit])}
        with self._db as db:
            db.insert_data(data, self._table)
            db.commit()
        self.load_from_db()

    def update_data(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float):
        filter = {"DATE": date, "ACCOUNT": acc, "SUBACCOUNT": sub}
        update_data = {"NET_WORTH": net, "INFLOW": inflow, "PROFIT": profit}
        with self._db as db:
            db.update_data(filter, update_data, self._table)
            db.commit()
        self.load_from_db()

    def insert_or_update(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float):
        filter = {"DATE": date, "ACCOUNT": acc, "SUBACCOUNT": sub}
        update_data = {"NET_WORTH": net, "INFLOW": inflow, "PROFIT": profit}
        with self._db as db:
            db.insert_or_update(filter, update_data, self._table)
            db.commit()
        self.load_from_db()

    def batch_insert(self, data: Sequence[list]):
        with self._db as db:
            for row in data:
                data = {x.name: y for x, y in zip(self._table.cols(), row)}
                db.insert_data(data, self._table)
            db.commit()
        self.load_from_db()

    def batch_insert_or_update(self, data: Sequence[list]):
        with self._db as db:
            for row in data:
                filter = {"DATE": row[0], "ACCOUNT": row[1], "SUBACCOUNT": row[2]}
                update_data = {"NET_WORTH": row[3], "INFLOW": row[4], "PROFIT": row[5]}
                db.insert_or_update(filter, update_data, self._table)
            db.commit()
        self.load_from_db()

    def delete_data(self, date: str, acc: str, sub: str):
        filter = {"DATE": date, "ACCOUNT": acc, "SUBACCOUNT": sub}
        with self._db as db:
            db.delete_data(filter, self._table)
            db.commit()
        self.load_from_db()

    def delete_asset(self, acc: str, sub: str):
        filter = {"ACCOUNT": acc, "SUBACCOUNT": sub}
        with self._db as db:
            db.delete_data(filter, self._table)
            db.commit()
        self.load_from_db()

    def query(self, date: str = "", acc: str = "", sub: str = "") -> pd.DataFrame:
        filter_dict = {}
        if date:
            filter_dict["DATE"] = date
        if acc:
            filter_dict["ACCOUNT"] = acc
        if sub:
            filter_dict["SUBACCOUNT"] = sub

        return self._query(filter=filter_dict)

    def query_last(self, date: str, acc: str, sub: str) -> pd.DataFrame:
        df = self.query(acc=acc, sub=sub)
        if df.empty:
            return pd.DataFrame(columns=df.columns)

        # Filter for dates less than the given date
        df_filtered = df[df['DATE'] < date]
        if df_filtered.empty:
            return pd.DataFrame(columns=df.columns)

        # Get the row with the maximum date
        max_date = df_filtered['DATE'].max()
        result = df_filtered[df_filtered['DATE'] == max_date]
        return result

    def query_period(self, start_date: str, end_date: str) -> pd.DataFrame:
        period_filter = {"DATE": (start_date, end_date)}
        filter = {}
        return self._query_period(period_filter, filter)

    def query_date_range(self) -> tuple[str, str]:
        df = self._df
        return df["DATE"].min(), df["DATE"].max()

    def load_from_df(self, df: pd.DataFrame, append: bool = False):
        if not append:
            self.reset()
            self.batch_insert_or_update(df.to_records(index=False))
        else:
            self.batch_insert_or_update(df.to_records(index=False))


class FinTranData(FinBaseData):

    def __init__(self, db: fsql.FinDataSQL, table_name="TRAN"):
        self._name = table_name
        self._db = db
        self._df: pd.DataFrame = None
        self._table = FinTranData.get_table_def()

    def get_table_def() -> fsql.SQLTableDef:
        # TRAN_INCOME_NAME = "INCOME"
        # TRAN_OUTLAY_NAME = "OUTLAY"
        COL_TRAN_ID = fsql.SQLColDef("ID", "INTEGER", "PRIMARY KEY")
        COL_DATE = fsql.SQLColDef("DATE", "TEXT", "NOT NULL", fu.norm_date)
        COL_TRAN_TYPE = fsql.SQLColDef("TYPE", "TEXT", "NOT NULL")
        COL_TRAN_VALUE = fsql.SQLColDef("VALUE", "REAL", "NOT NULL", fu.norm_number)
        COL_TRAN_CAT = fsql.SQLColDef("CAT", "TEXT", "NOT NULL")
        COL_TRAN_NOTE = fsql.SQLColDef("NOTE", "TEXT", "NOT NULL")
        TRAN_TABLE = fsql.SQLTableDef("TRAN", [COL_TRAN_ID, COL_DATE, COL_TRAN_TYPE, COL_TRAN_VALUE, COL_TRAN_CAT, COL_TRAN_NOTE])
        return TRAN_TABLE

    def insert_data(self, id: int, date: str, type: str, value: float, cat: str, note: str):
        data = {x.name: y for x, y in zip(self._table.cols(), [id, date, type, value, cat, note])}
        with self._db as db:
            db.insert_data(data, self._table)
            db.commit()
        self.load_from_db()

    def delete_data(self, id: int):
        filter = {"ID": id}
        with self._db as db:
            db.delete_data(filter, self._table)
            db.commit()
        self.load_from_db()

    def query(self, date: str = "", type: str = "", cat: str = "") -> pd.DataFrame:
        filter = {}
        if date:
            filter["DATE"] = date
        if type:
            filter["TYPE"] = type
        if cat:
            filter["CAT"] = cat
        return self._query(filter)

    def query_by_id(self, id: int) -> pd.DataFrame:
        filter = {"ID": id}
        return self._query(filter)

    def get_unique_id(self, date: str) -> int:
        df_date = self._df[self._df["DATE"] == date]
        max_id_by_date = df_date["ID"].max() % 10000 + 1 if not df_date.empty else 0
        digit_date = fu.digit_date(date)
        return digit_date * 10000 + max_id_by_date

    def reindex(self):
        df = self._df.copy()
        self._df = pd.DataFrame(columns=self._table.cols_name())
        for _, row in df.iterrows():
            date = row["DATE"]
            id = self.get_unique_id(date)
            row["ID"] = id
            self._df = pd.concat([self._df, row.to_frame().T], ignore_index=True)
        print(self._df)
        self.load_from_df(self._df)

class FinDataContext():

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = fsql.FinDataSQL(db_path)
        self.asset_data = FinAssetData(self.db)
        self.tran_data = FinTranData(self.db)

        if self.validate():
            self.asset_data.load_from_db()
            self.tran_data.load_from_db()

    def validate(self):
        return self.asset_data.validate() and self.tran_data.validate()

    def init_db(self) -> None:
        with self.db as db:
            tables = db.get_tables()
            if tables:
                print("db is not empty, can not initialize, please clear db first")
                return
            db.create_table(self.asset_data._table)
            db.create_table(self.tran_data._table)
            db.commit()
        self.asset_data.load_from_db()
        self.tran_data.load_from_db()

    def clear_db(self):
        with self.db as db:
            db.clear_db()
            db.commit()

    def query_asset_info(self) -> pd.DataFrame:
        with self.db as db:
            return db.query_table_info(self.asset_data._table)

    def query_tran_info(self) -> pd.DataFrame:
        with self.db as db:
            return db.query_table_info(self.tran_data._table)

    def get_asset_cols_name(self):
        return self.asset_data._table.cols_name()

    def insert_asset(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float) -> None:
        self.asset_data.insert_data(date, acc, sub, net, inflow, profit)

    def update_asset(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float) -> None:
        self.asset_data.update_data(date, acc, sub, net, inflow, profit)

    def insert_or_update_asset(self, date: str, acc: str, sub: str, net: float, inflow: float, profit: float) -> None:
        self.asset_data.insert_or_update(date, acc, sub, net, inflow, profit)

    def delete_asset_data(self, date: str, acc: str, sub: str) -> None:
        self.asset_data.delete_data(date, acc, sub)

    def delete_asset(self, acc: str, sub: str) -> None:
        self.asset_data.delete_asset(acc, sub)

    def reset_asset_table(self):
        self.asset_data.reset()

    def reset_tran_table(self):
        self.tran_data.reset()

    def _query_asset(self, filter: dict) -> pd.DataFrame:
        return self.asset_data._query(filter)

    def query_asset(self, date: str = "", acc: str = "", sub: str = "") -> pd.DataFrame:
        return self.asset_data.query(date=date, acc=acc, sub=sub)

    def query_last_asset(self, date: str, acc: str, sub: str) -> pd.DataFrame:
        return self.asset_data.query_last(date, acc, sub)

    def query_period_asset(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.asset_data.query_period(start_date, end_date)

    def query_date_range(self) -> tuple[str, str]:
        return self.asset_data.query_date_range()

    def query_asset_exist(self, date: str, acc: str, sub: str) -> bool:
        return not self.asset_data.query(date, acc, sub).empty

    def insert_tran(self, date: str, type: str, value: float, cat: str, note: str):
        id = self.tran_data.get_unique_id(date)
        self.tran_data.insert_data(id, date, type, value, cat, note)

    def delete_tran(self, id: int):
        self.tran_data.delete_data(id)

    def query_tran(self, date: str = "", type: str = "", cat: str = "") -> pd.DataFrame:
        return self.tran_data.query(date, type, cat)

    def df_to_asset(self, df: pd.DataFrame, append: bool = False):
        self.asset_data.load_from_df(df, append)

    def df_to_tran(self, df: pd.DataFrame, append: bool = False):
        self.tran_data.load_from_df(df, append)

    def reindex_tran_id(self):
        self.tran_data.reindex()
