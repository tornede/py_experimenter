import socket
import sys
import traceback
from configparser import NoSectionError
from typing import List
import logging
from random import shuffle

import utils as utils
import concurrent.futures
from database_connector import DatabaseConnector
from result_processor import ResultProcessor


class PyExperimenter:
    """
    Module to automatically execute experiments.
    """

    def __init__(self, config_path='config/configuration.cfg') -> None:
        """
        Initialize PyExperimenter with the configuration file.

        :param config_path: Path to the configuration file.
        """

        # load and check config for mandatory fields
        self._config = utils.load_config(config_path)

        if not self._valid_configuration():
            logging.error("Configuration file invalid")
            sys.exit()

        # connect to database
        self._dbconnector = DatabaseConnector(self._config)

        logging.info('Initialized and connected to database')

    def _valid_configuration(self):
        if not {'host', 'user', 'database', 'password', 'table'}.issubset(set(self._config.options('DATABASE'))):
            return False
        if not {'cpu.max', 'keyfields',
                'resultfields'}.issubset(set(self._config.options('PY_EXPERIMENTER'))):
            return False

        return True

    def fill_table(self, individual_parameters: List[dict] = None, parameters: dict = None) -> None:
        """
        Create (if not exist) and fill table in database with parameter combinations. If there are already entries in
        the table, only parameter combinations for which there is no entry in the database will be added. The status
        of this parameter combination is set to 'created'.

        :param own_paramerters: List of dictionaries of parameters
        to be written to the database instead of using the combinations of parameter domains from the configuration.
        """

        logging.debug("Create table if not exist")
        self._dbconnector.create_table_if_not_exists()
        logging.debug("Fill table with parameters")
        self._dbconnector.fill_table(individual_parameters=individual_parameters, parameters=parameters)
        logging.debug("Parameters successfully inserted to table")

    def execute(self, approach, max_experiments: int = -1, random_order=False) -> None:
        """
        Execute all parameter combinations from the database with status 'created'. If the execution was successful,
        the results will be written in the database. Any errors that occur during execution are also written to the
        database. After execution, the status of the instance is set to 'done', or 'error'.

        :param approach: Function to execute an experiment.
        :param max_experiments: Max number of experiments to execute.
        :param random_order:  Execute experiments in a random order.
        """

        logging.info("Start execution of approaches...")
        # load parameters (approach input) and results fields (approach output)
        parameters = self._dbconnector.get_parameters_to_execute()

        # generate random permutation of parameters
        if random_order:
            shuffle(parameters)

        # execute at most max_experiments (negative values -> execute all)
        if 0 <= max_experiments < len(parameters):
            parameters = parameters[:max_experiments]

        # read result fields from config
        result_fields = utils.get_field_names(self._config['PY_EXPERIMENTER']['resultfields'].split(', '))

        # read cpu.max
        try:
            cpus = int(self._config['PY_EXPERIMENTER']['cpu.max'])
        except ValueError:
            logging.error('Error in config file: cpu.max must be integer')
            sys.exit()

        # read database credentials
        table_name, host, user, database, password = utils.extract_db_credentials_and_table_name_from_config(
            self._config)
        db_credentials = dict(host=host, user=user, database=database, password=password)

        # initialize ResultProcessor for each experiment
        result_processors = [ResultProcessor(dbcredentials=db_credentials, table_name=table_name, condition=p,
                                             result_fields=result_fields) for p in parameters]

        # initialize approach and custom configuration part for each experiment
        approaches = [approach for _ in parameters]

        try:
            custom_config = [dict(self._config.items('CUSTOM')) for _ in parameters]
        except NoSectionError:
            custom_config = None

        # execution pool
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpus) as executor:

            # execute approach by using the execution wrapper and pass parameters and result_processor
            executor.map(execution_wrapper, approaches, custom_config, parameters, result_processors)

        logging.info("All executions finished")


def execution_wrapper(approach, custom_config: dict, parameters, result_processor: ResultProcessor):
    # before running the experiment, check again if it has not already been run
    if result_processor._not_executed_yet():

        # change status to running and set process id
        result_processor._change_status('running')
        result_processor._set_machine(socket.gethostname())

        try:
            # execute user approach
            logging.debug(f"Start of approach on process {socket.gethostname()}")
            approach(parameters, result_processor, custom_config)


            # TODO: Error?
        except Exception:
            error_msg = traceback.format_exc()
            logging.error(error_msg)
            result_processor._write_error(error_msg)
            result_processor._change_status('error')

        else:
            # set status to done
            result_processor._change_status('done')


