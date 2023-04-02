import os
import re
from configparser import ConfigParser
from typing import Dict

import pytest

from py_experimenter.exceptions import ConfigError, MissingLogTableError, NoConfigFileError, ParameterCombinationError
from py_experimenter.utils import (_generate_int_data, add_timestep_result_columns, combine_fill_table_parameters, extract_columns, extract_logtables,
                                   get_keyfield_data, get_keyfield_names, get_keyfields, get_resultfields, load_config, timestamps_for_result_fields)


@pytest.mark.parametrize(
    'path, comparable_dict',
    [
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
         {
             'PY_EXPERIMENTER': {
                 'provider': 'mysql',
                 'database': 'py_experimenter',
                 'table': 'test_table',
                 'n_jobs': '5',
                 'keyfields': 'value:int, exponent:int',
                 'resultfields': 'sin, cos',
                 'value': '1,2,3,4,5,6,7,8,9,10',
                 'exponent': '1,2,3'
             },
             'DEFAULT': {}
        }),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_file_with_wrong_syntax.cfg'),
         {
             'PY_EXPERIMENTER': {
                 'provider': 'mysql',
                 'database': 'py_experimenter',
                 'table': 'test_table_mysql_with_wrong_syntax',
                 'n_jobs': '5',
                 'keyfields': 'value:int, exponent:int,',
                 'resultfields': 'sin, cos',
                 'value': '1,2,3,4,5,6,7,8,9,10',
                 'exponent': '1,2,3'
             },
             'DEFAULT': {}
        }),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file_without_keyfields.cfg'),
         {
             'PY_EXPERIMENTER': {
                 'provider': 'mysql',
                 'database': 'py_experimenter',
                 'table': 'test_table_without_keyfields',
                 'n_jobs': '5',
                 'keyfields': '',
                 'resultfields': 'sin, cos',
                 'value': '1,2,3,4,5,6,7,8,9,10',
                 'exponent': '1,2,3'
             },
             'DEFAULT': {}
        }),

        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg'),
         {
             'PY_EXPERIMENTER': {
                 'provider': 'sqlite',
                 'database': 'py_experimenter',
                 'table': 'test_table_sqlite',
                 'n_jobs': '5',
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
    'config_file, expected_result',
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
        ),
        pytest.param(
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_resultfield_timestamp_upper_case.cfg'),
            True,
            id='with_timestamp_upper_case'
        )
    ]
)
def test_timestamps_for_result_fields(config_file, expected_result):
    config = load_config(config_file)
    assert expected_result == timestamps_for_result_fields(config)


def test_load_config_raises_error():
    path = os.path.join('config', 'file', 'missing.cfg')
    with pytest.raises(NoConfigFileError, match=re.escape(f'Configuration file missing! Please add file: {path}')):
        load_config(path)


@pytest.mark.parametrize(
    'path, expected_result',
    [
        pytest.param(
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_resultfield_timestamp_lower_case.cfg'),
                        ([
                            ('final_pipeline', 'LONGTEXT'),
                            ('final_pipeline_timestamp', 'VARCHAR(255)'),
                            ('internal_performance', 'int(3)'),
                            ('internal_performance_timestamp', 'VARCHAR(255)'),
                            ('performance_asymmetric_loss', 'VARCHAR(255)'),
                            ('performance_asymmetric_loss_timestamp', 'VARCHAR(255)'),
                        ]
            ),
            id='basic'
        )
    ]
)
def test_add_timestep_result_columns(path, expected_result):
    config = load_config(path)
    resultfields = get_resultfields(config)
    assert expected_result == add_timestep_result_columns(resultfields)


def test_get_keyfield_data():
    expected_data = {
        'value': [1, 2, 3, 4, 5],
        'value2': [1, 2, 3, 4, 5],
        'value3': ['different', 'test', 'strings'],
        'value4': [1, 2, 3, 4, 5, 6, 8, 10]
    }

    config = load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_get_keyfield_data.cfg'))
    data = get_keyfield_data(config)
    assert expected_data == data


