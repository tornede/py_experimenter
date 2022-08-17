import os

import pytest
from mock import patch

from py_experimenter import database_connector, utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.py_experimenter_exceptions import InvalidConfigError, InvalidResultFieldError
from py_experimenter.result_processor import ResultProcessor

CREDENTIAL_PATH = os.path.join('test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg')


@patch.object(database_connector.DatabaseConnector, '_test_connection')
@pytest.mark.parametrize(
    'config, table_name, condition, result_fields, expected_provider',
    [
        (
            utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg')),
            'test_table',
            {'test': 'condition'},
            ['result_field_1', 'result_field_2'],
            DatabaseConnectorMYSQL
        ),
        (
            utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg')),
            'test_table',
            {'test': 'condition'},
            ['result_field_1', 'result_field_2'],
            DatabaseConnectorLITE
        ),
    ]
)
def test_init(mock_fn, config, table_name, condition, result_fields, expected_provider):
    mock_fn.return_value = None
    result_processor = ResultProcessor(config, CREDENTIAL_PATH, table_name, condition, result_fields)

    assert table_name == result_processor.table_name
    assert result_fields == result_processor._result_fields
    assert expected_provider == result_processor._dbconnector.__class__


@patch.object(database_connector.DatabaseConnector, '_test_connection')
def test_init_raises_error(mock_fn):
    mock_fn.return_value = None
    table_name = 'test_table'
    condition = {'test': 'condition'}
    result_fields = ['result_field_1', 'result_field_2']
    config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    config.set('DATABASE', 'provider', 'test_provider')
    with pytest.raises(InvalidConfigError, match='Invalid database provider!'):
        ResultProcessor(config, CREDENTIAL_PATH, table_name, condition, result_fields)


@patch.object(database_connector.DatabaseConnector, '_test_connection')
@pytest.mark.parametrize(
    'result_fields, results, error, errorstring',
    [
        (
            [
                'result_field_1',
                'result_field_3', ],
            {
                'result_field_1': 'result_field_1_value',
                'result_field_2': 'result_field_2_value',
            },
            InvalidResultFieldError,
            f"Invalid result keys: {{'result_field_2'}}"
        ),
    ]
)
def test_process_results_raises_error(test_fn, result_fields, results, error, errorstring):
    test_fn.return_value = None
    table_name = 'test_table'
    condition = {'test': 'condition'}
    config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))

    result_processor = ResultProcessor(config, CREDENTIAL_PATH, table_name, condition, result_fields)

    with pytest.raises(error, match=errorstring):
        result_processor.process_results(results)


@patch.object(database_connector.DatabaseConnector, '_test_connection')
@pytest.mark.parametrize(
    'existing_result_fields, used_result_fields, subset_boolean',
    [
        (['result_field_1', 'result_field_2', 'result_field_3'], ['result_field_1', 'result_field_2', 'result_field_3'], True),
        (['result_field_1', 'result_field_2', 'result_field_3'], ['result_field_1', 'result_field_2'], False),
        ([], ['result_field_1', 'result_field_2', 'result_field_3', 'result_field_4'], True),
    ]
)
def test_valid_result_fields(mock_fn, existing_result_fields, used_result_fields, subset_boolean):
    mock_fn.return_value = None
    mock_config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    assert subset_boolean == ResultProcessor(mock_config, CREDENTIAL_PATH, 'test_table_name', {
                                             'test_condition_key': 'test_condition_value'}, used_result_fields)._valid_result_fields(existing_result_fields)
