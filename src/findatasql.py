import streamlit as st
import csv
import sqlite3
import copy
import pandas as pd


class SQLColDef:

    def __init__(self, name: str = "", type: str = "", constraint: str = "", format=None):
        self.name: str = name
        self.type = type
        self.constraint = constraint
        self.format_func = format

    def col_def_str(self):
        return f"{self.name} {self.type} {self.constraint}"

    def format(self, value, separate=False):
        if self.format_func is not None:
            value = self.format_func(value)

        if separate:
            return value

        if self.type == "TEXT":
            value = f"'{value}'"
        else:
            value = str(value)
        return value


class SQLTableDef:

    def __init__(self, name: str = "", cols: list[SQLColDef] = []):
        self._name: str = name
        self._cols = cols
        self._name_to_cols = {c.name: c for c in self._cols}

    def __getitem__(self, col_name: str) -> SQLColDef:
        return self._name_to_cols[col_name]

    def __setitem__(self, col_name: str, col_def: SQLColDef):
        if col_name not in self._name_to_cols:
            self._cols.append(col_def)
        self._name_to_cols[col_name] = col_def

    def name(self):
        return self._name

    def cols(self) -> list[SQLColDef]:
        return copy.copy(self._cols)

    def cols_str(self) -> str:
        ess_cols_str = ',\n'.join([x.name for x in self.cols()])
        return ess_cols_str

    def cols_name(self) -> list[str]:
        return [x.name for x in self.cols()]

    def create_table_str(self):
        col_def = ',\n'.join([x.col_def_str() for x in self.cols()])
        return f"CREATE TABLE {self.name()} ({col_def});"


class FinDataSQL:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db: sqlite3.Connection = None

    def __enter__(self):
        print(self.db_path)
        self.db = sqlite3.connect(self.db_path)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.db.close()

    def get_tables(self) -> list[str]:
        """
        Returns:
            list[str]: all tables' names in list
        """
        return self.exec("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

    def exec(self, exec_str):
        print(exec_str)
        return self.db.execute(exec_str)

    def exec_value(self, exec_str, values):
        print(exec_str)
        print(', '.join([str(x) for x in values]))
        return self.db.execute(exec_str, values)

    def clear_db(self):
        tables = self.get_tables()
        for table in tables:
            self.exec(f"DROP TABLE IF EXISTS {table[0]}")

    def drop_table(self, table: SQLTableDef):
        self.exec(f'''DROP TABLE IF EXISTS {table.name()}''')

    def create_table(self, table: SQLTableDef):
        self.exec(table.create_table_str())

    def empty(self, table: SQLTableDef):
        return self.exec(f"SELECT COUNT(*) FROM {table.name()}").fetchone()[0] == 0

    def query_all(self, table: SQLTableDef) -> list:
        results = self.exec(f"SELECT * FROM {table.name()}").fetchall()
        return results

    def insert_data(self, data: dict, table: SQLTableDef):
        insert_keys = []
        insert_values = []
        for c in table.cols():
            k = c.name
            assert k in data, f"{k} is not in {data}"
            insert_keys.append(k)
            value = c.format(data[k])
            insert_values.append(value)

        key_str = ', '.join(insert_keys)
        value_str = ', '.join(insert_values)
        execute_str = f"INSERT INTO {table.name()} ({key_str}) VALUES ({value_str});"
        self.exec(execute_str)

    def sql_placeholder_and_values(filter: dict, table: SQLTableDef, delimiter: str = "AND") -> tuple[str, list]:
        cmd_placeholder = ""
        values = []
        i = 0
        for k, v in filter.items():
            if i != 0:
                cmd_placeholder += f" {delimiter} "
            cmd_placeholder += f"{k} = ?"

            assert k in table.cols_name(), f"{k} is not in {table.cols_name()}"
            value = table[k].format(v, True)
            values.append(value)
            i = i + 1
        return cmd_placeholder, values

    def sql_cmd_between_period(col: SQLColDef, start: str, end: str):
        date_str = f'''{col.name} BETWEEN "{start}" AND "{end}"'''
        return date_str

    def sql_cmd_filter_cols_with_placeholder(cols, len_of_values):
        cols_str = ', '.join(cols)
        marks = ', '.join(['?'] * len(cols))
        placeholder = ', '.join([f"({marks})"] * len_of_values)
        cmd = f"({cols_str}) IN ({placeholder})"
        return cmd

    def update_data(self, filter: dict, data: dict, table: SQLTableDef):
        where_ph, where_values = FinDataSQL.sql_placeholder_and_values(filter, table, "AND")
        set_ph, set_values = FinDataSQL.sql_placeholder_and_values(data, table, ",")
        cmd_str = f'''UPDATE {table.name()} SET {set_ph} WHERE {where_ph}'''
        values = tuple(set_values + where_values)
        self.exec_value(cmd_str, values)

    def insert_or_update(self, filter: dict, data: dict, table: SQLTableDef):
        if self.query_exist(filter, table):
            self.update_data(filter, data, table)
        else:
            d = {**filter, **data}
            self.insert_data(d, table)

    def query_data(self, filter: dict, table: SQLTableDef) -> list:
        ph, values = FinDataSQL.sql_placeholder_and_values(filter, table, "AND")
        cmd_str = f'''SELECT * FROM {table.name()} WHERE {ph}'''
        return self.exec_value(cmd_str, values).fetchall()

    def query_exist(self, data: dict, table: SQLTableDef) -> bool:
        return len(self.query_data(data, table)) > 0

    def query_col(self, cols: list[str], table: SQLTableDef) -> list:
        col_str = ", ".join(cols)
        results = self.exec(f'''SELECT {col_str} FROM {table.name()}''').fetchall()
        return results

    def commit(self):
        self.db.commit()

    def query_period(self, period_filter: dict[str, tuple[any, any]], filter: dict, table: SQLTableDef):
        period_cmds = [FinDataSQL.sql_cmd_between_period(table[col], start, end) for col, (start, end) in period_filter.items()]
        period_cmd = " AND ".join(period_cmds)

        values = []
        if filter:
            where_ph, where_values = FinDataSQL.sql_placeholder_and_values(filter, table, "AND")
            cmd_str = f'''SELECT * FROM {table.name()} WHERE {period_cmd} AND {where_ph}'''
            values += where_values
        else:
            cmd_str = f'''SELECT * FROM {table.name()} WHERE {period_cmd}'''

        return self.exec_value(cmd_str, values).fetchall()

    def delete_data(self, filter: dict, table: SQLTableDef):
        where_ph, where_values = FinDataSQL.sql_placeholder_and_values(filter, table)
        cmd_str = f'''DELETE FROM {table.name()} WHERE {where_ph}'''
        self.exec_value(cmd_str, where_values)

    def query_table_info(self, table: SQLTableDef):
        return self.exec(f'''PRAGMA table_info({table.name()})''').fetchall()

    def load_from_csv(self, csv_path, table: SQLTableDef):
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
        assert (len(csv_data[0]) == len(table.cols_name()))

        for data in csv_data[1:]:
            insert_data = {x: y for x, y in zip(table.cols_name(), data)}
            self.insert_data(insert_data, table)
        self.db.commit()

    def query_max(self, col, table: SQLTableDef):
        return self.exec(f'''SELECT MAX({col}) FROM {table.name()}''').fetchone()[0]
