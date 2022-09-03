import logging
from configparser import ConfigParser

import numpy as np
from mysql.connector import Error, connect

from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.py_experimenter_exceptions import DatabaseConnectionError, DatabaseCreationError, TableError
from py_experimenter.utils import load_config


class DatabaseConnectorMYSQL(DatabaseConnector):
    _write_to_database_separator = "', '"

    def __init__(self, config: ConfigParser, credential_path):
        credentials = load_config(credential_path)
        self.host = credentials.get('CREDENTIALS', 'host')
        self.user = credentials.get('CREDENTIALS', 'user')
        self.password = credentials.get('CREDENTIALS', 'password')

        super().__init__(config)

        self._create_database_if_not_existing()

    def _test_connection(self):
        modified_credentials = self._db_credentials.copy()
        del modified_credentials['database']
        try:
            connection = self.connect(modified_credentials)
        except Exception as err:
            logging.error(err)
            raise DatabaseConnectionError(err)
        else:
            self.close_connection(connection)

    def _create_database_if_not_existing(self):
        modified_credentials = self._db_credentials.copy()
        del modified_credentials['database']
        try:
            connection = self.connect(modified_credentials)
            cursor = self.cursor(connection)
            self.execute(cursor, "SHOW DATABASES")
            databases = [database[0] for database in self.fetchall(cursor)]

            if self._database_name not in databases:
                self.execute(cursor, f"CREATE DATABASE {self._database_name}")
                self.commit(connection)
            self.close_connection(connection)
        except Exception as err:
            raise DatabaseCreationError(f'Error when creating database: \n {err}')

    def _extract_credentials(self):
        return dict(host=self.host, user=self.user, database=self._database_name, password=self.password)

    def connect(self, credentials=None):
        try:
            if credentials is None:
                credentials = self._db_credentials
            return connect(**credentials, use_pure=True)
        except Error as err:
            raise DatabaseConnectionError(err)

    def _table_exists(self, cursor):
        self.execute(cursor, f"SHOW TABLES LIKE '{self._get_tablename_for_query()}'")
        return self.fetchall(cursor)

    def _create_table(self, cursor, columns):
        try:
            self.execute(cursor,
                         f"CREATE TABLE {DatabaseConnectorMYSQL.escape_sql_chars(self._table_name)[0]} (ID int NOT NULL AUTO_INCREMENT, {','.join(columns)}, PRIMARY KEY (ID))")
        except Exception as err:
            raise TableError(f'Error when creating table: {err}')

    def _get_tablename_for_query(self):
        return DatabaseConnectorMYSQL.escape_sql_chars(self._table_name)[0]

    def _table_has_correct_structure(self, cursor, typed_fields):
        self.execute(cursor,
                     f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self._table_name}' AND TABLE_SCHEMA = '{self._database_name}'")

        columns = self._exclude_fixed_columns([k[0] for k in self.fetchall(cursor)])
        config_columns = [k[0] for k in typed_fields]
        return set(columns) == set(config_columns)

    @staticmethod
    def escape_sql_chars(*args):
        escaped_args = []
        for arg in args:
            if isinstance(arg, str):
                escaped_args.append(arg.replace("'", "''").replace('"', '""').replace('`', '``'))
            else:
                escaped_args.append(arg)
        return escaped_args

    def _get_existing_rows(self, column_names):
        def _remove_double_whitespaces(existing_rows):
            return [' '.join(row.split()) for row in existing_rows]

        def _remove_string_markers(existing_rows):
            return [row.replace("'", "") for row in existing_rows]

        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, f"SELECT {column_names} FROM {self._table_name}")
        existing_rows = list(map(np.array2string, np.array(self.fetchall(cursor))))
        existing_rows = _remove_string_markers(existing_rows)
        existing_rows = _remove_double_whitespaces(existing_rows)
        self.close_connection(connection)
        return existing_rows

    def get_structure_from_table(self, cursor):
        def _get_column_names_from_entries(entries):
            return [entry[0] for entry in entries]

        self.execute(cursor, f"SHOW COLUMNS FROM {self._table_name}")
        column_names = _get_column_names_from_entries(self.fetchall(cursor))
        return column_names
