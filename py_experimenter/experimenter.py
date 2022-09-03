import concurrent.futures
import configparser
import logging
import os
import socket
import traceback
from configparser import NoSectionError
from random import shuffle
from typing import List

import pandas as pd

from py_experimenter import utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.py_experimenter_exceptions import InvalidConfigError, InvalidValuesInConfiguration
from py_experimenter.result_processor import ResultProcessor


class PyExperimenter:
    """
    Module that connects the execution of different machine learning experiments with a database.
    """

    def __init__(self,
                 config_file: str = os.path.join('config', 'configuration.cfg'),
                 credential_path: str = os.path.join('config', 'database_credentials.cfg'),
                 table_name: str = None,
                 database_name: str = None,
                 name='PyExperimenter'):
        """
        Initialize PyExperimenter with the configuration file. If table_name or database_name are given they overwrite the
        values in the configuration file.

        :param config_file: Path to the configuration file. Defaults to 'config/configuration.cfg'.
        :param table_name: Name of the table in the database. If None, the table name is taken from the configuration file. Defaults to None.
        :param database_name: Name of the database. If None, the database name is taken from the configuration file. Defaults to None.
        """
        self._config = utils.load_config(config_file)
        self._credential_path = credential_path
        if not PyExperimenter._valid_configuration(self._config, credential_path):
            raise InvalidConfigError('Invalid configuration')

        if table_name is not None:
            self._config.set('PY_EXPERIMENTER', 'table', table_name)
        if database_name is not None:
            self._config.set('PY_EXPERIMENTER', 'database', database_name)
        self.name= name

        self._config_file = config_file
        self.timestamp_on_result_fields = utils.timestamps_for_result_fields(self._config)

        if self._config['PY_EXPERIMENTER']['provider'] == 'sqlite':
            self._dbconnector = DatabaseConnectorLITE(self._config)
        elif self._config['PY_EXPERIMENTER']['provider'] == 'mysql':
            self._dbconnector = DatabaseConnectorMYSQL(self._config, credential_path)
        else:
            raise ValueError('The provider indicated in the config file is not supported')

        logging.info('Initialized and connected to database')

    def set_config_value(self, section_name: str, key: str, value: str) -> None:
        """
        Sets a value in the configuration file. If the section does not exist, it is created.
        :param section_name: Name of the section in the configuration file.
        :param key: Name of the key in the configuration file.
        :param value: Value to set.
        """
        if not self._config.has_section(section_name):
            self._config.add_section(section_name)
        self._config.set(section_name, key, value)
        PyExperimenter._valid_configuration(self._config, self._credential_path)

    def get_config_value(self, section_name: str, key: str) -> str:
        return self._config.get(section_name, key)

    def has_option(self, section_name: str, key: str) -> bool:
        return self._config.has_option(section_name, key)

    @ staticmethod
    def _valid_configuration(_config: configparser, credential_path=None) -> bool:
        """
        This method checks if the configuration is valid.
        """
        if not _config.has_section('PY_EXPERIMENTER'):
            return False

        if set(_config.keys()) > {'PY_EXPERIMENTER', 'CUSTOM', 'DEFAULT'}:
            return False
    
        if not {'provider', 'database', 'table'}.issubset(set(_config.options('PY_EXPERIMENTER'))):
            logging.error('Error in config file: DATABASE section must contain provider, database, and table')
            return False

        if _config['PY_EXPERIMENTER']['provider'] not in ['sqlite', 'mysql']:
            logging.error('Error in config file: DATABASE provider must be either sqlite or mysql')
            return False

        if _config['PY_EXPERIMENTER']['provider'] == 'mysql':
            credentials = utils.load_config(credential_path)
            if not {'host', 'user', 'password'}.issubset(set(credentials.options('CREDENTIALS'))):
                logging.error(
                    f'Error in config file: DATABASE section must contain host, user, and password since provider is {_config["DATABASE"]["provider"]}')
                return False

        if not {'cpu.max', 'keyfields',
                'resultfields'}.issubset(set(_config.options('PY_EXPERIMENTER'))):
            return False
        return True

    def fill_table_from_combination(self, fixed_parameter_combinations: List[dict] = None, parameters: dict = None) -> None:
        """
        Create (if not exist) and fill table in database with parameter combinations. If there are already entries in
        the table, only parameter combinations for which there is no entry in the database will be added. The status
        of this parameter combination is set to 'created'.

        The combinations are calculated as follows: the cartesian product of the parameters and fixed_parameter_combinations.
        parameter1 X parameter2 X {fixed_parameter_combination1, fixed_parameter_combination2, ...}

        If the combinations of fixed_parameter_combinations, parameters, and config_parameters do not match the
        keyfields given in the config file, an error is raised.

        param parameters: Dictionary with parameters that are used for the cartesian product
        param fixed_parameter_combinations: List of fixed parameter combinations.
        """

        self._dbconnector.create_table_if_not_existing()
        self._dbconnector.fill_table(fixed_parameter_combinations=fixed_parameter_combinations,
                                     parameters=parameters)
        

    def fill_table_from_config(self) -> None:
        """
        Create (if not exist) and fill table in database with parameter combinations. If there are already entries in
        the table, only parameter combinations for which there is no entry in the database will be added. The status
        of this parameter combination is set to 'created'.
        """
        self._dbconnector.create_table_if_not_existing()
        parameters = utils.get_keyfield_data(self._config)
        self._dbconnector.fill_table(parameters=parameters)

    def fill_table_with_rows(self, rows: List[dict]) -> None:
        self._dbconnector.create_table_if_not_existing()
        keyfield_names = utils.get_keyfield_names(self._config)
        for row in rows:
            if set(keyfield_names) != set(row.keys()):
                raise ValueError('The keyfields in the config file do not match the keyfields in the rows')
        self._dbconnector.fill_table(fixed_parameter_combinations=rows)

    def execute(self, approach, max_experiments: int = -1, random_order=False) -> None:
        """
        Execute approach for max_experiment parameter combinations that are in the database and have status 'created'.
        If the execution was successful, the status is changed to done and the results are written into the database. 
        If an errors that occurs during execution the status is changed to error and the error is written into the database.

        :param approach: Function to execute an experiment.
        :param max_experiments: Max number of experiments to execute. If max_experiments is -1, all experiments are executed.
        :param random_order:  Execute experiments in a random order.
        """

        logging.info("Start execution of approaches...")
        keyfield_values = self._dbconnector.get_keyfield_values_to_execute()

        if random_order:
            shuffle(keyfield_values)

        if 0 <= max_experiments < len(keyfield_values):
            keyfield_values = keyfield_values[:max_experiments]
        result_field_names = utils.get_result_field_names(self._config)
        try:
            cpus = int(self._config['PY_EXPERIMENTER']['cpu.max'])
        except ValueError:
            raise InvalidValuesInConfiguration('cpu.max must be an integer')
        table_name = self.get_config_value('PY_EXPERIMENTER', 'table')
        result_processors = [ResultProcessor(self._config, self._credential_path, table_name=table_name, condition=p,
                                             result_fields=result_field_names) for p in keyfield_values]
        approaches = [approach for _ in keyfield_values]
        try:
            custom_fields = [dict(self._config.items('CUSTOM')) for _ in keyfield_values]
        except NoSectionError:
            custom_fields = [None for _ in keyfield_values]

        with concurrent.futures.ProcessPoolExecutor(max_workers=cpus) as executor:
            executor.map(self.execution_wrapper, approaches, custom_fields, keyfield_values, result_processors)
        logging.info("All executions finished")

    def get_table(self) -> pd.DataFrame:
        return self._dbconnector.get_table()

    def execution_wrapper(self, approach, custom_fields: dict, keyfields, result_processor: ResultProcessor):
        if result_processor._not_executed_yet():
            result_processor._change_status('running')
            result_processor._set_name(self.name)
            result_processor._set_machine(socket.gethostname())
            try:
                logging.debug(f"Start of approach on process {socket.gethostname()}")
                approach(keyfields, result_processor, custom_fields)
            except Exception:
                error_msg = traceback.format_exc()
                logging.error(error_msg)
                result_processor._write_error(error_msg)
                result_processor._change_status('error')
            else:
                result_processor._change_status('done')

    def reset_experiments(self, status= 'error') -> None:        
        keyfields,entries = self._dbconnector.delete_experiments_with_status(status)
        rows = self._extract_row_from_entries(keyfields, entries)
        if rows:
            self.fill_table_with_rows(rows)
        logging.info(f"{len(rows)} experiments with status {status} were reset")
        
    def _extract_row_from_entries(self, keyfields, entries):
        return [{k:value for k,value in zip(keyfields, entry)}
                for entry in entries]

    