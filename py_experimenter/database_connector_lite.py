import logging
from sqlite3 import Error, connect
from typing import Dict, Iterable, List, Tuple

from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.exceptions import DatabaseConnectionError


class DatabaseConnectorLITE(DatabaseConnector):
    _write_to_database_separator = "','"
    _prepared_statement_placeholder = "?"

    def _test_connection(self):
        try:
            connection = self.connect()
        except Exception as err:
            logging.error(err)
            raise DatabaseConnectionError(err)
        else:
            self.close_connection(connection)

    def connect(self):
        try:
            return connect(f"{self.database_configuration.database_name}.db")
        except Error as err:
            raise DatabaseConnectionError(err)

    def _pull_open_experiment(self, random_order: bool) -> Tuple[int, List, List]:
        with connect(f"{self.database_configuration.database_name}.db") as connection:
            try:
                cursor = self.cursor(connection)
                experiment_id, description, values = self._select_open_experiments_from_db(connection, cursor, random_order)
            except Exception as err:
                connection.rollback()
                raise err

        return experiment_id, description, values

    def _get_pull_experiment_query(self, order_by):
        return super()._get_pull_experiment_query(order_by) + ";"

    def _table_exists(self, cursor) -> bool:
        self.execute(cursor, f"SELECT name FROM sqlite_master WHERE type='table';")
        table_names = self.fetchall(cursor)
        return self.database_configuration.table_name in [x[0] for x in table_names]

    def _last_insert_id_string(self) -> str:
        return "last_insert_rowid()"

    @staticmethod
    def random_order_string():
        return "RANDOM()"

    @staticmethod
    def get_autoincrement():
        return "AUTOINCREMENT"

    def _table_has_correct_structure(self, cursor, config_columns) -> List[str]:
        self.execute(cursor, f"PRAGMA table_info({self.database_configuration.table_name})")
        # Extracts columns from table
        table_columns = self._exclude_fixed_columns([k[1] for k in self.fetchall(cursor)])
        return set(table_columns) == set(config_columns.keys())

    def _get_existing_rows(self, column_names: List[str]) -> List[Dict[str, str]]:
        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, f"SELECT {','.join(column_names)} FROM {self.database_configuration.table_name}")
        existing_rows = self.fetchall(cursor)
        return [dict(zip(column_names, existing_row)) for existing_row in existing_rows]

    def get_structure_from_table(self, cursor):
        def _get_column_names_from_entries(entries):
            return [entry[1] for entry in entries]

        self.execute(cursor, f"PRAGMA table_info({(self.database_configuration.table_name)})")
        column_names = _get_column_names_from_entries(self.fetchall(cursor))
        return column_names
