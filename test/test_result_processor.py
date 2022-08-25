import os

import pytest
from mock import patch

from py_experimenter import database_connector, database_connector_lite, database_connector_mysql, utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.py_experimenter_exceptions import InvalidConfigError, InvalidResultFieldError
from py_experimenter.result_processor import ResultProcessor

CREDENTIAL_PATH = os.path.join('test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg')


@patch.object(database_connector_lite.DatabaseConnectorLITE, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
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
def test_init(create_database_if_not_existing_mock, test_connection_mysql, test_connection_sqlite, config, table_name, condition, result_fields, expected_provider):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mysql.return_value = None
    test_connection_sqlite.return_value = None
    result_processor = ResultProcessor(config, CREDENTIAL_PATH, table_name, condition, result_fields)

    assert table_name == result_processor._table_name
    assert result_fields == result_processor._result_fields
    assert expected_provider == result_processor._dbconnector.__class__


@patch.object(database_connector.DatabaseConnector, '_test_connection')
def test_init_raises_error(mock_fn):
    mock_fn.return_value = None
    table_name = 'test_table'
    condition = {'test': 'condition'}
    result_fields = ['result_field_1', 'result_field_2']
    config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    config.set('PY_EXPERIMENTER', 'provider', 'test_provider')
    with pytest.raises(InvalidConfigError, match='Invalid database provider!'):
        ResultProcessor(config, CREDENTIAL_PATH, table_name, condition, result_fields)


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
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
def test_process_results_raises_error(create_database_mock, test_connection_mock, result_fields, results, error, errorstring):
    create_database_mock.return_value = None
    test_connection_mock.return_value = None
    table_name = 'test_table'
    condition = {'test': 'condition'}
    config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))

    result_processor = ResultProcessor(config, CREDENTIAL_PATH, table_name, condition, result_fields)

    with pytest.raises(error, match=errorstring):
        result_processor.process_results(results)


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@pytest.mark.parametrize(
    'existing_result_fields, used_result_fields, subset_boolean',
    [
        (['result_field_1', 'result_field_2', 'result_field_3'], ['result_field_1', 'result_field_2', 'result_field_3'], True),
        (['result_field_1', 'result_field_2', 'result_field_3'], ['result_field_1', 'result_field_2'], False),
        ([], ['result_field_1', 'result_field_2', 'result_field_3', 'result_field_4'], True),
    ]
)
def test_valid_result_fields(create_database_if_not_existing_mock, test_connection_mock, existing_result_fields, used_result_fields, subset_boolean):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mock.return_value = None
    mock_config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    assert subset_boolean == ResultProcessor(mock_config, CREDENTIAL_PATH, 'test_table_name', {
                                             'test_condition_key': 'test_condition_value'}, used_result_fields)._valid_result_fields(existing_result_fields)


@pytest.mark.parametrize(
    'results, time, expected_results',
    [
        pytest.param(
            {
                'result_field_1': 'result_field_1_value',
                'result_field_2': 'result_field_2_value',
            },
            '2020-01-01 00:00:00',
            {
                'result_field_1': 'result_field_1_value',
                'result_field_1_timestamp': '2020-01-01 00:00:00',
                'result_field_2': 'result_field_2_value',
                'result_field_2_timestamp': '2020-01-01 00:00:00',
            },
            id='default_testcase'
        ),
        pytest.param(
            {
            },
            '2020-01-01 00:00:00',
            {
            },
            id='empty_testcase'
        ),
        pytest.param(
            {
                'result_field_1': 'result_field_1_value',
            },
            '2020-01-01 00:00:00',
            {
                'result_field_1': 'result_field_1_value',
                'result_field_1_timestamp': '2020-01-01 00:00:00',
            },
            id='one_value_testcase'
        ),

    ]
)
def test_add_timestamps_to_results(results, time, expected_results):
    assert expected_results == ResultProcessor._add_timestamps_to_results(results, time)
