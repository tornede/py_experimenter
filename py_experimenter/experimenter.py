import logging
import os
import socket
import traceback
from typing import Callable, Dict, List, Optional, Tuple, Union

import pandas as pd
from codecarbon import EmissionsTracker, OfflineEmissionsTracker
from joblib import Parallel, delayed

from py_experimenter import utils
from py_experimenter.config import PyExperimenterCfg
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.exceptions import (
    InvalidConfigError,
    NoExperimentsLeftException,
)
from py_experimenter.experiment_status import ExperimentStatus
from py_experimenter.result_processor import ResultProcessor


class PyExperimenter:
    """
    Module handling the initialization, execution and collection of experiments and their respective results.
    """

    def __init__(
        self,
        experiment_configuration_file_path: str = os.path.join("config", "experiment_configuration.yml"),
        database_credential_file_path: str = os.path.join("config", "database_credentials.yml"),
        use_ssh_tunnel: bool = False,
        table_name: str = None,
        database_name: str = None,
        use_codecarbon: bool = True,
        name="PyExperimenter",
        logger_name: str = "py-experimenter",
        log_level: Union[int, str] = logging.INFO,
        log_file: str = "./logs/py-experimenter.log",
    ):
        """
        Initializes the PyExperimenter with the given information. If no loger `logger_name` exists, a new logger
        is created with the given `logger_name` and `log_level`.

        :param experiment_configuration_file_path: The path to the experiment configuration file. Defaults to
            'config/experiment_configuration.yml'.
        :type experiment_configuration_file_path: str, optional
        :param database_credential_file_path: The path to the database configuration file storing the credentials
            for the database connection, i.e., host, user and password. Defaults to 'config/database_credentials.cfg'.
        :type database_credential_file_path: str, optional
        :param use_ssh_tunnel: If the used dataabse is sqlite this parameter is ignored Otherwise: If the database is mysql,
            and `use_ssh_tunnel == True` the ssh credentials provided in `database_credential_file_path` used to establish
            a ssh tunnel to the database. If `use_ssh_tunnel == True` but no ssh credentials are provided in
            `database_credential_file_path`, no ssh tunnel is established. Defaults to True.
        :type use_ssh_tunnel: bool
        :param table_name: The name of the database table, if given it will overwrite the table_name given in the
            `experiment_configuration_file_path`. If None, the table table name is taken from the experiment
            configuration file. Defaults to None.
        :type table_name: str, optional
        :param database_name: The name of the database, if given it will overwrite the database_name given in the
            `experiment_configuration_file_path`. If None, the database name is taken from the experiment configuration
            file. Defaults to None.
        :type database_name: str, optional
        :param use_codecarbon: If True, the carbon emissions are tracked and stored in the database. Defaults to True.
        :type use_codecarbon: bool, optional
        :param name: The name of the PyExperimenter, which will be logged in the according column in the database table.
            Defaults to 'PyExperimenter'.
        :type name: str, optional
        :param logger_name: The name of the logger. Defaults to 'py-experimenter'.
        :type logger_name: str
        :param log_level: The log level of the logger. Defaults to logging.INFO.
        :type log_level: Union[int,str]
        :param log_file: The path to the log file. Defaults to "./py_experimenter.log".
        :type log_file: str
        :raises InvalidConfigError: If either the experiment or database configuration are missing mandatory information.
        :raises ValueError: If an unsupported or unknown database connection provider is given.
        """
        # If the logger is not allready craeted, create it with the given name and level
        self.logger_name = logger_name

        logger_initialization_needed = self.logger_name not in logging.root.manager.loggerDict.keys()
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)

        if logger_initialization_needed:
            if not os.path.exists("logs"):
                os.makedirs("logs")

            formatter = logging.Formatter("%(asctime)s  | %(name)s - %(levelname)-8s | %(message)s")

            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            handler = logging.FileHandler(log_file)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.config = PyExperimenterCfg.extract_config(experiment_configuration_file_path, logger=self.logger)

        self.use_codecarbon = use_codecarbon

        if not self.config.valid():
            raise InvalidConfigError("Invalid configuration")

        self.database_credential_file_path = database_credential_file_path
        self.use_ssh_tunnel = use_ssh_tunnel

        if table_name is not None:
            self.config.database_configuration.table_name = table_name
        if database_name is not None:
            self.config.database_configuration.database_name = database_name
        self.name = name

        self.experiment_configuration_file_path = experiment_configuration_file_path

        if self.config.database_configuration.provider == "sqlite":
            self.db_connector = DatabaseConnectorLITE(self.config.database_configuration, self.use_codecarbon, self.logger)
        elif self.config.database_configuration.provider == "mysql":
            self.db_connector = DatabaseConnectorMYSQL(
                self.config.database_configuration, self.use_codecarbon, database_credential_file_path, use_ssh_tunnel, self.logger
            )
        else:
            raise ValueError("The provider indicated in the config file is not supported")

        self.logger.info("Initialized and connected to database")

    def close_ssh(self) -> None:
        """
        Closes the ssh tunnel if it is used.
        """
        if self.config.database_configuration.provider == "mysql" and self.use_ssh_tunnel:
            self.db_connector.close_ssh_tunnel()
        else:
            self.logger.warning("No ssh tunnel to close")

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
        rows = utils.combine_fill_table_parameters(self.config.database_configuration.keyfields.keys(), parameters, fixed_parameter_combinations)
        self.db_connector.create_table_if_not_existing()
        self.db_connector.fill_table(rows)

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
        self.db_connector.create_table_if_not_existing()
        parameters = self.config.database_configuration.get_experiment_configuration()
        self.db_connector.fill_table(parameters)

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
        self.db_connector.create_table_if_not_existing()
        self.db_connector.fill_table(rows)

    def execute(
        self,
        experiment_function: Callable[[Dict, Dict, ResultProcessor], Optional[ExperimentStatus]],
        random_order: bool = False,
        n_jobs: Optional[int] = None,
        max_experiments: int = -1,
    ) -> None:
        """
        Pulls open experiments from the database table and executes them.

        First as many processes are created and started as specified with `n_jobs` in the experiment configuration file.
        If `n_jobs` is not given, a single process is created.

        Each process sequentially pulls and executes experiments from the database table, until all processes executed as
        many experiments as defined by `max_experiments`. If `max_experiments == -1` all experiments will be executed.

        By default the order execution is determined by the id, but if `random_order` is set to `True`, the order is
        determined randomly.

        After pulling an experiment, `experiment_function` is executed with keyfield values of the pulled open
        experiment and the experiments status is set to `running`. Results can be continuously written to the database
        during the execution via `ResultProcessor` that is given as parameter to `experiment_function`. If the execution
        was successful (returns `None` or `ExperimentStatus.Done.`), the status of the corresponding experiment is set to `done`.
        Otherwise, if an error occurred (error raised or `ExperimentStatus.Error` returned), the status is changed to  `error`
        and, in case an error occured, it is logged into the database table. Alternatively the experiment can be paused by returning
        `ExperimentStatus.PAUSED`. In this case the status of the experiment is set to `paused` and the experiment
        can be unpaused and executed again with the `unpause_experiment` method.

        To pause the experiment the `experiment_function` can return `ExperimentStatus.PAUSED`. In this case the
        status of the experiment is set to `paused` and the experiment can be unpaused and executed again with the
        `unpause_experiment` method.

        Note that only errors raised within `experiment_function` are logged in to the database table. Therefore all
        errors raised before or after the execution of `experiment_function` are logged according to the local
        logging configuration and do not appear in the table.

        :param experiment_function: The function that should be executed with the different parametrizations.
        :type experiment_function:  Callable[[Dict, Dict, ResultProcessor], Optional[ExperimentStatus]]
        :param max_experiments: The number of experiments to be executed by this `PyExperimenter`. If all experiments
            should be executed, set this to `-1`. Defaults to `-1`.
        :type max_experiments: int, optional
        :param random_order: If True, the order of the experiments is determined randomly. Defaults to False.
        :type random_order: bool, optional
        :param n_jobs: The number parallel processes that should be created and started. If None, the number is taken
            from the experiment configuration file. Defaults to None.
        :type n_jobs: int, optional
        :raises InvalidValuesInConfiguration: If any value of the experiment parameters is of wrong data type.
        """
        if n_jobs is None:
            n_jobs = self.config.n_jobs

        self._write_codecarbon_config()

        with Parallel(n_jobs=n_jobs) as parallel:
            if max_experiments == -1:
                parallel(delayed(self._worker)(experiment_function, random_order) for _ in range(n_jobs))
            else:
                parallel(delayed(self._execution_wrapper)(experiment_function, random_order) for _ in range(max_experiments))
        self.logger.info("All configured executions finished.")

        self._delete_codecarbon_config()

    def unpause_experiment(self, experiment_id: int, experiment_function: Callable) -> None:
        """
        Pulls the experiment with the given `experiment_id` from the database (if it is `paused`) table and executes it. In
        this context "executing" means that the given `experiment_function` is executed with the keyfield values of the pulled experiment.

        After pulling the experiment its status is changed to `running` before and changed to `done` after the
        execution of `experiment_function` if no error occurred. If the function tries to pull an experiment that is
        not in the `paused` state, an error is raised.

        :raises NoPausedExperimentsException if there are no paused experiment with id `experiment_id`.
        :param experiment_id: _description_ The id of the experiment to be executed.
        :type experiment_id: int
        :param experiment_function: _description_ The experiment function to use to continue the given experiment
        :type experiment_function: Callable
        """
        self._write_codecarbon_config()

        keyfield_dict, _ = self.db_connector.pull_paused_experiment(experiment_id)
        self._execute_experiment(experiment_id, keyfield_dict, experiment_function)

        self._delete_codecarbon_config()

    def _worker(self, experiment_function: Callable[[Dict, Dict, ResultProcessor], None], random_order: bool) -> None:
        """
        Worker that repeatedly pulls open experiments from the database table and executes them.

        :param experiment_function: The function that should be executed with the different parametrizations.
        :type experiment_function: Callable[[Dict, Dict, ResultProcessor], None]
        :param random_order: If True, the order of the experiments is determined randomly. Defaults to False.
        :type random_order: bool
        """
        while True:
            try:
                self._execution_wrapper(experiment_function, random_order)
            except NoExperimentsLeftException:
                break

    def _execution_wrapper(
        self, experiment_function: Callable[[Dict, Dict, ResultProcessor], Optional[ExperimentStatus]], random_order: bool
    ) -> None:
        """
        Executes the given `experiment_function` on one open experiment. To that end, one of the open experiments is pulled
        from the database table. Then `experiment_function` is executed on the keyfield values of the pulled experiment.

        Thereby, the status of the experiment is continuously updated. The experiment can have the following states:

        * `running` when the experiment has been pulled from the database table, which will be executed directly afterwards.
        * `error` if an exception was raised during the execution of the experiment.
        * `done` if the execution of the experiment has finished successfully.
        * `paused` if the experiment was paused during the execution.

        Errors raised during the execution of `experiment_function` are logged to the `error` column in the database table.
        Note that only errors raised within `experiment_function` are logged in to the database table. Therefore all errors
        raised before or after the execution of `experiment_function` are logged according to the local logging configuration
        and do not appear in the table. Additionally errors due to returning `ExperimentStatus.ERROR` are not logged.

        :param experiment_function: The function that should be executed with the different parametrizations.
        :type experiment_function: Callable[[dict, dict, ResultProcessor], None]
        :param random_order: If True, the order of the experiments is determined randomly. Defaults to False.
        :type random_order: bool
        :raises NoExperimentsLeftError: If there are no experiments left to be executed.
        :raises DatabaseConnectionError: If an error occurred during the connection to the database.
        """
        experiment_id, keyfield_values = self.db_connector.get_experiment_configuration(random_order)
        self._execute_experiment(experiment_id, keyfield_values, experiment_function)

    def _execute_experiment(self, experiment_id, keyfield_values, experiment_function):
        result_processor = ResultProcessor(self.config.database_configuration, self.db_connector, experiment_id=experiment_id, logger=self.logger)
        result_processor._set_name(self.name)
        result_processor._set_machine(socket.gethostname())

        if self.use_codecarbon:
            if self.codecarbon_offline_mode:
                if "country_iso_code" not in self.config.codecarbon_configuration.config:
                    raise InvalidConfigError(
                        (
                            "CodeCarbon offline mode requires a `country_iso_code` in the config file."
                            "For more information see `https://mlco2.github.io/codecarbon/index.html`."
                        )
                    )
                tracker = OfflineEmissionsTracker()
            else:
                tracker = EmissionsTracker()

        try:
            self.logger.debug(f"Start of experiment_function on process {socket.gethostname()}")
            if self.use_codecarbon:
                tracker.start()
            final_status = experiment_function(keyfield_values, result_processor, self.config.custom_configuration.custom_values)
            if final_status not in (None, ExperimentStatus.DONE, ExperimentStatus.ERROR, ExperimentStatus.PAUSED):
                raise ValueError(f"Invalid final status {final_status}")

        except Exception:
            error_msg = traceback.format_exc()
            self.logger.error(error_msg)
            result_processor._write_error(error_msg)
            result_processor._change_status(ExperimentStatus.ERROR.value)
        else:
            if final_status is None or final_status == ExperimentStatus.DONE:
                result_processor._change_status(ExperimentStatus.DONE.value)
            elif final_status == ExperimentStatus.ERROR:
                result_processor._change_status(ExperimentStatus.ERROR.value)
            elif final_status == ExperimentStatus.PAUSED:
                result_processor._change_status(ExperimentStatus.PAUSED.value)
        finally:
            if self.use_codecarbon:
                tracker.stop()
                emission_data = tracker._prepare_emissions_data().values
                result_processor._write_emissions(emission_data, self.codecarbon_offline_mode)

    def _write_codecarbon_config(self) -> None:
        """ "
        Writes the CodeCarbon config file if CodeCarbon is used in this experiment.
        """
        if self.use_codecarbon:
            if "offline_mode" in self.config.codecarbon_configuration.config:
                self.codecarbon_offline_mode = self.config.codecarbon_configuration.config["offline_mode"]
            else:
                self.codecarbon_offline_mode = False
                self.config.codecarbon_configuration.config["offline_mode"] = False
            utils.write_codecarbon_config(self.config.codecarbon_configuration.config)

    def _delete_codecarbon_config(self) -> None:
        """
        Deletes the CodeCarbon config file if CodeCarbon is used in this experiment.
        """
        if self.use_codecarbon:
            try:
                os.remove(".codecarbon.config")
            except FileNotFoundError as e:
                self.logger.error(f"Could not delete CodeCarbon config file. Error: {e}")

    def reset_experiments(self, *states: Tuple["str"]) -> None:
        """
        Deletes the experiments from the database table that have the given `states`. Afterward, all deleted rows are added to the
        table again.

        :param states: The status of experiments that should be reset. Either `created`, `running`, `error`, `done`, or `all`.
        Note that `states` is a variable-length argument, so multiple states can be given as a tuple.
        :type status: Tuple[str]
        """
        if not states:
            self.logger.warning("No states given to reset experiments. No experiments are reset.")
        else:
            self.db_connector.reset_experiments(*states)

    def delete_table(self) -> None:
        """
        Drops the table defined in the configuration file. Additionally, all associated log tables are dropped.
        """
        self.db_connector.delete_table()

    def get_table(self) -> pd.DataFrame:
        """
        Returns the database table as `Pandas.DataFrame`.

        :return: The database table as `Pandas.DataFrame`.
        :rtype: pd.DataFrame
        """
        return self.db_connector.get_table()

    def get_logtable(self, logtable_name: str) -> pd.DataFrame:
        """
        Returns the log table as `Pandas.DataFrame`.

        :param table_name: The name of the log table.
        :type table_name: str
        :return: The log table as `Pandas.DataFrame`.
        :rtype: pd.DataFrame
        """
        return self.db_connector.get_logtable(logtable_name)

    def get_codecarbon_table(self) -> pd.DataFrame:
        """
        Returns the CodeCarbon table as `Pandas.DataFrame`. If CodeCarbon is not used in this experiment, an error is raised.

        :raises ValueError: If CodeCarbon is not used in this experiment.
        :return: Returns the CodeCarbon table as `Pandas.DataFrame`.
        :rtype: pd.DataFrame
        """
        if self.use_codecarbon:
            return self.db_connector.get_codecarbon_table()
        else:
            raise ValueError("CodeCarbon is not used in this experiment.")
