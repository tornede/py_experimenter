import abc
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd

from py_experimenter import utils
from py_experimenter.exceptions import DatabaseConnectionError, EmptyFillDatabaseCallError, NoExperimentsLeftException, TableHasWrongStructureError
from py_experimenter.experiment_status import ExperimentStatus


class DatabaseConnector(abc.ABC):

    def __init__(self, database_credential_file_path):
        self.database_credential_file_path = database_credential_file_path
        self.table_name = self.database_credential_file_path.get('PY_EXPERIMENTER', 'table')
        self.database_name = self.database_credential_file_path.get('PY_EXPERIMENTER', 'database')

        self.database_credentials = self._extract_credentials()
        self.timestamp_on_result_fields = utils.timestamps_for_result_fields(self.database_credential_file_path)

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
        logging.debug("Create table if not exist")

        keyfields = utils.get_keyfields(self.database_credential_file_path)
        resultfields = utils.get_resultfields(self.database_credential_file_path)

        if self.timestamp_on_result_fields:
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
        amount_of_keyfields = len(utils.get_keyfield_names(self.database_credential_file_path))
        amount_of_result_fields = len(utils.get_result_field_names(self.database_credential_file_path))

        if self.timestamp_on_result_fields:
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

        keyfield_names = utils.get_keyfield_names(self.database_credential_file_path)
        combinations = utils.combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations)

        if len(combinations) == 0:
            raise EmptyFillDatabaseCallError("No combinations to execute found.")

        column_names = ','.join(combinations[0].keys())

        existing_rows = self._get_existing_rows(column_names)

        column_names += ",status"
        column_names += ",creation_date"

        time = datetime.now()
        values_added = 0
        for combination in combinations:
            if self._check_combination_in_existing_rows(combination, existing_rows, keyfield_names):
                continue
            values = list(combination.values())
            values.append(ExperimentStatus.CREATED.value)
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

    def get_experiment_configuration(self, random_order: bool):
        try:
            experiment_id, description, values = self._pull_open_experiment(random_order)
        except IndexError as e:
            raise NoExperimentsLeftException("No experiments left to execute")
        except Exception as e:
            raise DatabaseConnectionError(f'error \n {e} raised. \n Please check if fill_table() was called correctly.')

        return experiment_id, dict(zip([i[0] for i in description], *values))

    def _execute_queries(self, connection, cursor, random_order) -> Tuple[int, List, List]:
        if random_order:
            order_by = self.__class__.random_order_string()
        else:
            order_by = "id"
            
        self.execute(cursor, f"SELECT id FROM {self.table_name} WHERE status = 'created' ORDER BY {order_by} LIMIT 1;")
        experiment_id = self.fetchall(cursor)[0][0]
        self.execute(cursor, f"UPDATE {self.table_name} SET status = '{ExperimentStatus.RUNNING.value}' WHERE id = {experiment_id};")
        keyfields = ','.join(utils.get_keyfield_names(self.database_credential_file_path))
        self.execute(cursor, f"SELECT {keyfields} FROM {self.table_name} WHERE id = {experiment_id};")
        values = self.fetchall(cursor)
        self.commit(connection)
        description = cursor.description
        return experiment_id, description, values

    @abc.abstractstaticmethod
    def random_order_string():
        pass

    @abc.abstractmethod
    def _pull_open_experiment(self, random_order) -> Tuple[int, List, List]:
        pass

    def _write_to_database(self, keys, values) -> None:
        keys = ", ".join(keys)
        values = "'" + self.__class__._write_to_database_separator.join([str(value) for value in values]) + "'"

        stmt = f"INSERT INTO {self.table_name} ({keys}) VALUES ({values})"

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
                stmt = f"UPDATE {self.table_name} SET {key}='{value}' WHERE {where}"
                self.execute(cursor, stmt)
            self.commit(connection)

        except Exception as err:
            logging.error(err)
            stmt = """UPDATE %s SET error="%s" WHERE %s""" % (self.table_name, err, where)
            self.execute(cursor, stmt)
            self.commit(connection)
        else:
            self.close_connection(connection)

    def not_executed_yet(self, where) -> bool:
        not_executed = False

        try:
            connection = self.connect()
            cursor = self.cursor(connection)

            stmt = "SELECT status FROM %s WHERE %s" % (self.table_name, where)

            self.execute(cursor, stmt)
            for result in cursor:
                if result[0] == 'created':
                    not_executed = True

        except Exception as err:
            logging.error(err)
        else:
            connection.close()
            return not_executed

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
            keyfields = utils.get_keyfield_names(self.database_credential_file_path)
            entries = df[keyfields].values.tolist()
            return keyfields, entries

        connection = self.connect()
        cursor = self.cursor(connection)

        query_condition= condition or ''
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

    def delete_table(self) -> None:
        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, f'DROP TABLE IF EXISTS {self.table_name}')
        self.commit(connection)

    def get_table(self) -> pd.DataFrame:
        connection = self.connect()
        query = f"SELECT * FROM {self.table_name}"
        df = pd.read_sql(query, connection)
        self.close_connection(connection)
        return df
