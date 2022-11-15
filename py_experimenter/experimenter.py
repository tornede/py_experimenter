import configparser
import logging
import os
import socket
import traceback
from multiprocessing import Manager, Pool, Semaphore
from typing import Callable, Dict, List, Optional

import pandas as pd

from py_experimenter import utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.py_experimenter_exceptions import InvalidConfigError, InvalidValuesInConfiguration, NoExperimentsLeftError
from py_experimenter.result_processor import ResultProcessor


class PyExperimenter:
    """
    Module handling the initialization, execution and collection of experiments and their respective results.
    """

    def __init__(self,
                 experiment_configuration_file_path: str = os.path.join('config', 'configuration.cfg'),
                 database_credential_file_path: str = os.path.join('config', 'database_credentials.cfg'),
                 table_name: str = None,
                 database_name: str = None,
                 name='PyExperimenter'):
        """
        Initializes the PyExperimenter with the given information.

        :param experiment_configuration_file_path: The path to the experiment configuration file. Defaults to 
            'config/configuration.cfg'.
        :type experiment_configuration_file_path: str, optional
        :param database_credential_file_path: The path to the database configuration file storing the credentials 
            for the database connection, i.e., host, user and password. Defaults to 'config/database_credentials.cfg'.
        :type database_credential_file_path: str, optional
        :param table_name: The name of the database table, if given it will overwrite the table_name given in the 
            `experiment_configuration_file_path`. If None, the table table name is taken from the experiment 
            configuration file. Defaults to None.
        :type table_name: str, optional
        :param database_name: The name of the database, if given it will overwrite the database_name given in the 
            `experiment_configuration_file_path`. If None, the database name is taken from the experiment configuration 
            file. Defaults to None.
        :type database_name: str, optional
        :param name: The name of the PyExperimenter, which will be logged in the according column in the database table. 
            Defaults to 'PyExperimenter'.
        :type name: str, optional
        :raises InvalidConfigError: If either the experiment or database configuration are missing mandatory information.
        :raises ValueError: If an unsupported or unknown database connection provider is given.
        """
        self.config = utils.load_config(experiment_configuration_file_path)
        self.database_credential_file_path = database_credential_file_path
        if not PyExperimenter._is_valid_configuration(self.config, database_credential_file_path):
            raise InvalidConfigError('Invalid configuration')

        if table_name is not None:
            self.config.set('PY_EXPERIMENTER', 'table', table_name)
        if database_name is not None:
            self.config.set('PY_EXPERIMENTER', 'database', database_name)
        self.name = name

        self.experiment_configuration_file_path = experiment_configuration_file_path
        self.timestamp_on_result_fields = utils.timestamps_for_result_fields(self.config)

        if self.config['PY_EXPERIMENTER']['provider'] == 'sqlite':
            self.dbconnector = DatabaseConnectorLITE(self.config)
        elif self.config['PY_EXPERIMENTER']['provider'] == 'mysql':
            self.dbconnector = DatabaseConnectorMYSQL(self.config, database_credential_file_path)
        else:
            raise ValueError('The provider indicated in the config file is not supported')

        logging.info('Initialized and connected to database')

    def set_config_value(self, section_name: str, key: str, value: str) -> None:
        """
        Modifies the experiment configuration so that within the given `section_name` the value of the  property identified by
        the given `key` is overwritten, or created if it was not existing beforehand.

        :param section_name: The name of the section of the experiment configuration in which a value should be set.
        :type section_name: str
        :param key: The name of the key identifying the property within the given section whose value should be set.
        :type key: str
        :param value: The value which should be set to the property identified by the given key in the given section.
        :type value: str
        :raises InvalidConfigError: If the modified configuration either misses, or has invalid information.
        """
        if not self.config.has_section(section_name):
            self.config.add_section(section_name)
        self.config.set(section_name, key, value)
        if not PyExperimenter._is_valid_configuration(self.config, self.database_credential_file_path):
            raise InvalidConfigError('Invalid configuration')

    def get_config_value(self, section_name: str, key: str) -> str:
        """
        Returns the value of the property of the experiment configuration identified by the given key. If the `key` 
        is not contained within the section, an exception is raised.

        :param section_name: The name of the section containing the property whose value should be returned.
        :type section_name: str
        :param key: The name of the key identifying the property within the given section of the experiment 
            configuration of which a value should be returned.
        :type key: str
        :return: The value of the property identified by the given key within the section `section_name` of the 
            experiment configuration.
        :rtype: str
        :raises NoOptionError: If the section called `section_name` is not part of the experiment configuration, or 
            the `key` is not contained within that section.
        """
        return self.config.get(section_name, key)

    def has_section(self, section_name: str) -> bool:
        """
        Checks whether the experiment configuration contains a section with the given name.

        :param section_name: The name of the section which should be checked for existence.
        :type section_name: str
        :return: True if the section exists, False otherwise.
        :rtype: bool
        """
        return self.config.has_section(section_name)

    def has_option(self, section_name: str, key: str) -> bool:
        """
        Checks whether the experiment configuration contains a property identified by the given 'key' within the 
        section called 'section_name'.

        :param section_name: The name of the section of the experiment configuration of which the `key` should be 
            checked.
        :type section_name: str
        :param key: The name of the key to check within the given section.
        :type key: str
        :return: True if the given `key` is contained in the experiment configuration within the section called 
            `section_name`. False otherwise.
        :rtype: bool
        """
        return self.config.has_option(section_name, key)

    @ staticmethod
    def _is_valid_configuration(_config: configparser, database_credential_file_path: str = None) -> bool:
        """
        Checks whether the given experiment configuration is valid, i.e., it contains all necessary fields, the database provider
        is either mysql or sqlite, and in case of a mysql database provider, that the database credentials are available.

        :param _config: The experiment configuration.
        :type _config: configparser
        :param database_credential_file_path: The path to the database configuration file, i.e., the file defining 
            the host, user and password. Defaults to None.
        :type database_credential_file_path: str, optional
        :return: True if the experiment configuration contains all necessary fields.
        :rtype: bool
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
            credentials = utils.load_config(database_credential_file_path)
            if not {'host', 'user', 'password'}.issubset(set(credentials.options('CREDENTIALS'))):
                logging.error(
                    f'Error in config file: DATABASE section must contain host, user, and password since provider is {_config["DATABASE"]["provider"]}')
                return False

        if not {'n_jobs', 'keyfields',
                'resultfields'}.issubset(set(_config.options('PY_EXPERIMENTER'))):
            return False
        return True

    def fill_table_from_combination(self, fixed_parameter_combinations: List[dict] = None, parameters: dict = None) -> None:
        """
        Adds rows to the database table based on the given information.

        First the existence of the database table is checked. If it does not exist, the database table is created 
        based on the information in the experiment configuration file the `PyExperimenter` has been initialized 
        with. 

        Afterwards, the database table is filled. To this end, the cartesian product of all `parameters` and the 
        `fixed_parameter_combinations` is built, where each combination will make up a row in the database table.
        Note that only rows are added whose parameter combinations do not already exist in the database table.
        For each added row the status is set to 'created'. If any parameter of the combinations (rows) does not 
        match the keyfields from the experiment configuration, an error is raised. 

        In the following, an example call of this method is given:

        >>> fill_table_from_combination(
        >>>    fixed_parameter_combinations = [ { a:1, a2:2 }, { a:2, a2:4 } ],
        >>>    parameters = { b:[1,2], c:['cat', 'dog']}
        >>> )

        The according table with four columns [a, a2, b, c] is filled with the following rows:

        >>> [
        >>>     { a:1, a2:2, b:1, c:'cat' },
        >>>     { a:1, a2:2, b:1, c:'dog' },
        >>>     { a:1, a2:2, b:2, c:'cat' },
        >>>     { a:1, a2:2, b:2, c:'dog' },
        >>>     { a:2, a2:4, b:1, c:'cat' },
        >>>     { a:2, a2:4, b:1, c:'dog' },
        >>>     { a:2, a2:4, b:2, c:'cat' },
        >>>     { a:2, a2:4, b:2, c:'dog' }
        >>> ]

        :param fixed_parameter_combinations: List of predefined parameter combinations (each of type dict).
                Defaults to None.
        :type fixed_parameter_combinations: List[dict], optional
        :param parameters: Dictionary of parameters and their lists of possible values. Defaults to None.
        :type parameters: dict, optional
        :raises ParameterCombinationError: If any parameter of the combinations (rows) does not match the keyfields 
            from the experiment configuration.
        """
        self.dbconnector.create_table_if_not_existing()
        self.dbconnector.fill_table(fixed_parameter_combinations=fixed_parameter_combinations,
                                    parameters=parameters)

    def fill_table_from_config(self) -> None:
        """
        Adds rows to the database table based on the experiment configuration file.

        First the existence of the database table is checked. If it does not exist, the database table is created 
        based on the information from the experiment configuration file the `PyExperimenter` has been initialized
        with. 

        Afterwards, the database table is filled. To this end, the cartesian product of all `keyfields` from the 
        experiment configuration file is build, where each combination will make up a row in the database table.
        Note that only rows are added whose parameter combinations do not already exist in the table. For each 
        added row the status is set to 'created'. If the `keyfield` values do not match their respective types an 
        error is raised.
        """
        self.dbconnector.create_table_if_not_existing()
        parameters = utils.get_keyfield_data(self.config)
        self.dbconnector.fill_table(parameters=parameters)

    def fill_table_with_rows(self, rows: List[dict]) -> None:
        """
        Adds rows to the database table based on the given list of `rows`.

        First the existence of the database table is checked. If it does not exist, the database table is created 
        based on the information from the experiment configuration file the `PyExperimenter` has been initialized with. 

        Afterwards, the database table is filled with the list of `rows`. Note that only rows are added whose 
        parameter combinations do not already exist in the table. For each added row the status will is to 'created'. 
        If any parameter of `rows` does not match the keyfields from the experiment configuration, an error is 
        raised. 

        :param rows: A list of rows, where each entry is made up of a dict containing a key-value-pair for each 
            `keyfield` of the experiment configuration file.
        :type rows: List[dict]
        :raises ValueError: If any key of any row in `rows` does not match the `keyfields` from the experiment 
            configuration file
        """
        self.dbconnector.create_table_if_not_existing()
        keyfield_names = utils.get_keyfield_names(self.config)
        for row in rows:
            if set(keyfield_names) != set(row.keys()):
                raise ValueError('The keyfields in the config file do not match the keyfields in the rows')
        self.dbconnector.fill_table(fixed_parameter_combinations=rows)

    def execute(self, experiment_function: Callable[[Dict, Dict, ResultProcessor], None],
                max_experiments: int = -1,
                random_order=False) -> None:
        """
        Starts the execution of experiments.

        To that end as many processes as specified in the experiment configuration file are started. The workers' behavior
        is specified in the function `_execution_worker`. Mainly each worker repeatedly calls the function `_execution_wrapper` 
        until either all experiments or `max_experiments` are started. If limited the amount of experiments
        is coordinated via a `multiprocessing.semaphore`.

        In `_execution_wrapper` one of the open experiments is selected from the table and its status is set to running.
        This is done within one transaction to insure that no other process can select the same experiment. An experiment is
        considered to be open if its status is 'created'. In case of `random_order`, the experiment is not selected based on its
        `id`, but randomly.

        After pulling an experiment, the given `experiment_function` is executed on the keyfield values defined in the table.
        Results can be continuously written to the database during the execution via the `ResultProcessor` that is given as 
        parameter to the `experiment_function`. If the execution was successful, the status of the corresponding 
        experiment is set to `done`. Otherwise, if an error occurred during the execution, the status is changed to 
        `error` and the raised error is logged to the database table.
        
        Note that errors that occur before or after the execution of the `experiment_function` are logged via the function
        `_handle_error`.

        :param experiment_function: The function that should be executed with the different parametrizations.
        :type experiment_function: Callable[[dict, dict, ResultProcessor], None]
        :param max_experiments: The number of experiments to be executed by this `PyExperimenter`. If all experiments 
            should be executed, -1 can be used. Defaults to -1. 
        :type max_experiments: int, optional
        :param random_order: Indicates whether the experiments to be executed are chosen consecutively by its experiment 
            ID (`False`) or in a randomized fashion (`True`). Defaults to False.
        :type random_order: bool, optional
        :raises InvalidValuesInConfiguration: If any value of the experiment parameters is of wrong data type.
        """
        try:
            n_jobs = int(self.config['PY_EXPERIMENTER']['n_jobs'])
        except ValueError:
            raise InvalidValuesInConfiguration('n_jobs must be an integer')

        with Manager() as manager:
            if max_experiments != -1:
                semaphore = manager.Semaphore(max_experiments)
            else:
                semaphore = None
            with Pool(n_jobs) as pool:
                for _ in range(n_jobs):
                    pool.apply_async(self._execution_worker, args=(experiment_function, random_order, semaphore),
                                     error_callback=self._handle_error)
                pool.close()
                pool.join()

        logging.info("All executions finished")

    def _execution_worker(self, experiment_function: Callable[[Dict, Dict, ResultProcessor], None], random_order, semaphore: Optional[Semaphore]) -> None:
        """
        Handles the execution of experiments in worker processes.

        Each worker repeatedly executes the function `_execution_wrapper`. When either all experiments or `max_experiments`
        are started, the worker processes are stopped. The `max_experiments` is coordinated via a semaphore.
        
        If an error occurs before or after the execution of the `experiment_function`, the error is logged via the function `_handle_error`.

        :param experiment_function: The function that should be executed with the different parametrizations.
        :type experiment_function: Callable[[dict, dict, ResultProcessor], None]
        :param max_experiments: The number of experiments to be executed by this `PyExperimenter`. If all experiments 
            should be executed, -1 can be used. Defaults to -1. 
        :type max_experiments: int, optional
        :param semaphore: A semaphore that is used to limit the number of experiments that are executed by this `PyExperimenter`.
        :type semaphore: multiprocessing.Semaphore or None
        """
        while True:
            if semaphore is not None:
                experiment_left = semaphore.acquire(blocking=False)
                if not experiment_left:
                    return
            self._execution_wrapper(experiment_function, random_order)

    def _handle_error(self, error: Exception):
        """
        Gets called if an error occurs in a worker process. Simply logs the error.

        :param error: Error that occurred in a worker process.
        :type error: Exception
        """
        logging.error(error)

    def _execution_wrapper(self,
                           experiment_function: Callable[[dict, dict, ResultProcessor], None],
                           random_order: bool) -> None:
        """
        Executes the given `experiment_function` on one experiment. To that end, one of the open experiments is selected (randomly
        if `random_order` = True). Then the `experiment_function` is executed on its keyfield values defined in the table.
        In this function the status of the experiment is continuously updated. The experiment can have the following states:

        * `running` when the execution of the experiment has been started, but not yet finished.
        * `error` if an exception was raised during the execution of the experiment.
        * `done` if the execution of the experiment has finished successfully.

        If an error occurs during the execution of the experiment, it is logged to the `error` column in the table. If an 
        error occurs before or after the execution of the `experiment_function`, it is logged via the function `_handle_error`.

        :param experiment_function: The function that should be executed with the different parametrizations.
        :type experiment_function: Callable[[dict, dict, ResultProcessor], None]
        :param random_order: Indicates whether the experiments to be executed are chosen consecutively by its experiment
                                ID (`False`) or in a randomized fashion (`True`). Defaults to False.
        :type random_order: bool
        :raises NoExperimentsLeftError: If there are no experiments left to be executed.
        :raises DatabaseConnectionError: If an error occurred during the connection to the database.
        """
        result_field_names = utils.get_result_field_names(self.config)
        custom_fields = dict(self.config.items('CUSTOM')) if self.has_section('CUSTOM') else None
        table_name = self.get_config_value('PY_EXPERIMENTER', 'table')

        experiment_id, keyfield_values = self.dbconnector.get_experiment_configuration(random_order)

        result_processor = ResultProcessor(self.config, self.database_credential_file_path, table_name=table_name,
                                           condition=keyfield_values, result_fields=result_field_names)
        result_processor._set_name(self.name)
        result_processor._set_machine(socket.gethostname())
        
        try:
            logging.debug(f"Start of experiment_function on process {socket.gethostname()}")
            experiment_function(keyfield_values, result_processor, custom_fields)
        except Exception:
            error_msg = traceback.format_exc()
            logging.error(error_msg)
            result_processor._write_error(error_msg)
            result_processor._change_status('error')
        else:
            result_processor._change_status('done')

    def reset_experiments(self, status) -> None:
        """
        Deletes the experiments of the database table having the given `status`. Afterwards, all rows that have been 
        deleted from the database table are added to the table again featuring `created` as a status. Experiments 
        to reset can be selected based on the following status: 

        * `created` when the experiment is added to the database table, execution has not started.
        * `running` when the execution of the experiment has been started.
        * `error` if something went wrong during the execution, i.e., an exception is raised
        * `done` if the execution finished successfully.

        :param status: The status of experiments that should be reset.
        :type status: str
        """
        def get_dict_for_keyfields_and_rows(keyfields: List[str], rows: List[List[str]]) -> List[dict]:
            return [{key: value for key, value in zip(keyfields, row)} for row in rows]

        keyfields, rows = self.dbconnector.delete_experiments_with_status(status)
        rows = get_dict_for_keyfields_and_rows(keyfields, rows)
        if rows:
            self.fill_table_with_rows(rows)
        logging.info(f"{len(rows)} experiments with status {status} were reset")

    def get_table(self) -> pd.DataFrame:
        """
        Returns the database table as `Pandas.DataFrame`. 

        :return: The database table as `Pandas.DataFrame`. 
        :rtype: pd.DataFrame
        """
        return self.dbconnector.get_table()
