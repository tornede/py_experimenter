import os
import re

import pytest

from py_experimenter.py_experimenter_exceptions import NoConfigFileError, ParameterCombinationError
from py_experimenter.utils import (combine_fill_table_parameters, get_fields, get_keyfield_names, get_keyfields, load_config,
                                   timestamps_for_result_fields)


@pytest.mark.parametrize(
    'path, comparable_dict',
    [
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
         {
             'DATABASE': {
                 'provider': 'mysql',
                 'database': 'py_experimenter',
                 'table': 'test_table'
             },
             'PY_EXPERIMENTER': {
                 'cpu.max': '5',
                 'keyfields': 'value:int, exponent:int',
                 'resultfields': 'sin, cos',
                 'value': '1,2,3,4,5,6,7,8,9,10',
                 'exponent': '1,2,3'
             },
             'DEFAULT': {}
        }),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_file_with_wrong_syntax.cfg'),
         {
             'DATABASE': {
                 'provider': 'mysql',
                 'database': 'py_experimenter',
                 'table': 'test_table_mysql_with_wrong_syntax'
             },
             'PY_EXPERIMENTER': {
                 'cpu.max': '5',
                 'keyfields': 'value:int, exponent:int,',
                 'resultfields': 'sin, cos',
                 'value': '1,2,3,4,5,6,7,8,9,10',
                 'exponent': '1,2,3'
             },
             'DEFAULT': {}
        }),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file_without_keyfields.cfg'),
         {
             'DATABASE': {
                 'provider': 'mysql',
                 'database': 'py_experimenter',
                 'table': 'test_table_without_keyfields'
             },
             'PY_EXPERIMENTER': {
                 'cpu.max': '5',
                 'keyfields': '',
                 'resultfields': 'sin, cos',
                 'value': '1,2,3,4,5,6,7,8,9,10',
                 'exponent': '1,2,3'
             },
             'DEFAULT': {}
        }),

        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg'),
         {
             'DATABASE': {
                 'provider': 'sqlite',
                 'database': 'py_experimenter',
                 'table': 'test_table_sqlite'
             },
             'PY_EXPERIMENTER': {
                 'cpu.max': '5',
                 'keyfields': 'datasetName, internal_performance_measure, featureObjectiveMeasure, seed:int(3)',
                 'resultfields': 'final_pipeline:LONGTEXT, internal_performance:int(3), performance_asymmetric_loss',
                 'datasetname': 'A,B,C',
                 'internal_performance_measure': 'X,Y',
                 'featureobjectivemeasure': 'M',
                 'seed': '1,2,3,4'
             },
             'CUSTOM': {
                 'pause.max': '10',
                 'pause.threshold': '8'
             },
             'DEFAULT': {}
        })
    ],

)
def test_load_config(path, comparable_dict):
    def compare_dict_with_config(config, comparable_dict):
        assert len(config) == len(comparable_dict)
        assert config.keys() == comparable_dict.keys()
        for key, value in comparable_dict.items():
            if isinstance(config[key], str):
                assert config[key] == value
            else:
                compare_dict_with_config(config[key], value)

    config = load_config(path)
    compare_dict_with_config(config, comparable_dict)


@pytest.mark.parametrize(
    'config_path, expected_result',
    [
        pytest.param(
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_no_resultfield_timestamp_upper_case.cfg'),
            False,
            id='no_timestamp_upper_case'
        ),
        pytest.param(
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_no_resultfield_timestamp_config.cfg'),
            False,
            id='file_without_specification'
        ),
        pytest.param(
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_no_resultfield_timestamp_lower_case.cfg'),
            False,
            id='no_timestamp_lower_case'
        ),
        pytest.param(
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_resultfield_timestamp_lower_case.cfg'),
            True,
            id='with_timestamp_lower_case'
        ), pytest.param(
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_resultfield_timestamp_upper_case.cfg'),
            True,
            id='with_timestamp_upper_case'
        )

    ]
)
def test_timestamps_for_result_fields(config_path, expected_result):
    config = load_config(config_path)
    assert expected_result == timestamps_for_result_fields(config)


def test_load_config_raises_error():
    path = os.path.join('config', 'file', 'missing.cfg')
    with pytest.raises(NoConfigFileError, match=re.escape(f'Configuration file missing! Please add file: {path}')):
        load_config(path)


@pytest.mark.parametrize(
    'fields, expected_field_names',
    [
        ('value:int, exponent:int',  [('value', 'int'), ('exponent', 'int')]),
        ('value, exponent', [('value', 'VARCHAR(255)'), ('exponent', 'VARCHAR(255)')]),
        ('', []),
        ('value:int, exponent', [('value', 'int'), ('exponent', 'VARCHAR(255)')]),
        ('value:int,', [('value', 'int')]),
        ('value, value:int', [('value', 'VARCHAR(255)'), ('value', 'int')]),
    ])
def test_get_field_names(fields, expected_field_names):
    assert get_fields(fields) == expected_field_names


