import abc
import logging
from functools import reduce
from operator import concat
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from py_experimenter import utils
from py_experimenter.config import DatabaseCfg, Keyfield
from py_experimenter.exceptions import (CreatingTableError, DatabaseConnectionError, EmptyFillDatabaseCallError, NoExperimentsLeftException,
                                        NoPausedExperimentsException, TableHasWrongStructureError)
from py_experimenter.experiment_status import ExperimentStatus


class DatabaseConnector(abc.ABC):
    def __init__(self, database_configuration: DatabaseCfg, use_codecarbon: bool, logger: logging.Logger):
        self.logger = logger
        self.database_configuration = database_configuration

        self.use_codecarbon = use_codecarbon
        self._test_connection()

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
            raise DatabaseConnectionError(f"error \n{e}\n raised when closing connection to database.")

    def commit(self, connection) -> None:
        try:
            connection.commit()
        except Exception as e:
            raise DatabaseConnectionError(f"error \n{e}\n raised when committing to database.")

    def execute(self, cursor, sql_statement, values=None) -> None:
        try:
            if values is None:
                self.logger.debug(f"Executing sql statement: {sql_statement}")
                cursor.execute(sql_statement)
            else:
                self.logger.debug(f"Executing sql statement: {sql_statement} with prepared statement values: {values}")
                cursor.execute(sql_statement, values)
        except Exception as e:
            raise DatabaseConnectionError(f"error \n{e}\n raised when executing sql statement.")

    def cursor(self, connection):
        try:
            return connection.cursor()
        except Exception as e:
            raise DatabaseConnectionError(f"error \n{e}\n raised when creating cursor.")

    def fetchall(self, cursor):
        try:
            return cursor.fetchall()
        except Exception as e:
            raise DatabaseConnectionError(f"error \n{e}\n raised when fetching all rows from database.")

    def create_table_if_not_existing(self) -> None:
        self.logger.debug("Create table if not exist")

        connection = self.connect()
        cursor = self.cursor(connection)
        if self._table_exists(cursor):
            if not self._table_has_correct_structure(cursor, {**self.database_configuration.keyfields, **self.database_configuration.resultfields}):
                raise TableHasWrongStructureError(
                    "Keyfields or resultfields from the configuration do not match columns in the existing "
                    "table. Please change your configuration or delete the table in your database."
                )
        else:
            columns = self._compute_columns(self.database_configuration.keyfields, self.database_configuration.resultfields)
            self._create_table(cursor, columns, self.database_configuration.table_name)

            for logtable_name, logtable_columns in self.database_configuration.logtables.items():
                self._create_table(cursor, logtable_columns, logtable_name, table_type="logtable")

            if self.use_codecarbon:
                codecarbon_columns = utils.extract_codecarbon_columns()
                self._create_table(cursor, codecarbon_columns, f"{self.database_configuration.table_name}_codecarbon", table_type="codecarbon")

        self.close_connection(connection)

    @abc.abstractmethod
    def _table_exists(self, cursor, table_name: str):
        pass

    @staticmethod
    def _compute_columns(keyfields: Dict["str", Keyfield], resultfields: Dict["str", "str"]) -> Dict["str", "str"]:
        keyfields = {value.name: value.dtype for value in keyfields.values()}
        metadata_values = {
            "creation_date": "DATETIME",
            "status": "VARCHAR(255)",
            "start_date": "DATETIME",
            "name": "LONGTEXT",
            "machine": "VARCHAR(255)",
        }
        final_values = {
            "end_date": "DATETIME",
            "error": "LONGTEXT",
        }
        return {**keyfields, **metadata_values, **resultfields, **final_values}

    def _exclude_fixed_columns(self, columns: List[str]) -> List[str]:
        columns.remove("ID")
        columns.remove("creation_date")
        columns.remove("status")
        columns.remove("start_date")
        columns.remove("name")
        columns.remove("machine")
        columns.remove("end_date")
        columns.remove("error")
        return columns

    def _create_table(self, cursor, columns: List[Tuple["str"]], table_name: str, table_type: str = "standard"):
        query = self._get_create_table_query(columns, table_name, table_type)
        try:
            self.execute(cursor, query)
        except Exception as err:
            raise CreatingTableError(f"Error when creating table: {err}")

    def _get_create_table_query(self, columns: List[Tuple["str"]], table_name: str, table_type: str = "standard"):
        columns = ["%s %s DEFAULT NULL" % (field, datatype) for field, datatype in columns.items()]
        columns = ",".join(columns)
        query = f"CREATE TABLE {table_name} (ID INTEGER PRIMARY KEY {self.get_autoincrement()}"
        if table_type == "standard":
            query += f", {columns}"
        elif table_type == "logtable":
            query += f", experiment_id INTEGER, timestamp DATETIME, {columns}, FOREIGN KEY (experiment_id) REFERENCES {self.database_configuration.table_name}(ID) ON DELETE CASCADE"
        elif table_type == "codecarbon":
            query += f", experiment_id INTEGER, {columns}, FOREIGN KEY (experiment_id) REFERENCES {self.database_configuration.table_name}(ID) ON DELETE CASCADE"
        else:
            raise ValueError(f"Unknown table type: {table_type}")
        return query + ");"

    @abc.abstractstaticmethod
    def get_autoincrement(self):
        pass

    @abc.abstractmethod
    def _table_has_correct_structure(self, cursor, typed_fields):
        pass

    def fill_table(self, combinations) -> None:
        self.logger.debug("Fill table with parameters.")

        if len(combinations) == 0:
            raise EmptyFillDatabaseCallError("No combinations to execute found.")

        column_names = list(self.database_configuration.keyfields.keys())
        self.logger.debug("Getting existing rows.")
        existing_rows = self._get_existing_rows(column_names)
        time = utils.get_timestamp_representation()

        rows_skipped = 0
        rows = []
        self.logger.debug("Checking which of the experiments to be inserted already exist.")
        for combination in combinations:
            if self._check_combination_in_existing_rows(combination, existing_rows):
                rows_skipped += 1
                continue
            combination = self._add_metadata(combination, time)
            rows.append(combination)

        if rows:
            self.logger.debug(f"Now adding {len(rows)} rows to database. {rows_skipped} rows were skipped.")
            self._write_to_database(rows)
            self.logger.info(f"{len(rows)} rows successfully added to database. {rows_skipped} rows were skipped.")
        else:
            self.logger.info(f"No rows to add. All the {len(combinations)} experiments already exist.")

    def add_experiment(self, combination: Dict[str, str]) -> None:
        existing_rows = self._get_existing_rows(list(self.database_configuration.keyfields.keys()))
        if self._check_combination_in_existing_rows(combination, existing_rows):
            self.logger.info("Experiment already exists in database. Skipping.")
            return

        connection = self.connect()
        try:
            cursor = self.cursor(connection)
            combination = self._add_metadata(combination, utils.get_timestamp_representation(), ExperimentStatus.CREATED_FOR_EXECUTION.value)
            insert_query = self._get_insert_query(self.database_configuration.table_name, list(combination.keys()))
            self.execute(cursor, insert_query, list(combination.values()))
            cursor.execute(f"SELECT {self._last_insert_id_string()};")
            experiment_id = cursor.fetchone()[0]
            self.commit(connection)
        except Exception as e:
            raise DatabaseConnectionError(f"error \n{e}\n raised when adding experiment to database.")
        finally:
            self.close_connection(connection)
        return experiment_id

    def _get_insert_query(self, table_name: str, columns: List[str]) -> str:
        return f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join([self._prepared_statement_placeholder] * len(columns))})"

    @abc.abstractmethod
    def _last_insert_id_string(self) -> str:
        pass

    def _add_metadata(
        self,
        combination: Dict[str, Any],
        time: str,
        status: ExperimentStatus = ExperimentStatus.CREATED.value,
    ) -> Dict[str, Any]:
        combination["creation_date"] = time
        combination["status"] = status
        return combination

    def _check_combination_in_existing_rows(self, combination, existing_rows) -> bool:
        if combination in existing_rows:
            return True
        return False

    @abc.abstractmethod
    def _get_existing_rows(self, column_names) -> List[str]:
        pass

    def get_experiment_configuration(self, random_order: bool) -> Tuple[int, Dict[str, Any]]:
        try:
            experiment_id, description, values = self._pull_open_experiment(random_order)
        except IndexError as e:
            raise NoExperimentsLeftException("No experiments left to execute")
        except Exception as e:
            raise DatabaseConnectionError(f"error \n {e} raised. \n Please check if fill_table() was called correctly.")

        return experiment_id, dict(zip([i[0] for i in description], *values))

    @abc.abstractmethod
    def _pull_open_experiment(self, random_order) -> Tuple[int, List, List]:
        pass

    def _select_open_experiments_from_db(self, connection, cursor, random_order: bool) -> Tuple[int, List, List]:
        if random_order:
            order_by = self.random_order_string()
        else:
            order_by = "id"

        time = utils.get_timestamp_representation()

        self.execute(cursor, self._get_pull_experiment_query(order_by))
        experiment_id = self.fetchall(cursor)[0][0]
        self.execute(
            cursor,
            f"UPDATE {self.database_configuration.table_name} SET status = {self._prepared_statement_placeholder}, start_date = {self._prepared_statement_placeholder} WHERE id = {self._prepared_statement_placeholder};",
            (ExperimentStatus.RUNNING.value, time, experiment_id),
        )
        keyfields = ",".join(list(self.database_configuration.keyfields.keys()))
        self.execute(cursor, f"SELECT {keyfields} FROM {self.database_configuration.table_name} WHERE id = {experiment_id};")
        values = self.fetchall(cursor)
        self.commit(connection)
        description = cursor.description
        return experiment_id, description, values

    @abc.abstractstaticmethod
    def random_order_string():
        pass

    @abc.abstractmethod
    def _get_pull_experiment_query(self, order_by: str):
        return f"SELECT `id` FROM {self.database_configuration.table_name} WHERE status = 'created' ORDER BY {order_by} LIMIT 1"

    def _write_to_database(self, combinations: List[Dict[str, str]]) -> None:
        columns = list(combinations[0].keys())
        values = [list(combination.values()) for combination in combinations]
        prepared_statement_palcehodler = ",".join([f"({', '.join([self._prepared_statement_placeholder] * len(columns))})"] * len(combinations))

        stmt = f"INSERT INTO {self.database_configuration.table_name} ({','.join(columns)}) VALUES {prepared_statement_palcehodler}"
        values = reduce(concat, values)
        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, stmt, values)
        self.commit(connection)
        self.close_connection(connection)

    def pull_paused_experiment(self, experiment_id: int) -> Dict[str, Any]:
        connnection = self.connect()
        cursor = self.cursor(connnection)
        keyfields = ",".join(list(self.database_configuration.keyfields.keys()))
        query = f"SELECT {keyfields} FROM {self.database_configuration.table_name} WHERE id = {self._prepared_statement_placeholder} AND status = {self._prepared_statement_placeholder};"
        self.execute(cursor, query, (experiment_id, ExperimentStatus.PAUSED.value))
        keyfield_values = self.fetchall(cursor)
        if keyfield_values:
            description = cursor.description
            query = f"UPDATE {self.database_configuration.table_name} SET status = {self._prepared_statement_placeholder} WHERE id = {self._prepared_statement_placeholder};"
            self.execute(cursor, query, (ExperimentStatus.RUNNING.value, experiment_id))
            self.commit(connnection)
            self.close_connection(connnection)
            keyfield_dict = dict(zip([i[0] for i in description], *keyfield_values))
            return keyfield_dict, description
        else:
            self.close_connection(connnection)
            raise NoPausedExperimentsException(f"There is no paused experiment with id {experiment_id} in the table.")

    def prepare_write_query(self, table_name: str, keys) -> str:
        return f"INSERT INTO {table_name} ({', '.join(keys)}) VALUES ({','.join([self._prepared_statement_placeholder] * len(keys))})"

    def update_database(self, table_name: str, values: Dict[str, Union[str, int, object]], condition: str):
        connection = self.connect()
        cursor = self.cursor(connection)
        self.execute(cursor, self._prepare_update_query(table_name, values.keys(), condition), list(values.values()))
        self.commit(connection)
        self.close_connection(connection)

    def _prepare_update_query(self, table_name: str, values: Dict[str, Union[str, int, object]], condition: str) -> str:
        return f"UPDATE {table_name} SET {', '.join(f'{key} = {self._prepared_statement_placeholder}' for key in values)}" f" WHERE {condition}"

    def reset_experiments(self, *states: str) -> None:
        def get_dict_for_keyfields_and_rows(keyfields: List[str], rows: List[List[str]]) -> List[dict]:
            return [{key: value for key, value in zip(keyfields, row)} for row in rows]

        for state in states:
            keyfields, rows = self._pop_experiments_with_status(state)
            rows = get_dict_for_keyfields_and_rows(keyfields, rows)
            if rows:
                self.fill_table(rows)
        self.logger.info(f"{len(rows)} experiments with status {' '.join(list(states))} were reset")

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
            keyfields = self.database_configuration.keyfields.keys()
            entries = df[keyfields].values.tolist()
            return keyfields, entries

        connection = self.connect()
        cursor = self.cursor(connection)

        query_condition = condition or ""
        self.execute(cursor, f"SELECT * FROM {self.database_configuration.table_name} {query_condition}")
        entries = self.fetchall(cursor)
        column_names = self.get_structure_from_table(cursor)
        column_names, entries = _get_keyfields_from_columns(column_names, entries)

        return column_names, entries

    def _delete_experiments_with_condition(self, condition: Optional[str] = None) -> None:
        connection = self.connect()
        cursor = self.cursor(connection)

        query_condition = condition or ""
        self.execute(cursor, f"DELETE FROM {self.database_configuration.table_name} {query_condition}")
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
        for logtable_name in self.database_configuration.logtables.keys():
            self.execute(cursor, f"DROP TABLE IF EXISTS {logtable_name}")
        if self.use_codecarbon:
            self.execute(cursor, f"DROP TABLE IF EXISTS {self.database_configuration.table_name}_codecarbon")

        self.execute(cursor, f"DROP TABLE IF EXISTS {self.database_configuration.table_name}")
        self.commit(connection)
        self.close_connection(connection)

    def get_logtable(self, logtable_name: str) -> pd.DataFrame:
        return self.get_table(f"{self.database_configuration.table_name}__{logtable_name}")

    def get_codecarbon_table(self) -> pd.DataFrame:
        return self.get_table(f"{self.database_configuration.table_name}_codecarbon")

    def get_table(self, table_name: Optional[str] = None) -> pd.DataFrame:
        connection = self.connect()
        query = f"SELECT * FROM {self.database_configuration.table_name}" if table_name is None else f"SELECT * FROM {table_name}"
        # suppress warning for pandas
        import warnings

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            df = pd.read_sql(query, connection)
        self.close_connection(connection)
        return df
