import logging
from abc import ABC, abstractclassmethod
from logging import Logger
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import omegaconf
from attr import dataclass
from omegaconf import DictConfig, ListConfig, OmegaConf

from py_experimenter import utils
from py_experimenter.exceptions import (
    InvalidColumnError,
    InvalidConfigError,
    InvalidLogtableError,
)


class Cfg(ABC):
    @abstractclassmethod
    def extract_config(self, **kwargs) -> "Cfg":
        """
        Abstract method for extracting the configuration from a given OmegaConf object.
        """

    def valid(self) -> bool:
        """
        Abstract method for checking the validity of the configuration.
        """


@dataclass
class Keyfield:
    name: str
    dtype: str
    values: List[Union[int, str, bool, Any]]


class DatabaseCfg(Cfg):
    """
    Class for the configuration of the database connection. In addition to `provider`, `database_name`, and `table_name`, the class also defined the structure
    of tables in the `keyfields`, `resultfields`, and `logtables` attributes.
    """

    def __init__(
        self,
        provider: str,
        database_name: str,
        table_name: str,
        result_timestamps: bool,
        keyfields: List[Keyfield],
        resultfields: Dict[str, str],
        logtables: Dict[str, Dict[str, str]],
        logger: logging.Logger,
    ) -> None:
        """
        The constructor of the DatabaseCfg class.

        :param provider: Database Provider; either `sqlite` or `mysql`
        :type provider: str
        :param database_name: Name of the database
        :type database_name: str
        :param table_name: Name of the table
        :type table_name: str
        :param keyfields: Definition of table `key_fields`. Each `key_field` is a tuple of the field name and the field type.
        :type keyfields: List[Tuple[str,str]]
        :param resultfields: Definition of table `result_fields`. Each `result_field` is a tuple of the field name and the field type.
        :type resultfields: List[Tuple[str,str]]
        :param logtables: Definition of table `log_tables`. Each `log_table` is a dictionary with the table name as key and the table definition as value,
            where the table definition is a list of tuples of the field name and the field type.
        :type logtables: Dict[str, Dict[str,str]]
        """
        self.provider = provider
        self.database_name = database_name
        self.table_name = table_name
        self.result_timestamps = result_timestamps
        self.keyfields = keyfields
        self.resultfields = resultfields
        self.logtables = logtables

        self.logger = logger

    @staticmethod
    def extract_config(config: OmegaConf, logger: logging.Logger) -> Tuple["DatabaseCfg", List[str]]:
        database_config = config["PY_EXPERIMENTER"]["Database"]
        table_config = database_config["table"]
        provider = database_config["provider"]
        database_name = database_config["database"]
        table_name = database_config["table"]["name"]

        # Extract Keyfields and Resultfields. If no type is given, the default is VARCHAR(255)
        keyfields = DatabaseCfg._extract_keyfields(table_config["keyfields"], logger)

        result_timestamps, resultfields = DatabaseCfg._extract_resultfields(table_config, logger)

        logtables = DatabaseCfg._extract_logtables(table_name, database_config, logger)

        return DatabaseCfg(
            provider,
            database_name,
            table_name,
            result_timestamps,
            keyfields,
            resultfields,
            logtables,
            logger,
        )

    @staticmethod
    def _extract_keyfields(keyfields: DictConfig, logger) -> Dict[str, Keyfield]:
        extracted_keyfields = dict()
        for keyfield_name, keyfield_content in keyfields.items():
            keyfield_type, values = DatabaseCfg._extract_value_range(keyfield_name, keyfield_content, logger)
            extracted_keyfields[keyfield_name] = Keyfield(
                keyfield_name,
                keyfield_type,
                values,
            )

        logger.info(f"Found {len(keyfields)} keyfields")
        return extracted_keyfields

    @staticmethod
    def _extract_value_range(keyfield_name: str, keyfield_content: DictConfig, logger) -> Tuple[str, List[Union[int, str, bool, Any]]]:
        keyfield_type = keyfield_content["type"]
        if "values" not in keyfield_content:
            logger.warning(f"No values given for keyfield {keyfield_name}")
            return keyfield_type, None

        if isinstance(keyfield_content["values"], ListConfig):
            values = list(keyfield_content["values"])

        elif isinstance(keyfield_content["values"], DictConfig):
            if "start" not in keyfield_content["values"] or "stop" not in keyfield_content["values"]:
                raise InvalidColumnError(f"Invalid keyfield values: {keyfield_name}")

            start = keyfield_content["values"]["start"]
            stop = keyfield_content["values"]["stop"]
            if "step" in keyfield_content["values"]:
                step = keyfield_content["values"]["step"]
            else:
                step = 1
            values = np.arange(start, stop, step).tolist()
        return keyfield_type, values

    @staticmethod
    def _extract_resultfields(table_config: OmegaConf, logger) -> Dict[str, str]:
        if "resultfields" not in table_config:
            logger.warning("No resultfields given")
            resultfields = dict()
            return False, resultfields

        if not isinstance(table_config["resultfields"], DictConfig):
            raise InvalidColumnError(f"Invalid resultfields: {table_config['resultfields']}")

        resultfields = dict(table_config["resultfields"])

        if "result_timestamps" in table_config:
            if table_config["result_timestamps"] not in [True, False]:
                raise InvalidColumnError(f"Invalid result_timestamps: {table_config['result_timestamps']}")
            if table_config["result_timestamps"]:
                result_timestamps = True
                new_resultfields = dict()
                for key, value in resultfields.items():
                    new_resultfields[key] = value
                    new_resultfields[f"{key}_timestamp"] = "VARCHAR(255)"
                resultfields = new_resultfields
            else:
                result_timestamps = False
        else:
            result_timestamps = False

        return result_timestamps, resultfields

    @staticmethod
    def _extract_logtables(table_name: str, table_config: OmegaConf, logger: Logger) -> Dict[str, Dict[str, str]]:
        if "logtables" in table_config:
            preliminary_logtables = table_config["logtables"]
            logtables = dict()

            for logtable_name, logtable_definition in preliminary_logtables.items():
                # normal notation - extracting table name, columns and types as above
                if isinstance(logtable_definition, DictConfig):
                    logtables[f"{table_name}__{logtable_name}"] = dict(logtable_definition)

                else:
                    logger.warning(f"Invalid logtable content for {logtable_name}")
                    raise InvalidLogtableError(f"Invalid logtable content for {logtable_name}")
        else:
            logger.warning("No logtables given")
            logtables = dict()

        return logtables

    def get_experiment_configuration(self):
        keyfield_names = [keyfield.name for keyfield in self.keyfields.values()]
        parameters = {keyfield.name: keyfield.values for keyfield in self.keyfields.values()}
        config = utils.combine_fill_table_parameters(keyfield_names, parameters, [])
        return config

    def valid(self) -> bool:
        if self.provider not in ["sqlite", "mysql"]:
            self.logger.error("Database provider must be either sqlite or mysql")
            return False
        if not isinstance(self.database_name, str):
            self.logger.error("Database name must be a string")
            return False
        if not isinstance(self.table_name, str):
            self.logger.error("Table name must be a string")
            return False
        if not isinstance(self.result_timestamps, bool):
            self.logger.error("Result timestamps must be a boolean")
            return False

        if not isinstance(self.keyfields, dict):
            self.logger.error("Keyfields must be a dictionary")
            return False
        else:
            for keyfield, keyfield_type in self.keyfields.items():
                if not isinstance(keyfield, str):
                    self.logger.error("Keyfield name must be a string")
                    return False
                if not isinstance(keyfield_type, Keyfield):
                    self.logger.error("Keyfield type must be of type Keyfield")
                    return False
        if not isinstance(self.resultfields, dict):
            self.logger.error("Resultfields must be a dictionary")
            return False
        else:
            for resultfield, resultfield_type in self.resultfields.items():
                if not isinstance(resultfield, str):
                    self.logger.error("Keyfield name must be a string")
                    return False
                if not isinstance(resultfield_type, str):
                    self.logger.error("Keyfield type must be a string")
                    return False

        if not isinstance(self.logtables, dict):
            self.logger.error("Logtable configuration invalid")
            return False
        else:
            for logtable_name, logtable in self.logtables.items():
                if not isinstance(logtable_name, str):
                    self.logger.error("Logtable name must be a string")
                    return False
                if not logtable_name.startswith(self.table_name):
                    self.logger.error("Logtable name must start with table name")
                    return False
                if not isinstance(logtable, dict):
                    self.logger.error("Logtable configuration invalid")
                    return False
                else:
                    for key, type in logtable.items():
                        if not isinstance(key, str):
                            self.logger.error("Logtable name must be a string")
                            return False
                        if not isinstance(type, str):
                            self.logger.error("Logtable configuration invalid")
                            return False
        return True