@ pytest.mark.parametrize(
    'config_mock_dict, expected_keyfields',
    [
        ({'PY_EXPERIMENTER': {
            'keyfields': 'datasetName, internal_performance_measure, featureObjectiveMeasure, seed:int(3)',
        }, },
            ['datasetName', 'internal_performance_measure', 'featureObjectiveMeasure', 'seed']),
        ({'PY_EXPERIMENTER': {
            'keyfields': '',
        }},
            []),
        ({'PY_EXPERIMENTER': {
            'keyfields': 'datasetName:str, internal_performance_measure:some_type, featureObjectiveMeasure,'
        }},
            ['datasetName', 'internal_performance_measure', 'featureObjectiveMeasure']),

    ]
)
def test_get_keyfield_names(config_mock_dict, expected_keyfields):
    keyfields = get_keyfield_names(config_mock_dict)
    assert keyfields == expected_keyfields


@ pytest.mark.parametrize(
    'config_mock_dict, expected_keyfields',
    [
        ({'PY_EXPERIMENTER': {
            'keyfields': 'datasetName, internal_performance_measure, featureObjectiveMeasure, seed:int(3)',
        }, },
            [('datasetName', 'VARCHAR(255)'), ('internal_performance_measure', 'VARCHAR(255)'), ('featureObjectiveMeasure', 'VARCHAR(255)'), ('seed', 'int(3)')]),
        ({'PY_EXPERIMENTER': {
            'keyfields': '',
        }},
            []),
        ({'PY_EXPERIMENTER': {
            'keyfields': 'datasetName:str, internal_performance_measure:some_type, featureObjectiveMeasure,'
        }},
            [('datasetName', 'str'), ('internal_performance_measure', 'some_type'), ('featureObjectiveMeasure', 'VARCHAR(255)')]),

    ]
)
def test_get_keyfields(config_mock_dict, expected_keyfields):
    keyfields = get_keyfields(config_mock_dict)
    assert expected_keyfields == keyfields


@ pytest.mark.parametrize(
    'fields, expected_keyfields',
    [
        (
            'datasetName, internal_performance_measure, featureObjectiveMeasure, seed:int(3)',
            [('datasetName', 'VARCHAR(255)'), ('internal_performance_measure', 'VARCHAR(255)'), ('featureObjectiveMeasure', 'VARCHAR(255)'), ('seed', 'int(3)')]),
        (
            '',
            []
        ),
        (
            'datasetName:str, internal_performance_measure:some_type, featureObjectiveMeasure,',
            [('datasetName', 'str'), ('internal_performance_measure', 'some_type'), ('featureObjectiveMeasure', 'VARCHAR(255)')]),

    ]
)
def test_get_fields(fields, expected_keyfields):
    field_values = get_fields(fields)
    assert expected_keyfields == field_values


@ pytest.mark.parametrize(
    'keyfield_names, parameters, fixed_parameter_combinations, expected_result',
    [
        (
            ['keyfield_name_1', 'keyfield_name_2'],
            {'keyfield_name_1': [1, 2, 3], 'keyfield_name_2': [4, 5, 6]},
            {},
            [
                {'keyfield_name_1': 1, 'keyfield_name_2': 4},
                {'keyfield_name_1': 1, 'keyfield_name_2': 5},
                {'keyfield_name_1': 1, 'keyfield_name_2': 6},
                {'keyfield_name_1': 2, 'keyfield_name_2': 4},
                {'keyfield_name_1': 2, 'keyfield_name_2': 5},
                {'keyfield_name_1': 2, 'keyfield_name_2': 6},
                {'keyfield_name_1': 3, 'keyfield_name_2': 4},
                {'keyfield_name_1': 3, 'keyfield_name_2': 5},
                {'keyfield_name_1': 3, 'keyfield_name_2': 6}
            ]
        ),
        (
            ['keyfield_name_1', 'keyfield_name_2'],
            {},
            [
                {'keyfield_name_1': 1, 'keyfield_name_2': 2},
                {'keyfield_name_1': 3, 'keyfield_name_2': 4},
                {'keyfield_name_1': 5, 'keyfield_name_2': 6},
            ],
            [
                {'keyfield_name_1': 1, 'keyfield_name_2': 2},
                {'keyfield_name_1': 3, 'keyfield_name_2': 4},
                {'keyfield_name_1': 5, 'keyfield_name_2': 6},
            ]
        ),

    ]
)
def test_combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations, expected_result):
    assert expected_result == combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations)


@ pytest.mark.parametrize(
    'keyfield_names, parameters, fixed_parameter_combinations, error_msg',
    [
        ([], {}, [], 'No parameter combination found!'),
        (
            ['keyfield_name_1'],
            {},
            [],
            'No parameter combination found!'
        ),
        (
            ['keyfield_name_1', 'keyfield_name_2'],
            {'keyfield_name_1': [1, 2], 'keyfield_name_2': [4, 5]},
            [{'keyfield_name_2': [7]}],
            'There is at least one key that is used more than once!'
        ),

    ]
)
def test_combine_fill_table_parameters_raises_error(keyfield_names, parameters, fixed_parameter_combinations, error_msg):
    with pytest.raises(ParameterCombinationError, match=error_msg):
        combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations)