@pytest.mark.parametrize(
    'file_data, expected_data',
    [
        pytest.param(
            '1,2,3,4,5,6,7,8,9,10'.split(','),
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            id='simple_values'
        ),
        pytest.param(
            '1:4:1'.split(','),
            [1, 2, 3, 4],
            id='range'
        ),
        pytest.param(
            '1:4:1,6:9:2'.split(','),
            [1, 2, 3, 4, 6, 8],
            id='two_ranges_without_overlap'
        ),
        pytest.param(
            '-1:10:2, 1:10:3'.split(','),
            [-1, 1, 3, 4, 5, 7, 9, 10],
            id='two_ranges_with_overlap'
        ),
        pytest.param(
            '1:6:2, 4'.split(','),
            [1, 3, 4, 5],
            id='range_and_simple_value'
        ),
        pytest.param(
            '1:6, 4'.split(','),
            [1, 2, 3, 4, 5, 6],
            id='range_without_step'
        )
    ]
)
def test_generate_int_data(file_data, expected_data):
    assert expected_data == _generate_int_data(file_data)


@pytest.mark.parametrize(
    'keyfield_values, error, error_string',
    [
        pytest.param(
            ':2:2'.split(','),
            ConfigError,
            ':2:2 is not a valid integer range',
            id='no_start_of_range'
        ),
        pytest.param(
            'error:2:2'.split(','),
            ConfigError,
            'error:2:2 is not a valid integer range',
            id='invalid_start_of_range'
        ),
        pytest.param(
            '1::2'.split(','),
            ConfigError,
            '1::2 is not a valid integer range',
            id='no_end_of_range'
        ),
        pytest.param(
            '1:error:2'.split(','),
            ConfigError,
            '1:error:2 is not a valid integer range',
            id='invalid_end_of_range'
        ),
        pytest.param(
            '1:2:error'.split(','),
            ConfigError,
            '1:2:error is not a valid integer range',
            id='invalid_step'
        ),
        pytest.param(
            '2:1'.split(','),
            ConfigError,
            'end of range 1 is smaller than, or equal to start of range 2',
            id='end_smaller_than_start'
        )


    ]
)
def test_generate_int_data_raises_error(keyfield_values, error, error_string):
    with pytest.raises(error, match=re.escape(error_string)):
        _generate_int_data(keyfield_values)


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
def test_extract_columns(fields, expected_field_names):
    assert extract_columns(fields) == expected_field_names


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


@pytest.mark.parametrize(
    'table_name, configuration_dict, expected_logtables',
    [
        pytest.param(
            'some_table_name',
            {'PY_EXPERIMENTER': {
                'logtables': 'table1:Table1, table2:Table2',
                'Table1': 'a:FLOAT, b:FLOAT',
                'Table2': 'a:FLOAT, b'}},
            {'some_table_name__table1': [('a', 'FLOAT'), ('b', 'FLOAT')], 
             'some_table_name__table2': [('a', 'FLOAT'), ('b', 'VARCHAR(255)')]},
            id='logtables with two tables'
        ),
        pytest.param(
            'some_table_name',
            {'PY_EXPERIMENTER': {
                'logtables': 'table1:Table1, table2:Table2, table3:FLOAT',
                'Table1': 'a:FLOAT, b:FLOAT',
                'Table2': 'a:FLOAT, b'}},
            {'some_table_name__table1': [('a', 'FLOAT'), ('b', 'FLOAT')],
             'some_table_name__table2': [('a', 'FLOAT'), ('b', 'VARCHAR(255)')],
             'some_table_name__table3': [('table3', 'FLOAT')]},
            id='logtables with three tables'
        ),
    ]
)
def test_extract_logtables(table_name:str, configuration_dict: Dict[str, Dict[str, str]], expected_logtables: Dict[str, Dict[str, str]]):
    config = ConfigParser()
    config.read_dict(configuration_dict)
    logtables = extract_logtables(config, table_name)
    assert expected_logtables == logtables


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
