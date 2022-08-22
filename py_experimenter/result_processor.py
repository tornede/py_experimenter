import logging
from datetime import datetime
from typing import List

from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.py_experimenter_exceptions import InvalidConfigError, InvalidResultFieldError

result_logger = logging.getLogger('result_logger')
result_logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')

file_handler = logging.FileHandler('result.log')
file_handler.setFormatter(formatter)
result_logger.addHandler(file_handler)


class ResultProcessor:
    """
    Class for processing the results from an experiment. Use this class whenever you want to write results to the
    database.
    """

    def __init__(self, config: dict, credential_path, table_name: str, condition: dict, result_fields: List[str]):
        self.table_name = table_name
        self._where = ' AND '.join([f"{str(key)}='{str(value)}'" for key, value in condition.items()])
        self._result_fields = result_fields

        if config['DATABASE']['provider'] == 'sqlite':
            self._dbconnector = DatabaseConnectorLITE(config)
        elif config['DATABASE']['provider'] == 'mysql':
            self._dbconnector = DatabaseConnectorMYSQL(config, credential_path)
        else:
            raise InvalidConfigError("Invalid database provider!")

    def process_results(self, results: dict) -> None:
        """
        Process results from the experiment and write them to the database. You can call this method, whenever you
        want to write results to the database.
        :param results: Dictionary with result field name and result value pairs.
        """

        result_fields = list(results.keys())
        result = list(results.values())
        if not self._valid_result_fields(result_fields):
            invalid_result_keys = set(result_fields) - set(self._result_fields)
            raise InvalidResultFieldError(f"Invalid result keys: {invalid_result_keys}")

        self._dbconnector._update_database(keys=result_fields, values=result, where=self._where)

    def _change_status(self, status):
        time = datetime.now()
        time = time.strftime("%m/%d/%Y, %H:%M:%S")

        if status == 'running':
            self._dbconnector._update_database(keys=['status', 'start_date'], values=["running", time],
                                               where=self._where)

        if status == 'done' or status == 'error':
            self._dbconnector._update_database(keys=['status', 'end_date'], values=[status, time], where=self._where)

    def _write_error(self, error_msg):
        self._dbconnector._update_database(keys=['error'], values=[error_msg], where=self._where)

    def _set_machine(self, machine_id):
        self._dbconnector._update_database(keys=['machine'], values=[machine_id], where=self._where)

    def _not_executed_yet(self) -> bool:
        return self._dbconnector.not_executed_yet(where=self._where)

    def _valid_result_fields(self, result_fields):
        return set(result_fields).issubset(set(self._result_fields))
