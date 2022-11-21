import logging
from copy import deepcopy
from datetime import datetime
from typing import List, Tuple

import py_experimenter.utils as utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.exceptions import InvalidConfigError, InvalidResultFieldError

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

    def __init__(self, _config: dict, credential_path, table_name: str, condition: dict, result_fields: List[str]):
        self._table_name = table_name
        self._where = ' AND '.join([f"{str(key)}='{str(value)}'" for key, value in condition.items()])
        self._result_fields = result_fields
        self._config = _config
        self._timestamp_on_result_fields = utils.timestamps_for_result_fields(self._config)

        if _config['PY_EXPERIMENTER']['provider'] == 'sqlite':
            self._dbconnector = DatabaseConnectorLITE(_config)
        elif _config['PY_EXPERIMENTER']['provider'] == 'mysql':
            self._dbconnector = DatabaseConnectorMYSQL(_config, credential_path)
        else:
            raise InvalidConfigError("Invalid database provider!")

    def process_results(self, results: dict) -> None:
        """
        Process results from the experiment and write them to the database. You can call this method, whenever you
        want to write results to the database.
        :param results: Dictionary with result field name and result value pairs.
        """
        time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        if not self._valid_result_fields(list(results.keys())):
            invalid_result_keys = set(list(results.keys())) - set(self._result_fields)
            raise InvalidResultFieldError(f"Invalid result keys: {invalid_result_keys}")

        if self._timestamp_on_result_fields:
            results = self.__class__._add_timestamps_to_results(results, time)

        keys = self._dbconnector.escape_sql_chars(*list(results.keys()))
        values = self._dbconnector.escape_sql_chars(*list(results.values()))
        self._dbconnector._update_database(keys=keys, values=values, where=self._where)

    @staticmethod
    def _add_timestamps_to_results(results: dict, time: datetime) -> List[Tuple[str, object]]:
        result_fields_with_timestep = deepcopy(results)
        for result_field, value in sorted(results.items()):
            result_fields_with_timestep[result_field] = value
            result_fields_with_timestep[f"{result_field}_timestamp"] = time
        return result_fields_with_timestep

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

    def _set_name(self, name):
        self._dbconnector._update_database(keys=['name'], values=[name], where=self._where)

    def _not_executed_yet(self) -> bool:
        return self._dbconnector.not_executed_yet(where=self._where)

    def _valid_result_fields(self, result_fields):
        return set(result_fields).issubset(set(self._result_fields))