class CustomCfg(Cfg):
    """
    Class for custom values given to every experiment.
    """

    def __init__(
        self,
        custom_values: Dict[str, Union[str, int]],
        logger: logging.Logger,
    ) -> None:
        """
        The constructor of the CustomCfg class.

        :param custom_values: Dictionary containing keys and values of custom values to be given to every experiment.
        :type custom_values: Dict[str, Union[str, int]]
        """
        self.custom_values = custom_values

        self.logger = logger

    @staticmethod
    def extract_config(config: OmegaConf, logger: logging.Logger) -> "CustomCfg":
        if not "Custom" in config["PY_EXPERIMENTER"]:
            logger.warning("No custom section defined in config")
            return CustomCfg({}, logger)
        else:
            custom_config = dict(config["PY_EXPERIMENTER"]["Custom"])
            logger.info(f"Found {len(custom_config)} custom values")
            return CustomCfg(custom_config, logger)

    def valid(self):
        if not isinstance(self.custom_values, dict):
            self.logger.error(f"self.custom_values must be a dictionary, but are of type {type(self.custom_values)}")
            return False
        return True


class CodeCarbonCfg(Cfg):
    """
    Class for the configuration of the CodeCarbon API.
    """

    def __init__(self, config: Dict[str, str], logger: logging.Logger) -> None:
        """
        Constructor for CodeCarbonCfg.

        :param config: Dictionary of key,values as described in the codecarbon configuration
        :type config: Dict[str,str]
        """
        self.config = config
        self.logger = logger

    @staticmethod
    def extract_config(config: OmegaConf, logger: logging.Logger) -> "CodeCarbonCfg":
        if not "CodeCarbon" in config["PY_EXPERIMENTER"]:
            logger.warning("No codecarbon section defined in config")
            return CodeCarbonCfg({}, logger)
        else:
            codecarbon_config = dict(config["PY_EXPERIMENTER"]["CodeCarbon"])
            logger.info(f"Found {len(codecarbon_config)} codecarbon values")
            return CodeCarbonCfg(codecarbon_config, logger)

    def valid(self):
        if not isinstance(self.config, dict):
            self.logger.error(f"self.config must be of type dict, but is {type(self.config)}")
            return False
        return True


