from sqlite3 import Error, connect
from typing import List

import numpy as np

from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.py_experimenter_exceptions import DatabaseConnectionError


class DatabaseConnectorLITE(DatabaseConnector):
    _write_to_database_seperator = "','"

    def _extract_credentials(self):
        return dict(database=f'{self.database}.db')

    def connect(self):
        try:
            return connect(**self._db_credentials)
        except Error as err:
            raise DatabaseConnectionError(err)

    def _table_exists(self, cursor) -> bool:
        self.execute(cursor, f"SELECT name FROM sqlite_master WHERE type='table';")
        table_names = self.fetchall(cursor)
        return self.table_name in [x[0] for x in table_names]

    def _create_table(self, cursor, columns):
        self.execute(cursor,
                     f"CREATE TABLE {DatabaseConnectorLITE.escape_sql_chars(self.table_name)[0]} (ID Integer PRIMARY KEY AUTOINCREMENT, {','.join(DatabaseConnectorLITE.escape_sql_chars(*columns))});")

    def _table_has_correct_structure(self, cursor, typed_fields) -> List[str]:
        self.execute(cursor, f"PRAGMA table_info({DatabaseConnectorLITE.escape_sql_chars(self.table_name)[0]})")

        columns = [k[1] for k in self.fetchall(cursor)][1:-6]
        config_columns = [k[0] for k in typed_fields]
        return set(columns) == set(config_columns)

    @staticmethod
    def escape_sql_chars(*args):
        return args

    def _get_existing_rows(self, column_names):
        def _remove_string_markers(row):
            return row.replace("'", "")
        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, f"SELECT {column_names} FROM {self.table_name}")
        existing_rows = list(map(np.array2string, np.array(self.fetchall(cursor))))
        existing_rows = [' '.join(_remove_string_markers(row).split()) for row in existing_rows]
        self.close_connection(connection)
        return existing_rows
