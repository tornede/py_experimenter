import logging
from configparser import ConfigParser
from copy import deepcopy
from typing import Dict, List, Tuple

from codecarbon.output import EmissionsData

import py_experimenter.utils as utils
from py_experimenter.database_connector import DatabaseConnector
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

    def __init__(self, config: ConfigParser, use_codecarbon: bool, codecarbon_config: ConfigParser, credential_path, table_name: str, result_fields: List[str], experiment_id: int):
        self._table_name = table_name
        self._result_fields = result_fields
        self._config = config
        self._timestamp_on_result_fields = utils.timestamps_for_result_fields(self._config)
        self._experiment_id = experiment_id
        self._experiment_id_condition = f'ID = {self._experiment_id}'

        self.use_codecarbon = use_codecarbon
        self._codecarbon_config = codecarbon_config

        if config['PY_EXPERIMENTER']['provider'] == 'sqlite':
            self._dbconnector: DatabaseConnector = DatabaseConnectorLITE(config, self.use_codecarbon, self._codecarbon_config)
        elif config['PY_EXPERIMENTER']['provider'] == 'mysql':
            self._dbconnector: DatabaseConnector = DatabaseConnectorMYSQL(config, self.use_codecarbon, self._codecarbon_config, credential_path)
        else:
            raise InvalidConfigError("Invalid database provider!")

    def process_results(self, results: dict) -> None:
        """
        Process results from the experiment and write them to the database. You can call this method, whenever you
        want to write results to the database.
        :param results: Dictionary with result field name and result value pairs.
        """
        if not self._valid_result_fields(list(results.keys())):
            invalid_result_keys = set(list(results.keys())) - set(self._result_fields)
            raise InvalidResultFieldError(f"Invalid result keys: {invalid_result_keys}")

        if self._timestamp_on_result_fields:
            results = self.__class__._add_timestamps_to_results(results)

        self._dbconnector.update_database(self._table_name, values=results, condition=self._experiment_id_condition)

    def _write_emissions(self, emission_data: EmissionsData, offline_mode: bool) -> None:
        emission_data['offline_mode'] = offline_mode
        emission_data['experiment_id'] = self._experiment_id

        keys = utils.extract_codecarbon_columns(with_type = False)
        values = emission_data.values()
        values = [value if not value == '' else None for value in values]
        statement = self._dbconnector.prepare_write_query(f'{self._table_name}_codecarbon', keys)
        self._dbconnector.execute_queries([(statement, values)])

    @staticmethod
    def _add_timestamps_to_results(results: dict) -> List[Tuple[str, object]]:
        time = utils.get_timestamp_representation()
        result_fields_with_timestep = deepcopy(results)
        for result_field, value in sorted(results.items()):
            result_fields_with_timestep[result_field] = value
            result_fields_with_timestep[f"{result_field}_timestamp"] = time
        return result_fields_with_timestep

    def process_logs(self, logs: Dict[str, Dict[str, str]]) -> None:
        queries = []
        time = utils.get_timestamp_representation()
        for logtable_identifier, log_entries in logs.items():
            logtable_name = f'{self._table_name}__{logtable_identifier}'
            log_entries['experiment_id'] = str(self._experiment_id)
            log_entries['timestamp'] = f"{time}"
            stmt = self._dbconnector.prepare_write_query(logtable_name, log_entries.keys())
            queries.append((stmt, log_entries.values()))
        self._dbconnector.execute_queries(queries)

    def _change_status(self, status: str):
        values = {'status': status,
                  'end_date': utils.get_timestamp_representation()}
        self._dbconnector.update_database(self._table_name, values=values, condition=self._experiment_id_condition)

    def _write_error(self, error_msg):
        self._dbconnector.update_database(self._table_name, {'error': error_msg}, condition=self._experiment_id_condition)

    def _set_machine(self, machine_id):
        self._dbconnector.update_database(self._table_name, {'machine': machine_id}, condition=self._experiment_id_condition)

    def _set_name(self, name):
        self._dbconnector.update_database(self._table_name, {'name': name}, condition=self._experiment_id_condition)

    def _valid_result_fields(self, result_fields):
        return set(result_fields).issubset(set(self._result_fields))
