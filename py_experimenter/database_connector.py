import abc
import itertools
import logging
from configparser import ConfigParser
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from py_experimenter import utils
from py_experimenter.exceptions import (CreatingTableError, DatabaseConnectionError, EmptyFillDatabaseCallError, NoExperimentsLeftException,
                                        TableHasWrongStructureError)
from py_experimenter.experiment_status import ExperimentStatus


class DatabaseConnector(abc.ABC):

    def __init__(self, config: ConfigParser, use_codecarbon: bool, codecarbon_config: ConfigParser):
        self.config = config
        self.codecarbon_config = codecarbon_config
        self.table_name = self.config.get('PY_EXPERIMENTER', 'table')
        self.database_name = self.config.get('PY_EXPERIMENTER', 'database')

        self.database_credentials = self._extract_credentials()
        self.timestamp_on_result_fields = utils.timestamps_for_result_fields(self.config)

        self.use_codecarbon = use_codecarbon
        self._test_connection()

    @abc.abstractmethod
    def _extract_credentials(self):
        pass

    @abc.abstractmethod
    def _test_connection(self):
        pass

    @abc.abstractmethod
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

    def execute(self, cursor, sql_statement, values=None) -> None:
        try:
            if values is None:
                cursor.execute(sql_statement)
            else:
                cursor.execute(sql_statement, values)
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
        logging.debug("Create table if not exist")

        keyfields = utils.get_keyfields(self.config)
        resultfields = utils.get_resultfields(self.config)
        if self.timestamp_on_result_fields:
            resultfields = utils.add_timestep_result_columns(resultfields)

        connection = self.connect()
        cursor = self.cursor(connection)
        if self._table_exists(cursor):
            if not self._table_has_correct_structure(cursor, keyfields + resultfields):
                raise TableHasWrongStructureError("Keyfields or resultfields from the configuration do not match columns in the existing "
                                                  "table. Please change your configuration or delete the table in your database.")
        else:
            columns = self._compute_columns(keyfields, resultfields)
            self._create_table(cursor, columns, self.table_name)

            for logtable_name, logtable_columns in utils.extract_logtables(self.config, self.table_name).items():
                self._create_table(cursor, logtable_columns, logtable_name, table_type='logtable')

            if self.use_codecarbon:
                codecarbon_columns = utils.extract_codecarbon_columns()
                self._create_table(cursor, codecarbon_columns, f"{self.table_name}_codecarbon", table_type='codecarbon')

        self.close_connection(connection)

    @abc.abstractmethod
    def _table_exists(self, cursor, table_name: str):
        pass

    @staticmethod
    def _compute_columns(keyfields, resultfields):
        return (keyfields +
                [('creation_date', 'DATETIME'),
                    ('status', 'VARCHAR(255)'),
                    ('start_date', 'DATETIME'),
                    ('name', 'LONGTEXT'),
                    ('machine', 'VARCHAR(255)')] +
                resultfields +
                [('end_date', 'DATETIME'),
                    ('error', 'LONGTEXT')]
                )

    def _exclude_fixed_columns(self, columns: List[str]) -> List[str]:
        amount_of_keyfields = len(utils.get_keyfield_names(self.config))
        amount_of_result_fields = len(utils.get_result_field_names(self.config))

        if self.timestamp_on_result_fields:
            amount_of_result_fields *= 2

        return columns[1:amount_of_keyfields + 1] + columns[-amount_of_result_fields - 2:-2]

    def _create_table(self, cursor, columns: List[Tuple['str']], table_name: str, table_type: str = 'standard'):
        query = self._get_create_table_query(columns, table_name, table_type)
        try:
            self.execute(cursor, query)
        except Exception as err:
            raise CreatingTableError(f'Error when creating table: {err}')

    def _get_create_table_query(self, columns: List[Tuple['str']], table_name: str, table_type: str = 'standard'):
        columns = ['%s %s DEFAULT NULL' % (field, datatype) for field, datatype in columns]
        columns = ','.join(columns)
        query = f"CREATE TABLE {table_name} (ID INTEGER PRIMARY KEY {self.get_autoincrement()}"
        if table_type == 'standard':
            query += f", {columns}"
        elif table_type == 'logtable':
            query += f", experiment_id INTEGER, timestamp DATETIME, {columns}, FOREIGN KEY (experiment_id) REFERENCES {self.table_name}(ID) ON DELETE CASCADE"
        elif table_type == 'codecarbon':
            query += f", experiment_id INTEGER, {columns}, FOREIGN KEY (experiment_id) REFERENCES {self.table_name}(ID) ON DELETE CASCADE"
        else:
            raise ValueError(f"Unknown table type: {table_type}")
        return query + ');'

    @abc.abstractstaticmethod
    def get_autoincrement(self):
        pass

    @abc.abstractmethod
    def _table_has_correct_structure(self, cursor, typed_fields):
        pass

    def fill_table(self, parameters=None, fixed_parameter_combinations=None) -> None:
        logging.debug("Fill table with parameters.")
        parameters = parameters if parameters is not None else {}
        fixed_parameter_combinations = fixed_parameter_combinations if fixed_parameter_combinations is not None else []

        keyfield_names = utils.get_keyfield_names(self.config)
        combinations = utils.combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations)

        if len(combinations) == 0:
            raise EmptyFillDatabaseCallError("No combinations to execute found.")

        column_names = list(combinations[0].keys())
        logging.debug("Getting existing rows.")
        existing_rows = set(self._get_existing_rows(column_names))
        time = utils.get_timestamp_representation()

        rows_skipped = 0
        rows = []
        logging.debug("Checking which of the experiments to be inserted already exist.")
        for combination in combinations:
            if self._check_combination_in_existing_rows(combination, existing_rows, keyfield_names):
                rows_skipped += 1
                continue
            values = list(combination.values())
            values.append(ExperimentStatus.CREATED.value)
            values.append(time)
            rows.append(values)

        if rows:
            logging.debug(f"Now adding {len(rows)} rows to database. {rows_skipped} rows were skipped.")
            self._write_to_database(rows, column_names + ["status", "creation_date"])
            logging.info(f"{len(rows)} rows successfully added to database. {rows_skipped} rows were skipped.")
        else:
            logging.info(f"No rows to add. All the {len(combinations)} experiments already exist.")

    def _check_combination_in_existing_rows(self, combination, existing_rows, keyfield_names) -> bool:
        def _get_column_values():
            return [combination[keyfield_name] for keyfield_name in keyfield_names]
        return ("[" + " ".join([str(value) for value in _get_column_values()]) + "]") in existing_rows

    @abc.abstractmethod
    def _get_existing_rows(self, column_names):
        pass

    def get_experiment_configuration(self):
        try:
            experiment_id, description, values = self._pull_open_experiment()
        except IndexError as e:
            raise NoExperimentsLeftException("No experiments left to execute")
        except Exception as e:
            raise DatabaseConnectionError(f'error \n {e} raised. \n Please check if fill_table() was called correctly.')

        return experiment_id, dict(zip([i[0] for i in description], *values))

    def _execute_queries(self, connection, cursor) -> Tuple[int, List, List]:
        order_by = "id"
        time = utils.get_timestamp_representation()

        self.execute(cursor, f"SELECT id FROM {self.table_name} WHERE status = 'created' ORDER BY {order_by} LIMIT 1;")
        experiment_id = self.fetchall(cursor)[0][0]
        self.execute(
            cursor, f"UPDATE {self.table_name} SET status = {self._prepared_statement_placeholder}, start_date = {self._prepared_statement_placeholder} WHERE id = {self._prepared_statement_placeholder};", (ExperimentStatus.RUNNING.value, time, experiment_id))
        keyfields = ','.join(utils.get_keyfield_names(self.config))
        self.execute(cursor, f"SELECT {keyfields} FROM {self.table_name} WHERE id = {experiment_id};")
        values = self.fetchall(cursor)
        self.commit(connection)
        description = cursor.description
        return experiment_id, description, values

    @abc.abstractmethod
    def _pull_open_experiment(self) -> Tuple[int, List, List]:
        pass

    def _write_to_database(self, values: List, columns=List[str]) -> None:
        values_prepared = ','.join([f"({', '.join([self._prepared_statement_placeholder] * len(columns))})"] * len(values))
        values = list(map(lambda x: str(x) if x is not None else x, itertools.chain(*values)))
        stmt = f"INSERT INTO {self.table_name} ({','.join(columns)}) VALUES {values_prepared}"

        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, stmt, values)
        self.commit(connection)
        self.close_connection(connection)

    def prepare_write_query(self, table_name: str, keys) -> str:
        return f"INSERT INTO {table_name} ({', '.join(keys)}) VALUES ({','.join([self._prepared_statement_placeholder] * len(keys))})"

    def update_database(self, table_name: str, values: Dict[str, Union[str, int, object]], condition: str):
        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, self._prepare_update_query(table_name, values.keys(), condition),
                     list(values.values()))
        self.commit(connection)
        self.close_connection(connection)

    def _prepare_update_query(self, table_name: str, values: Dict[str, Union[str, int, object]],  condition: str) -> str:
        return (f"UPDATE {table_name} SET {', '.join(f'{key} = {self._prepared_statement_placeholder}' for key in values)}"
                f" WHERE {condition}")

    def reset_experiments(self, *states: str) -> None:
        def get_dict_for_keyfields_and_rows(keyfields: List[str], rows: List[List[str]]) -> List[dict]:
            return [{key: value for key, value in zip(keyfields, row)} for row in rows]

        for state in states:
            keyfields, rows = self._pop_experiments_with_status(state)
            rows = get_dict_for_keyfields_and_rows(keyfields, rows)
            if rows:
                self.fill_table(fixed_parameter_combinations=rows)
        logging.info(f"{len(rows)} experiments with status {' '.join(list(states))} were reset")

    def _pop_experiments_with_status(self, status: Optional[str] = None) -> Tuple[List[str], List[List]]:
        if status == ExperimentStatus.ALL.value:
            condition = None
        else:
            condition = f"WHERE status = '{status}'"

        column_names, entries = self._get_experiments_with_condition(condition)
        self._delete_experiments_with_condition(condition)
        return column_names, entries

    def _get_experiments_with_condition(self, condition: Optional[str] = None) -> Tuple[List[str], List[List]]:
        def _get_keyfields_from_columns(column_names, entries):
            df = pd.DataFrame(entries, columns=column_names)
            keyfields = utils.get_keyfield_names(self.config)
            entries = df[keyfields].values.tolist()
            return keyfields, entries

        connection = self.connect()
        cursor = self.cursor(connection)

        query_condition = condition or ''
        self.execute(cursor, f"SELECT * FROM {self.table_name} {query_condition}")
        entries = self.fetchall(cursor)
        column_names = self.get_structure_from_table(cursor)
        column_names, entries = _get_keyfields_from_columns(column_names, entries)

        return column_names, entries

    def _delete_experiments_with_condition(self, condition: Optional[str] = None) -> None:
        connection = self.connect()
        cursor = self.cursor(connection)

        query_condition = condition or ''
        self.execute(cursor, f'DELETE FROM {self.table_name} {query_condition}')
        self.commit(connection)
        self.close_connection(connection)

    @abc.abstractmethod
    def get_structure_from_table(self, cursor):
        pass

    def execute_queries(self, queries: List[str]):
        connection = self.connect()
        cursor = self.cursor(connection)
        for query in queries:
            self.execute(cursor, query[0], tuple(query[1]))
        self.commit(connection)
        self.close_connection(connection)

    def delete_table(self) -> None:
        connection = self.connect()
        cursor = self.cursor(connection)
        for logtable_name in utils.extract_logtables(self.config, self.table_name).keys():
            self.execute(cursor, f'DROP TABLE IF EXISTS {logtable_name}')
        if self.use_codecarbon:
            self.execute(cursor, f'DROP TABLE IF EXISTS {self.table_name}_codecarbon')

        self.execute(cursor, f'DROP TABLE IF EXISTS {self.table_name}')
        self.commit(connection)

    def get_logtable(self, logtable_name: str) -> pd.DataFrame:
        return self.get_table(f'{self.table_name}__{logtable_name}')

    def get_codecarbon_table(self) -> pd.DataFrame:
        return self.get_table(f'{self.table_name}_codecarbon')

    def get_table(self, table_name: Optional[str] = None) -> pd.DataFrame:
        connection = self.connect()
        query = f"SELECT * FROM {self.table_name}" if table_name is None else f"SELECT * FROM {table_name}"
        #suppress warning for pandas
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            df = pd.read_sql(query, connection)
        self.close_connection(connection)
        return df
