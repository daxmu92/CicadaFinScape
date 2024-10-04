import unittest
import sqlite3
import os
import tempfile
from src.findatasql import FinDataSQL, SQLTableDef, SQLColDef


class TestFinDataSQL(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_database.db')
        self.fin_data_sql = FinDataSQL(self.db_path)

        # Create a sample table definition
        self.test_table = SQLTableDef("test_table",
                                      [SQLColDef("id", "INTEGER", "PRIMARY KEY"),
                                       SQLColDef("name", "TEXT", "NOT NULL"),
                                       SQLColDef("age", "INTEGER")])

    def tearDown(self):
        # Close the database connection
        if hasattr(self, 'fin_data_sql'):
            self.fin_data_sql.db.close()

        # Remove the temporary directory and its contents
        if os.path.exists(self.temp_dir):
            for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.temp_dir)

    def test_create_table(self):
        with self.fin_data_sql:
            self.fin_data_sql.create_table(self.test_table)
            tables = self.fin_data_sql.get_tables()
            self.assertIn(('test_table',), tables)

    def test_insert_and_query_data(self):
        with self.fin_data_sql:
            self.fin_data_sql.create_table(self.test_table)

            # Insert test data
            test_data = {"id": 1, "name": "John Doe", "age": 30}
            self.fin_data_sql.insert_data(test_data, self.test_table)

            # Query the inserted data
            result = self.fin_data_sql.query_data({"id": 1}, self.test_table)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], (1, "John Doe", 30))

    def test_update_data(self):
        with self.fin_data_sql:
            self.fin_data_sql.create_table(self.test_table)

            # Insert initial data
            initial_data = {"id": 1, "name": "John Doe", "age": 30}
            self.fin_data_sql.insert_data(initial_data, self.test_table)

            # Update the data
            update_data = {"age": 31}
            self.fin_data_sql.update_data({"id": 1}, update_data, self.test_table)

            # Query the updated data
            result = self.fin_data_sql.query_data({"id": 1}, self.test_table)
            self.assertEqual(result[0], (1, "John Doe", 31))

    def test_delete_data(self):
        with self.fin_data_sql:
            self.fin_data_sql.create_table(self.test_table)

            # Insert test data
            test_data = {"id": 1, "name": "John Doe", "age": 30}
            self.fin_data_sql.insert_data(test_data, self.test_table)

            # Delete the data
            self.fin_data_sql.delete_data({"id": 1}, self.test_table)

            # Verify the data is deleted
            result = self.fin_data_sql.query_data({"id": 1}, self.test_table)
            self.assertEqual(len(result), 0)

    def test_query_period(self):
        with self.fin_data_sql:
            # Create a table with a date column and a type column
            period_table = SQLTableDef("period_table", [
                SQLColDef("id", "INTEGER", "PRIMARY KEY"),
                SQLColDef("date", "TEXT", "NOT NULL"),
                SQLColDef("type", "TEXT", "NOT NULL"),
                SQLColDef("value", "REAL", "NOT NULL")
            ])
            self.fin_data_sql.create_table(period_table)

            # Insert test data
            test_data = [{
                "id": 1,
                "date": "2023-01-01",
                "type": "A",
                "value": 100.0
            }, {
                "id": 2,
                "date": "2023-01-15",
                "type": "B",
                "value": 150.0
            }, {
                "id": 3,
                "date": "2023-02-01",
                "type": "A",
                "value": 200.0
            }, {
                "id": 4,
                "date": "2023-02-15",
                "type": "B",
                "value": 250.0
            }, {
                "id": 5,
                "date": "2023-03-01",
                "type": "A",
                "value": 300.0
            }]
            for data in test_data:
                self.fin_data_sql.insert_data(data, period_table)

            # Query data for a specific period and type
            start_date = "2023-01-15"
            end_date = "2023-02-15"
            period_filter = {"date": (start_date, end_date)}
            type_filter = {"type": "B"}
            result = self.fin_data_sql.query_period(period_filter, type_filter, period_table)

            # Verify the result
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0][1:], ("2023-01-15", "B", 150.0))
            self.assertEqual(result[1][1:], ("2023-02-15", "B", 250.0))

            # New test case: Query with empty normal filter
            result_all_types = self.fin_data_sql.query_period(period_filter, {}, period_table)

            # Verify the result for all types within the date range
            self.assertEqual(len(result_all_types), 3)
            self.assertEqual(result_all_types[0][1:], ("2023-01-15", "B", 150.0))
            self.assertEqual(result_all_types[1][1:], ("2023-02-01", "A", 200.0))
            self.assertEqual(result_all_types[2][1:], ("2023-02-15", "B", 250.0))


if __name__ == '__main__':
    unittest.main()