class PyExperimenterCfg:
    """
    Configuration of a PyExperimenter object. Contains the configuration of the database, custom values, and the CodeCarbon API.
    """
    def __init__(
        self,
        n_jobs: int,
        database_configuration: DatabaseCfg,
        custom_configuration: CustomCfg,
        codecarbon_configuration: CodeCarbonCfg,
        logger: logging.Logger,
    ) -> None:
        self.logger = logger

        self.n_jobs = n_jobs
        self.database_configuration = database_configuration
        self.custom_configuration = custom_configuration
        self.codecarbon_configuration = codecarbon_configuration

    @staticmethod
    def extract_config(config_path: str, logger: logging.Logger) -> "PyExperimenterCfg":
        config = omegaconf.OmegaConf.load(config_path)

        if "n_jobs" not in config["PY_EXPERIMENTER"]:
            config["PY_EXPERIMENTER"]["n_jobs"] = 1
        else:
            n_jobs = config["PY_EXPERIMENTER"]["n_jobs"]

        database_configuration = DatabaseCfg.extract_config(config, logger)
        custom_configuration = CustomCfg.extract_config(config, logger)
        codecarbon_configuration = CodeCarbonCfg.extract_config(config, logger)
        return PyExperimenterCfg(n_jobs, database_configuration, custom_configuration, codecarbon_configuration, logger)

    def valid(self) -> bool:
        if not isinstance(self.n_jobs, int) and self.n_jobs > 0:
            self.logger.error("n_jobs must be a positive integer")
        if not (self.database_configuration.valid() and self.custom_configuration.valid() and self.codecarbon_configuration.valid()):
            self.logger.error("Database configuration invalid")
            return False
        return True
