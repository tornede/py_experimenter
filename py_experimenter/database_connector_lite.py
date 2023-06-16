import logging
from sqlite3 import Error, connect
from typing import List, Tuple

import numpy as np

from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.exceptions import DatabaseConnectionError


class DatabaseConnectorLITE(DatabaseConnector):
    _write_to_database_separator = "','"
    _prepared_statement_placeholder = '?'

    def _extract_credentials(self):
        return dict(database=f'{self.database_name}.db')

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
            return connect(**self.database_credentials)
        except Error as err:
            raise DatabaseConnectionError(err)

    def _pull_open_experiment(self) -> Tuple[int, List, List]:
        with connect(**self.database_credentials) as connection:
            try:
                cursor = self.cursor(connection)
                experiment_id, description, values = self._execute_queries(connection, cursor)
            except Exception as err:
                connection.rollback()
                raise err

        return experiment_id, description, values

    def _table_exists(self, cursor) -> bool:
        self.execute(cursor, f"SELECT name FROM sqlite_master WHERE type='table';")
        table_names = self.fetchall(cursor)
        return self.table_name in [x[0] for x in table_names]

    @staticmethod
    def escape_sql_chars(*args):
        modified_args = list()
        for arg in args:
            arg = str(arg)
            if type(arg) == str:
                modified_args.append(arg.replace('`', '``').replace("'", "''").replace('"', '""'))

            else:
                modified_args.append(arg)
        return modified_args

    @staticmethod
    def get_autoincrement():
        return 'AUTOINCREMENT'

    def _table_has_correct_structure(self, cursor, typed_fields) -> List[str]:
        self.execute(cursor, f"PRAGMA table_info({self.table_name})")

        columns = self._exclude_fixed_columns([k[1] for k in self.fetchall(cursor)])
        config_columns = [k[0] for k in typed_fields]
        return set(columns) == set(config_columns)

    def _get_existing_rows(self, column_names: List[str]):
        def _remove_string_markers(row):
            return row.replace("'", "")
        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, f"SELECT {','.join(column_names)} FROM {self.table_name}")
        existing_rows = list(map(np.array2string, np.array(self.fetchall(cursor))))
        existing_rows = [' '.join(_remove_string_markers(row).split()) for row in existing_rows]
        self.close_connection(connection)
        return existing_rows

    def get_structure_from_table(self, cursor):
        def _get_column_names_from_entries(entries):
            return [entry[1] for entry in entries]
        self.execute(cursor, f"PRAGMA table_info({(self.table_name)})")
        column_names = _get_column_names_from_entries(self.fetchall(cursor))
        return column_names
