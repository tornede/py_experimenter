import abc
import logging
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

from py_experimenter import utils
from py_experimenter.py_experimenter_exceptions import DatabaseConnectionError, EmptyFillDatabaseCallError, TableHasWrongStructureError


class DatabaseConnector(abc.ABC):

    def __init__(self, _config):
        self._config = _config
        self._table_name = self._config.get('PY_EXPERIMENTER', 'table')
        self._database_name = self._config.get('PY_EXPERIMENTER', 'database')

        self._db_credentials = self._extract_credentials()
        self._timestamp_on_result_fields = utils.timestamps_for_result_fields(self._config)

        self._test_connection()

    @abc.abstractmethod
    def _extract_credentials(self):
        pass

    @abc.abstractmethod
    def _test_connection(self):
        pass

    @ abc.abstractmethod
    def connect(self):
        pass

    def close_connection(self, connection):
        try:
            return connection.close()
        except Exception as e:
            raise DatabaseConnectionError(f'error \n{e}\n raised when closing connection to database.')

    def commit(self, connection) -> None:
        try:
            connection.commit()
        except Exception as e:
            raise DatabaseConnectionError(f'error \n{e}\n raised when committing to database.')

    def execute(self, cursor, sql_statement):
        try:
            cursor.execute(sql_statement)
        except Exception as e:
            raise DatabaseConnectionError(f'error \n{e}\n raised when executing sql statement.')

    def cursor(self, connection):
        try:
            return connection.cursor()
        except Exception as e:
            raise DatabaseConnectionError(f'error \n{e}\n raised when creating cursor.')

    def fetchall(self, cursor):
        try:
            return cursor.fetchall()
        except Exception as e:
            raise DatabaseConnectionError(f'error \n{e}\n raised when fetching all rows from database.')

    def create_table_if_not_existing(self) -> None:
        """
        Check if tables does exist. If not, a new table will be created.
        :param mysql_connection: mysql_connector to the database
        :param table_name: name of the table from the config
        :param experiment_config: experiment section of the config file
        """
        logging.debug("Create table if not exist")

        keyfields = utils.get_keyfields(self._config)
        resultfields = utils.get_resultfields(self._config)

        if self._timestamp_on_result_fields:
            resultfields = utils.add_timestep_result_columns(resultfields)

        connection = self.connect()
        cursor = self.cursor(connection)

        if self._table_exists(cursor):
            if not self._table_has_correct_structure(cursor, keyfields + resultfields):
                raise TableHasWrongStructureError("Keyfields or resultfields from the configuration do not match columns in the existing "
                                                  "table. Please change your configuration or delete the table in your database.")
        else:
            fields = (
                keyfields +
                [
                    ('creation_date', 'VARCHAR(255)'),
                    ('status', 'VARCHAR(255)'),
                    ('start_date', 'VARCHAR(255)'),
                    ('name', 'LONGTEXT'),
                    ('machine', 'VARCHAR(255)')
                ]
                + resultfields +
                [
                    ('end_date', 'VARCHAR(255)'),
                    ('error', 'LONGTEXT'),
                ]
            )

            columns = ['%s %s DEFAULT NULL' % (self.__class__.escape_sql_chars(field)[0], datatype) for field, datatype in fields]
            self._create_table(cursor, columns)
        self.close_connection(connection)

    def _exclude_fixed_columns(self, columns: List[str]) -> List[str]:
        amount_of_keyfields = len(utils.get_keyfield_names(self._config))
        amount_of_result_fields = len(utils.get_result_field_names(self._config))

        if self._timestamp_on_result_fields:
            amount_of_result_fields *= 2

        return columns[1:amount_of_keyfields + 1] + columns[-amount_of_result_fields - 2:-2]

    @abc.abstractmethod
    def _table_exists(self, cursor):
        pass

    @abc.abstractmethod
    def _create_table(self, cursor, columns):
        pass

    @abc.abstractmethod
    def _table_has_correct_structure(self, cursor, typed_fields):
        pass

    @abc.abstractclassmethod
    def escape_sql_chars(*args):
        pass

    def fill_table(self, parameters=None, fixed_parameter_combinations=None) -> None:
        logging.debug("Fill table with parameters")
        parameters = parameters if parameters is not None else {}
        fixed_parameter_combinations = fixed_parameter_combinations if fixed_parameter_combinations is not None else []

        keyfield_names = utils.get_keyfield_names(self._config)
        combinations = utils.combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations)

        if len(combinations) == 0:
            raise EmptyFillDatabaseCallError("No combinations to execute found.")

        column_names = np.array2string(np.array(keyfield_names), separator=',') \
            .replace('[', '') \
            .replace(']', '') \
            .replace("'", "")

        existing_rows = self._get_existing_rows(column_names)

        column_names += ",status"
        column_names += ",creation_date"

        time = datetime.now()
        values_added = 0
        for combination in combinations:
            if self._check_combination_in_existing_rows(combination, existing_rows, keyfield_names):
                continue
            values = list(combination.values())
            values.append("created")
            values.append("%s" % time.strftime("%m/%d/%Y, %H:%M:%S"))

            self._write_to_database(column_names.split(', '), values)
            values_added += 1
        logging.info(f"{values_added} values successfully added to database")

    def _check_combination_in_existing_rows(self, combination, existing_rows, keyfield_names) -> bool:
        def _get_column_values():
            return [combination[keyfield_name] for keyfield_name in keyfield_names]
        return ("[" + " ".join([str(value) for value in _get_column_values()]) + "]") in existing_rows

    @abc.abstractmethod
    def _get_existing_rows(self, column_names):
        pass

    def get_keyfield_values_to_execute(self) -> List[dict]:
        keyfield_names = utils.get_keyfield_names(self._config)

        execute_condition = "status='created'"

        stmt = f"SELECT {', '.join(keyfield_names)} FROM {self._table_name} WHERE {execute_condition}"

        connection = self.connect()
        cursor = self.cursor(connection)

        try:
            self.execute(cursor, stmt)
        except Exception as e:
            raise DatabaseConnectionError(f'error \n {e} raised. \n Please check if fill_table() was called correctly.')
        keyfield_name_value_pairs = pd.DataFrame(self.fetchall(cursor))
        if keyfield_name_value_pairs.empty:
            return []
        keyfield_name_value_pairs.columns = [i[0] for i in cursor.description]
        self.close_connection(connection)

        keyfield_values = [dict(parameter.to_dict()) for _, parameter in keyfield_name_value_pairs.iterrows()]

        return keyfield_values

    def _write_to_database(self, keys, values) -> None:
        """
        Write new row(s) to database
        :param keys: Column names
        :param values: Values for column names
        """
        keys = ", ".join(keys)
        values = "'" + self.__class__._write_to_database_separator.join([str(value) for value in values]) + "'"

        stmt = f"INSERT INTO {self._table_name} ({keys}) VALUES ({values})"

        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, stmt)
        self.commit(connection)
        self.close_connection(connection)

    def _update_database(self, keys, values, where):
        logging.info(f"Update '{keys}' with values '{values}' in database")

        try:
            connection = self.connect()
            cursor = self.cursor(connection)
            for key, value in zip(keys, values):
                stmt = f"UPDATE {self._table_name} SET {key}='{value}' WHERE {where}"
                self.execute(cursor, stmt)
            self.commit(connection)

        except Exception as err:
            logging.error(err)
            stmt = """UPDATE %s SET error="%s" WHERE %s""" % (self._table_name, err, where)
            self.execute(cursor, stmt)
            self.commit(connection)
        else:
            self.close_connection(connection)

    def not_executed_yet(self, where) -> bool:
        not_executed = False

        try:
            connection = self.connect()
            cursor = self.cursor(connection)

            stmt = "SELECT status FROM %s WHERE %s" % (self._table_name, where)

            self.execute(cursor, stmt)
            for result in cursor:
                if result[0] == 'created':
                    not_executed = True

        except Exception as err:
            logging.error(err)
        else:
            connection.close()
            return not_executed

    def delete_experiments_with_status(self, status):
        def _get_keyfields_from_columns(column_names, entries):
            df = pd.DataFrame(entries, columns=column_names)
            keyfields = utils.get_keyfield_names(self._config)
            entries = df[keyfields].values.tolist()
            return keyfields, entries

        connection = self.connect()
        cursor = self.cursor(connection)
        column_names = self.get_structure_from_table(cursor)

        self.execute(cursor, f"SELECT * FROM {self._table_name} WHERE status='{status}'")
        entries = cursor.fetchall()
        column_names, entries = _get_keyfields_from_columns(column_names, entries)
        self.execute(cursor, f"DELETE FROM {self._table_name} WHERE status='{status}'")
        self.commit(connection)
        self.close_connection(connection)

        return column_names, entries

    @abc.abstractmethod
    def get_structure_from_table(self, cursor):
        pass

    def get_table(self) -> pd.DataFrame:
        connection = self.connect()
        query = f"SELECT * FROM {self._table_name}"
        df = pd.read_sql(query, connection)
        self.close_connection(connection)
        return df
