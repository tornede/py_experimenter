import os
import re
import tempfile
from configparser import ConfigParser
from typing import Dict

import pytest

from py_experimenter.exceptions import ConfigError, MissingLogTableError, NoConfigFileError, ParameterCombinationError
from py_experimenter.utils import combine_fill_table_parameters, load_credential_config


def test_load_config_raises_error():  # todo adapt test
    path = os.path.join("config", "file", "missing.yml")
    with pytest.raises(NoConfigFileError, match=re.escape(f"Configuration file missing! Please add file: {path}")):
        load_credential_config(path)


@pytest.mark.parametrize(
    "keyfield_names, parameters, fixed_parameter_combinations, expected_result",
    [
        (
            ["keyfield_name_1", "keyfield_name_2"],
            {"keyfield_name_1": [1, 2, 3], "keyfield_name_2": [4, 5, 6]},
            {},
            [
                {"keyfield_name_1": 1, "keyfield_name_2": 4},
                {"keyfield_name_1": 1, "keyfield_name_2": 5},
                {"keyfield_name_1": 1, "keyfield_name_2": 6},
                {"keyfield_name_1": 2, "keyfield_name_2": 4},
                {"keyfield_name_1": 2, "keyfield_name_2": 5},
                {"keyfield_name_1": 2, "keyfield_name_2": 6},
                {"keyfield_name_1": 3, "keyfield_name_2": 4},
                {"keyfield_name_1": 3, "keyfield_name_2": 5},
                {"keyfield_name_1": 3, "keyfield_name_2": 6},
            ],
        ),
        (
            ["keyfield_name_1", "keyfield_name_2"],
            {},
            [
                {"keyfield_name_1": 1, "keyfield_name_2": 2},
                {"keyfield_name_1": 3, "keyfield_name_2": 4},
                {"keyfield_name_1": 5, "keyfield_name_2": 6},
            ],
            [
                {"keyfield_name_1": 1, "keyfield_name_2": 2},
                {"keyfield_name_1": 3, "keyfield_name_2": 4},
                {"keyfield_name_1": 5, "keyfield_name_2": 6},
            ],
        ),
    ],
)
def test_combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations, expected_result):
    assert expected_result == combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations)


@pytest.mark.parametrize(  # todo adapt test
    "keyfield_names, parameters, fixed_parameter_combinations, error_msg",
    [
        ([], {}, [], "No parameter combination found!"),
        (["keyfield_name_1"], {}, [], "No parameter combination found!"),
    ],
)
def test_combine_fill_table_parameters_raises_error(keyfield_names, parameters, fixed_parameter_combinations, error_msg):
    with pytest.raises(ParameterCombinationError, match=error_msg):
        combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations)


def test_read_yaml_config():
    file_name = os.path.join("test", "test_config_files", "yml_config.yml")
