from __future__ import annotations
import sqlite3
import copy
import csv
import pandas as pd
from src.st_utils import FinLogger
import src.finutils as fu


class SQLColDef:

    def __init__(self, name: str = "", type: str = "", constraint: str = "", format=None):
        self.name: str = name
        self.type = type
        self.constraint = constraint
        self.format_func = format

    def col_def_str(self):
        return f"{self.name} {self.type} {self.constraint}"

    def format(self, value):
        if self.format_func is not None:
            value = self.format_func(value)

        if self.type == "TEXT":
            value = f"'{value}'"
        else:
            value = str(value)
        return value


class SQLTableDef:

    def __init__(self, name: str = "", cols: list[SQLColDef] = [], ex_cols: list[SQLColDef] = []):
        self._name: str = name
        self._ess_cols = cols
        self._ex_cols = ex_cols

    def name(self):
        return self._name

    def ess_cols(self) -> list[SQLColDef]:
        return copy.copy(self._ess_cols)

    def ex_cols(self) -> list[SQLColDef]:
        return copy.copy(self._ex_cols)

    def cols_str(self):
        ess_cols_str = ',\n'.join([x.name for x in self.ess_cols()])
        return ess_cols_str

    def cols_name(self):
        return [x.name for x in self.ess_cols()]

    def create_table_str(self):
        ess_col_def = ',\n'.join([x.col_def_str() for x in self.ess_cols()])
        ex_col_def = ',\n'.join([x.col_def_str() for x in self.ex_cols()])
        if ex_col_def:
            col_def = ',\n'.join([ess_col_def, ex_col_def])
        else:
            col_def = ess_col_def

        return f"CREATE TABLE {self.name()} ({col_def});"

    def round_df(self, df: pd.DataFrame):
        cols = df.columns

        for col in self._ess_cols:
            if col.type == "REAL":
                if col.name in cols:
                    df[col.name] = df[col.name].round(1)
        return df


TRAN_INCOME_NAME = "INCOME"
TRAN_OUTLAY_NAME = "OUTLAY"

COL_DATE = SQLColDef("DATE", "TEXT", "NOT NULL", fu.norm_date)
COL_ACCOUNT = SQLColDef("ACCOUNT", "TEXT", "NOT NULL")
COL_NAME = SQLColDef("SUBACCOUNT", "TEXT", "NOT NULL")
COL_NET_WORTH = SQLColDef("NET_WORTH", "REAL", "NOT NULL", fu.norm_number)
COL_INFLOW = SQLColDef("INFLOW", "REAL", "NOT NULL", fu.norm_number)
COL_PROFIT = SQLColDef("PROFIT", "REAL", "NOT NULL", fu.norm_number)
ASSET_TABLE = SQLTableDef("SUBACCOUNT", [COL_DATE, COL_ACCOUNT, COL_NAME, COL_NET_WORTH, COL_INFLOW, COL_PROFIT])

COL_TRAN_ID = SQLColDef("ID", "INTEGER", "PRIMARY KEY")
COL_TRAN_TYPE = SQLColDef("TYPE", "TEXT", "NOT NULL")
COL_TRAN_VALUE = SQLColDef("VALUE", "REAL", "NOT NULL", fu.norm_number)
COL_TRAN_CAT = SQLColDef("CAT", "TEXT", "NOT NULL")
COL_TRAN_NOTE = SQLColDef("NOTE", "TEXT", "NOT NULL")
TRAN_TABLE = SQLTableDef("TRAN", [COL_TRAN_ID, COL_DATE, COL_TRAN_TYPE, COL_TRAN_VALUE, COL_TRAN_CAT, COL_TRAN_NOTE])

class AssetItem:

    def __init__(self, name: str, acc: Account):
        self.acc = acc
        self.name = name
        self.cats: dict[str, str] = {}
        self.ex_cols: list[SQLColDef] = []

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
        self.asset_list: list[AssetItem] = []

    def add_asset(self, asset: AssetItem):
        self.asset_list.append(asset)

    def to_json(self):
        return {"Name": self.name}

    def to_df(self):
        df = pd.DataFrame()
        for asset in self.asset_list:
            df = pd.concat([df, asset.to_df()])
        print(df)
        return df

    def add_to_df(self, df: pd.DataFrame):
        for asset in self.asset_list:
            asset.add_to_df(df)

    def asset(self, sub_name):
        asset = next(filter(lambda x: x.name == sub_name, self.asset_list), None)
        return asset

