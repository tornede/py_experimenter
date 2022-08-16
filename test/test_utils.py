import os

import pytest

from py_experimenter.py_experimenter_exceptions import NoConfigFileError, ParameterCombinationError
from py_experimenter.utils import combine_fill_table_parameters, get_field_names, get_keyfields, load_config


@pytest.mark.parametrize(
    'path, comparable_dict',
    [
        (os.path.join('test','test_config_files','load_config_test_file','my_sql_test_file.cfg'),
         {
             'DATABASE': {
                 'provider': 'mysql',
                 'database': 'example3',
                 'table': 'example_table'
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
        (os.path.join('test','test_config_files','load_config_test_file','my_sql_file_with_weird_syntax.cfg'),
         {
             'DATABASE': {
                 'provider': 'mysql',
                 'database': 'example3',
                 'table': 'example_table'
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
        (os.path.join('test','test_config_files','load_config_test_file','my_sql_test_file_without_keyfields.cfg'),
         {
             'DATABASE': {
                 'provider': 'mysql',
                 'database': 'example3',
                 'table': 'example_table'
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

        (os.path.join('test','test_config_files','load_config_test_file','sqlite_test_file.cfg'),
         {
             'DATABASE': {
                 'provider': 'sqlite',
                 'database': 'example4',
                 'table': 'example_table'
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


def test_load_config_raises_error():
    path = os.path.join('config', 'file', 'misssing.cfg')
    with pytest.raises(NoConfigFileError, match=f'Configuration file missing! Please add file: {str(path)}'):
        load_config(path)


@pytest.mark.parametrize(
    'fields, expected_field_names',
    [
        ('value:int, exponent:int', ['value', 'exponent']),
        ('value, exponent', ['value', 'exponent']),
        ('', []),
        ('value:int, exponent', ['value', 'exponent']),
        ('value:int,', ['value']),
        ('value, value:int', ['value', 'value']),
    ])
def test_get_field_names(fields, expected_field_names):
    assert get_field_names(fields) == expected_field_names


@pytest.mark.parametrize(
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
def test_get_keyfields(config_mock_dict, expected_keyfields):
    keyfields = get_keyfields(config_mock_dict)
    assert keyfields == expected_keyfields


@pytest.mark.parametrize(
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
