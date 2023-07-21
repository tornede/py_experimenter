import logging
from configparser import ConfigParser
from copy import deepcopy
from typing import Dict, List, Tuple

from codecarbon.output import EmissionsData

import py_experimenter.utils as utils
from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.exceptions import InvalidConfigError, InvalidLogFieldError, InvalidResultFieldError


class ResultProcessor:
    """
    Class for processing the results from an experiment. Use this class whenever you want to write results to the
    database.
    """

    def __init__(self, config: ConfigParser, use_codecarbon: bool, codecarbon_config: ConfigParser, credential_path, table_name: str, experiment_id: int, logger):
        self._logger = logger
        self._table_name = table_name
        self._config = config
        self._timestamp_on_result_fields = utils.timestamps_for_result_fields(self._config)
        self._experiment_id = experiment_id
        self._experiment_id_condition = f'ID = {self._experiment_id}'

        self.use_codecarbon = use_codecarbon
        self._codecarbon_config = codecarbon_config

        if config['PY_EXPERIMENTER']['provider'] == 'sqlite':
            self._dbconnector: DatabaseConnector = DatabaseConnectorLITE(config, self.use_codecarbon, self._codecarbon_config, logger)
        elif config['PY_EXPERIMENTER']['provider'] == 'mysql':
            self._dbconnector: DatabaseConnector = DatabaseConnectorMYSQL(
                config, self.use_codecarbon, self._codecarbon_config, credential_path, logger)
        else:
            raise InvalidConfigError("Invalid database provider!")

        self._result_fields = utils.get_result_field_names(self._config)
        self._logtable_fields = utils.extract_logtables(config, table_name)

    def process_results(self, results: Dict) -> None:
        """
        Process results from the experiment and write them to the database. You can call this method, whenever you
        want to write results to the database.
        :param results: Dictionary with result field name and result value pairs.
        """
        if not self._valid_result_fields(list(results.keys())):
            invalid_result_keys = set(list(results.keys())) - set(self._result_fields)
            logging.error(
                f"The resultsfileds `{','.join(invalid_result_keys)}` are invalid sinceare not mentioned in the config file and therefore not in the database.")
            raise InvalidResultFieldError(f"Invalid result keys: {invalid_result_keys}. See previous logs for more information.")

        if self._timestamp_on_result_fields:
            results = self.__class__._add_timestamps_to_results(results)

        self._dbconnector.update_database(self._table_name, values=results, condition=self._experiment_id_condition)

    def _write_emissions(self, emission_data: EmissionsData, offline_mode: bool) -> None:
        emission_data['offline_mode'] = offline_mode
        emission_data['experiment_id'] = self._experiment_id

        keys = utils.extract_codecarbon_columns(with_type=False)
        values = emission_data.values()
        values = [value if not value == '' else None for value in values]
        statement = self._dbconnector.prepare_write_query(f'{self._table_name}_codecarbon', keys)
        self._dbconnector.execute_queries([(statement, values)])

    @staticmethod
    def _add_timestamps_to_results(results: Dict) -> List[Tuple[str, object]]:
        time = utils.get_timestamp_representation()
        result_fields_with_timestep = deepcopy(results)
        for result_field, value in sorted(results.items()):
            result_fields_with_timestep[result_field] = value
            result_fields_with_timestep[f"{result_field}_timestamp"] = time
        return result_fields_with_timestep

    def process_logs(self, logs: Dict[str, Dict[str, str]]) -> None:
        """
        Appends logs to the logtables. Raises InvalidLogFieldError if the given logs are invalid.
        The logs are of the following structure: Dictionary keys are the logtable_names (without the prefix `table_name__`). Each key refers to a inner dictionary
        with the keys as columnsnames and values as results.

        :param logs: Logs to be appended to the logtables. 
        :type logs: Dict[str, Dict[str, str]]
        """
        if not self._valid_logtable_logs(logs):
            raise InvalidLogFieldError("Invalid logtable entries. See logs for more informaiton")

        queries = []
        time = utils.get_timestamp_representation()
        for logtable_identifier, log_entries in logs.items():
            logtable_name = f'{self._table_name}__{logtable_identifier}'
            log_entries['experiment_id'] = str(self._experiment_id)
            log_entries['timestamp'] = f"{time}"
            stmt = self._dbconnector.prepare_write_query(logtable_name, log_entries.keys())
            queries.append((stmt, log_entries.values()))
        self._dbconnector.execute_queries(queries)

    def _valid_logtable_logs(self, logs: Dict[str, Dict[str, str]]) -> bool:
        logs = {f"{self._table_name}__{logtable_name}": logtable_entries for logtable_name, logtable_entries in logs.items()}
        if not set(logs.keys()) <= set(self._logtable_fields.keys()):
            self._logger.error(f'Logtabes `{set(logs.keys()) - set(self._logtable_fields.keys())}` are not valid logtables.')
            return False

        for logtable_name, logtable_entries in logs.items():
            for column, _ in logtable_entries.items():
                if column not in [column[0] for column in self._logtable_fields[logtable_name]]:
                    self._logger.error(f'Column `{column}` is not a valid column for logtable `{logtable_name}`')
                    return False
        return True

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