class FinSQL:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db: sqlite3.Connection = None

    def __enter__(self):
        print(self.db_path)
        self.db = sqlite3.connect(self.db_path)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.db.close()

    def _get_tables(self):
        return self.exec("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

    def exec(self, exec_str):
        print(exec_str)
        return self.db.execute(exec_str)

    def exec_value(self, exec_str, values):
        print(exec_str)
        print(', '.join([str(x) for x in values]))
        return self.db.execute(exec_str, values)

    def clear_db(self):
        tables = self._get_tables()
        for table in tables:
            self.exec(f"DROP TABLE IF EXISTS {table[0]}")
        self.db.commit()

    def clear_table(self, table: SQLTableDef):
        self.exec(f'''DROP TABLE IF EXISTS {table.name()}''')
        self.db.commit()

    def clear_asset_table(self):
        self.clear_table(ASSET_TABLE)

    def clear_tran_table(self):
        self.clear_table(TRAN_TABLE)

    def create_asset_table(self):
        self.exec(ASSET_TABLE.create_table_str())

    def create_tran_table(self):
        self.exec(TRAN_TABLE.create_table_str())

    def initial_db(self):
        tables = self._get_tables()
        if tables:
            print("db is not empty, can not initialize, please clear db first")
            return
        self.create_asset_table()
        self.create_tran_table()
        self.db.commit()

    def validate_db(self):
        tables = self._get_tables()
        for table in tables:
            if table[0] not in [ASSET_TABLE.name(), TRAN_TABLE.name()]:
                FinLogger.warn(f"Database contain unknown table {table[0]} !")

        if ASSET_TABLE.name() not in [x[0] for x in tables]:
            FinLogger.warn(f"{ASSET_TABLE.name()} table is not in database")
            return False

        if TRAN_TABLE.name() not in [x[0] for x in tables]:
            FinLogger.warn(f"{TRAN_TABLE.name()} table is not in database")
            return False

        return True

    def empty(self, table: SQLTableDef):
        return self.exec(f"SELECT COUNT(*) FROM {table.name()}").fetchone()[0] == 0

    def insert_data(self, data, table: SQLTableDef):
        insert_keys = []
        insert_values = []
        for c in table.ess_cols():
            k = c.name
            assert k in data, f"{k} is not in {data}"
            insert_keys.append(k)
            value = c.format(data[k])
            insert_values.append(value)
        for k in table.ex_cols():
            if k in data:
                insert_keys.append(data[k])
        key_str = ', '.join(insert_keys)
        value_str = ', '.join(insert_values)
        execute_str = f"INSERT INTO {table.name()} ({key_str}) VALUES ({value_str});"
        self.exec(execute_str)

    def insert_asset(self, data: dict):
        self.insert_data(data, ASSET_TABLE)

    def commit(self):
        self.db.commit()

    def cmd_filter_period(start_date: str, end_date: str):
        date_str = f'''DATE BETWEEN "{start_date}" AND "{end_date}"'''
        return date_str

    def cmd_filter_cols(cols, len_of_values):
        cols_str = ', '.join(cols)
        marks = ', '.join(['?'] * len(cols))
        placeholder = ', '.join([f"({marks})"] * len_of_values)
        cmd = f"({cols_str}) IN ({placeholder})"
        return cmd

    def cmd_filter_acc_ass(len_of_values):
        return FinSQL.cmd_filter_cols(["ACCOUNT", "SUBACCOUNT"], len_of_values)

    def load_from_csv(self, csv_path, table: SQLTableDef):
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
        assert (len(csv_data[0]) == len(table.ess_cols()))

        for data in csv_data[1:]:
            insert_data = {x.name: y for x, y in zip(table.ess_cols(), data)}
            self.insert_asset(insert_data)
        self.db.commit()

    def query_max(self, col, table: SQLTableDef):
        return self.exec(f'''SELECT MAX({col}) FROM {table.name()}''').fetchone()[0]

    def query_table_info(self, table: SQLTableDef):
        return self.exec(f'''PRAGMA table_info({table.name()})''').fetchall()

    def query_asset(self, acc_name, name):
        results = self.exec(f'''SELECT * FROM {ASSET_TABLE.name()} WHERE ACCOUNT = "{acc_name}" and SUBACCOUNT = "{name}"''')
        return results

    def query_all(self, table: SQLTableDef):
        results = self.exec(f"SELECT * FROM {table.name()}").fetchall()
        return results

    def query_all_asset(self):
        return self.query_all(ASSET_TABLE)

    def query_period(self, start_date, end_date, acc_ass_l: list[tuple], cols=ASSET_TABLE.cols_name()):
        col_str = ", ".join(cols)
        date_str = FinSQL.cmd_filter_period(start_date, end_date)
        filter_acc_ass_str = FinSQL.cmd_filter_acc_ass(len(acc_ass_l))
        where_str = f'''WHERE {date_str} AND {filter_acc_ass_str}'''
        values = acc_ass_l
        results = self.exec_value(f'''SELECT {col_str} FROM {ASSET_TABLE.name()} {where_str}''', values).fetchall()
        return results

    def query_period_all(self, start_date, end_date, cols=ASSET_TABLE.cols_name()):
        col_str = ", ".join(cols)
        date_str = FinSQL.cmd_filter_period(start_date, end_date)
        where_str = f'''WHERE {date_str}'''
        results = self.exec(f'''SELECT {col_str} FROM {ASSET_TABLE.name()} {where_str}''').fetchall()
        return results

    def query_date(self, date):
        results = self.exec(f'''SELECT * FROM {ASSET_TABLE.name()} WHERE DATE = "{date}"''').fetchall()
        return results

    def query_subacc_by_date(self, date, acc, sub):
        results = self.exec(f'''SELECT * FROM {ASSET_TABLE.name()} WHERE DATE = "{date}" and ACCOUNT = "{acc}" and SUBACCOUNT = "{sub}"''').fetchall()
        return results

    def query_data_exist(self, date, acc, sub):
        date = fu.norm_date(date)
        results = self.query_subacc_by_date(date, acc, sub)
        return len(results) > 0

    def update_data(self, filter: dict, data: dict):
        where_str = "WHERE "
        where_value = []
        i = 0
        for k, v in filter.items():
            if i != 0:
                where_str += " AND "
            where_str += f"{k} = ?"
            where_value.append(v)
            i = i + 1

        set_str = "SET "
        set_value = []
        i = 0
        for k, v in data.items():
            if i != 0:
                set_str += ", "
            set_str += f"{k} = ?"
            set_value.append(v)
            i += 1

        cmd_str = f'''UPDATE {ASSET_TABLE.name()} {set_str} {where_str}'''
        values = tuple(set_value + where_value)
        self.exec_value(cmd_str, values)

    def delete_data(self, filter: dict):
        where_str = "WHERE "
        where_value = []
        i = 0
        for k, v in filter.items():
            if i != 0:
                where_str += " AND "
            where_str += f"{k} = ?"
            where_value.append(v)
            i = i + 1
        cmd_str = f'''DELETE FROM {ASSET_TABLE.name()} {where_str}'''
        values = tuple(where_value)
        self.exec_value(cmd_str, values)

    def delete_asset(self, acc, sub):
        self.exec(f'''DELETE FROM {ASSET_TABLE.name()} WHERE ACCOUNT = "{acc}" and SUBACCOUNT = "{sub}"''')
        self.db.commit()

    def query_col(self, cols):
        col_str = ", ".join(cols)
        results = self.exec(f'''SELECT {col_str} FROM {ASSET_TABLE.name()}''').fetchall()
        return results

    def insert_tran(self, data):
        return self.insert_data(data, TRAN_TABLE)

    def query_tran_by_id(self, id):
        return self.exec(f'''SELECT * FROM {TRAN_TABLE.name()} WHERE {COL_TRAN_ID.name} = {id}''').fetchall()

    def delete_tran_by_id(self, id):
        return self.exec(f'''DELETE FROM {TRAN_TABLE.name()} WHERE {COL_TRAN_ID.name} = {id}''')

    def query_tran_all(self):
        return self.exec(f'''SELECT * FROM {TRAN_TABLE.name()}''').fetchall()

    def query_tran_by_date(self, date):
        return self.exec(f'''SELECT * FROM {TRAN_TABLE.name()} WHERE {COL_DATE.name} = {date}''').fetchall()

    def query_new_tran_id(self) -> int:
        if self.empty(TRAN_TABLE):
            return 0
        return int(self.query_max(COL_TRAN_ID.name, TRAN_TABLE)) + 1
