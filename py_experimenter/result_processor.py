import logging
import time
from configparser import ConfigParser
from copy import deepcopy
from typing import Dict, List, Tuple

from codecarbon.output import EmissionsData

import py_experimenter.utils as utils
from py_experimenter.config import CodeCarbonCfg, DatabaseCfg
from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.exceptions import (
    InvalidConfigError,
    InvalidLogFieldError,
    InvalidResultFieldError,
)


class ResultProcessor:
    """
    Class for processing the results from an experiment. Use this class whenever you want to write results to the
    database.
    """

    def __init__(self, database_config: DatabaseCfg, db_connector: DatabaseConnector, experiment_id: int, logger, stagger_logging: bool = False, log_every_n_seconds: int = None):
        self.logger = logger
        self.database_config = database_config
        self.db_connector = db_connector
        self.experiment_id = experiment_id
        self.experiment_id_condition = f"ID = {self.experiment_id}"
        self.stagger_logging = stagger_logging
        self.log_every_n_seconds = log_every_n_seconds
        self.last_log_time = time.time()
        self.log_queries = []
        self.log_counter = 0

        if self.stagger_logging:
            if self.log_every_n_seconds is None or not isinstance(self.log_every_n_seconds, int):
                raise ValueError("log_every_n_seconds must be set to an integer when stagger_logging is True")
            if self.log_every_n_seconds <= 0:
                raise ValueError("log_every_n_seconds must be greater than 0 when stagger_logging is True")

    def process_results(self, results: Dict) -> None:
        """
        Process results from the experiment and write them to the database. You can call this method, whenever you
        want to write results to the database.
        :param results: Dictionary with result field name and result value pairs.
        """
        if not self._valid_result_fields(list(results.keys())):
            invalid_result_keys = set(list(results.keys())) - set(self.database_config.resultfields)
            logging.error(
                f"The resultsfileds `{','.join(invalid_result_keys)}` are invalid since they are not mentioned in the config file and therefore not in the database."
            )
            raise InvalidResultFieldError(f"Invalid result keys: {invalid_result_keys}. See previous logs for more information.")

        if self.database_config.result_timestamps:
            results = self.__class__._add_timestamps_to_results(results)

        self.db_connector.update_database(self.database_config.table_name, values=results, condition=self.experiment_id_condition)

    def _write_emissions(self, emission_data: EmissionsData, offline_mode: bool) -> None:
        emission_data["offline_mode"] = offline_mode
        emission_data["experiment_id"] = self.experiment_id

        keys = list(utils.extract_codecarbon_columns().keys())

        # Add experiment_id to keys
        keys.append("experiment_id")
        values = emission_data.values()
        values = [value if not value == "" else None for value in values]
        statement = self.db_connector.prepare_write_query(f"{self.database_config.table_name}_codecarbon", keys)
        self.db_connector.execute_queries([(statement, values)])

    @staticmethod
    def _add_timestamps_to_results(results: Dict) -> List[Tuple[str, object]]:
        time = utils.get_timestamp_representation()
        result_fields_with_timestep = deepcopy(results)
        for result_field, value in sorted(results.items()):
            result_fields_with_timestep[result_field] = value
            result_fields_with_timestep[f"{result_field}_timestamp"] = time
        return result_fields_with_timestep

    def process_logs(self, logs: Dict[str, Dict[str, str]], force_write: bool = False) -> None:
        """
        Appends logs to the logtables. Raises InvalidLogFieldError if the given logs are invalid.
        The logs are of the following structure: Dictionary keys are the logtable_names (without the prefix `table_name__`). Each key refers to a inner dictionary
        with the keys as columnsnames and values as results. The logs are first collected and then written to the database jointly. To that end at every call to
        this method, it is checked if the time since the last write is greater than the log_every_n_seconds. If so, the logs are written to the database. 
        If force_write is True, or when the result_processor is closed, the logs are written to the database.

        :param logs: Logs to be appended to the logtables.
        :type logs: Dict[str, Dict[str, str]]
        """
        if not self._valid_logtable_logs(logs):
            raise InvalidLogFieldError("Invalid logtable entries. See logs for more information")

        time = utils.get_timestamp_representation()
        for logtable_identifier, log_entries in logs.items():
            logtable_name = f"{self.database_config.table_name}__{logtable_identifier}"
            log_entries["experiment_id"] = str(self.experiment_id)
            log_entries["timestamp"] = f"{time}"
            stmt = self.db_connector.prepare_write_query(logtable_name, log_entries.keys())
            self.log_queries.append((stmt, log_entries.values()))

        self.write_logs(force_write)

    def write_logs(self, force_write: bool = False) -> None:
        # Determine if we should write logs now
        if force_write:
            should_write = True
        elif self.stagger_logging:
            time_since_last_write = time.time() - self.last_log_time
            should_write = time_since_last_write >= self.log_every_n_seconds
        else:
            should_write = True
            
        # Write logs if conditions are met
        if should_write and self.log_queries:
            self.db_connector.execute_queries(self.log_queries)
            self.log_queries = []
            self.last_log_time = time.time()


    def _valid_logtable_logs(self, logs: Dict[str, Dict[str, str]]) -> bool:
        logs = {f"{self.database_config.table_name}__{logtable_name}": logtable_entries for logtable_name, logtable_entries in logs.items()}
        if set(logs.keys()) > set(self.database_config.logtables.keys()):
            self.logger.error(f"Logtables `{set(logs.keys()) - set(self.database_config.logtables.keys())}` are not valid logtables.")
            return False

        for logtable_name, logtable_entries in logs.items():
            for column, _ in logtable_entries.items():
                if column not in self.database_config.logtables[logtable_name]:
                    self.logger.error(f"Column `{column}` is not a valid column for logtable `{logtable_name}`")
                    return False
        return True

    def _change_status(self, status: str):
        values = {"status": status, "end_date": utils.get_timestamp_representation()}
        self.db_connector.update_database(self.database_config.table_name, values=values, condition=self.experiment_id_condition)

    def _write_error(self, error_msg):
        self.db_connector.update_database(self.database_config.table_name, {"error": error_msg}, condition=self.experiment_id_condition)

    def _set_machine(self, machine_id):
        self.db_connector.update_database(self.database_config.table_name, {"machine": machine_id}, condition=self.experiment_id_condition)

    def _set_name(self, name):
        self.db_connector.update_database(self.database_config.table_name, {"name": name}, condition=self.experiment_id_condition)

    def _valid_result_fields(self, result_fields):
        return set(result_fields).issubset(set(self.database_config.resultfields))
