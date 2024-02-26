# todo ckeck which of thees utils are still neded
import logging
from configparser import ConfigParser
from datetime import datetime
from typing import Any, Dict, List, Union

import numpy as np
from omegaconf import DictConfig

from py_experimenter.exceptions import (
    ConfigError,
    NoConfigFileError,
    ParameterCombinationError,
)


def load_credential_config(path):
    """
    Load and return configuration file.
    :param path: path to the config file
    :return: configuration file
    """
    config = ConfigParser()
    try:
        with open(path) as f:
            config.read_file(f)
    except FileNotFoundError:
        raise NoConfigFileError(f"Configuration file missing! Please add file: {path}")

    return dict(config["CREDENTIALS"])


def write_codecarbon_config(codecarbon_config: DictConfig):
    configparser = ConfigParser()
    configparser.read_dict({"codecarbon": dict(codecarbon_config)})
    with open(".codecarbon.config", "w") as f:
        configparser.write(f)


def extract_codecarbon_columns() -> Dict[str, str]:
    return dict(
        [
            ("codecarbon_timestamp", "DATETIME "),
            ("project_name", "VARCHAR(255)"),
            ("run_id", "VARCHAR(255)"),
            ("duration_seconds", "DOUBLE"),
            ("emissions_kg", "DOUBLE"),
            ("emissions_rate_kg_sec", "DOUBLE"),
            ("cpu_power_watt", "DOUBLE"),
            ("gpu_power_watt", "DOUBLE"),
            ("ram_power_watt", "DOUBLE"),
            ("cpu_energy_kw", "DOUBLE"),
            ("gpu_energy_kw", "DOUBLE"),
            ("ram_energy_kw", "DOUBLE"),
            ("energy_consumed_kw", "DOUBLE"),
            ("country_name", "VARCHAR(255)"),
            ("country_iso_code", "VARCHAR(255)"),
            ("region", "VARCHAR(255)"),
            ("cloud_provider", "VARCHAR(255)"),
            ("cloud_region", "VARCHAR(255)"),
            ("os", "VARCHAR(255)"),
            ("python_version", "VARCHAR(255)"),
            ("codecarbon_version", "VARCHAR(255)"),
            ("cpu_count", "DOUBLE"),
            ("cpu_model", "VARCHAR(255)"),
            ("gpu_count", "DOUBLE"),
            ("gpu_model", "VARCHAR(255)"),
            ("longitude", "VARCHAR(255)"),
            ("latitude", "VARCHAR(255)"),
            ("ram_total_size", "DOUBLE"),
            ("tracking_mode", "VARCHAR(255)"),
            ("on_cloud", "VARCHAR(255)"),
            ("power_usage_efficiency", "DOUBLE"),
            ("offline_mode", "BOOL"),
        ]
    )


def combine_fill_table_parameters(
    keyfield_names: List[str],
    parameters: Dict[str, Union[str, int, float, bool]],
    fixed_parameter_combinations: List[Dict[str, Union[str, int, float, bool]]] = None,
):
    """
    Combiens different parameters to a list of parameter combinations.
    :param keyfield_names: names of the keyfields
    :type keyfield_names: List[str]
    :param parameters: These values are combiend with each other and every fixed parameter combination. This combination is similar to the cartesian product.
    :type parameters: Dict[str, Union[str, int, float, bool]]
    :param fixed_parameter_combinations: These values are combiend with every parameter like in the cartesian product. However, the values inside of two different list items
    are not combined with each other.
    """

    def create_combination_from_parameters():
        keyfield_data = list()
        used_keys = list()

        for keyfield_name in keyfield_names:
            if keyfield_name in parameters.keys():
                keyfield_data.append(parameters[keyfield_name])
                used_keys.append(keyfield_name)

        if keyfield_data:
            combinations = np.array(np.meshgrid(*keyfield_data), dtype=object).T.reshape(-1, len(keyfield_data))
            combinations = [dict(zip(used_keys, combination)) for combination in combinations]
        else:
            combinations = []
        return combinations

    def add_individual_parameters_to_combinations():
        new_combinations = list()
        if combinations:
            for combination in combinations:
                for fixed_parameter_combination in fixed_parameter_combinations:
                    try:
                        new_combination = dict(**combination, **fixed_parameter_combination)
                    except TypeError:
                        raise ParameterCombinationError("There is at least one key that is used more than once!")
                    new_combinations.append(new_combination)
        else:
            new_combinations = fixed_parameter_combinations

        return new_combinations

    combinations = create_combination_from_parameters()

    if fixed_parameter_combinations:
        combinations = add_individual_parameters_to_combinations()

    if not combinations:
        raise ParameterCombinationError("No parameter combination found!")

    for combination in combinations:
        if len(combination.keys()) != len(set(combination.keys())):
            raise ParameterCombinationError(f"There is at least one key that is used more than once in {str(combination.keys())}!")

        if set(combination.keys()) != set(keyfield_names):
            raise ParameterCombinationError(
                "The number of config_parameters + individual_parameters + parameters does not match the amount of keyfields!"
            )

    return combinations


def get_timestamp_representation() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
