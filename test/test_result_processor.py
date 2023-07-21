import os

import pytest
from freezegun import freeze_time
from mock import patch

from py_experimenter import database_connector, database_connector_lite, database_connector_mysql, utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.exceptions import InvalidConfigError, InvalidResultFieldError
from py_experimenter.result_processor import ResultProcessor

CREDENTIAL_PATH = os.path.join('test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg')


@patch.object(database_connector_lite.DatabaseConnectorLITE, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@pytest.mark.parametrize(
    'config, table_name, expected_provider',
    [
        (
            utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg')),
            'test_table',
            DatabaseConnectorMYSQL
        ),
        (
            utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg')),
            'test_table',
            DatabaseConnectorLITE
        ),
    ]
)
def test_init(create_database_if_not_existing_mock, test_connection_mysql, test_connection_sqlite, config, table_name, expected_provider):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mysql.return_value = None
    test_connection_sqlite.return_value = None
    result_processor = ResultProcessor(config, False, None, CREDENTIAL_PATH, table_name, 0, 'test_logger')

    assert table_name == result_processor._table_name
    assert expected_provider == result_processor._dbconnector.__class__


@patch.object(database_connector.DatabaseConnector, '_test_connection')
def test_init_raises_error(mock_fn):
    mock_fn.return_value = None
    table_name = 'test_table'
    condition = {'test': 'condition'}
    config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    config.set('PY_EXPERIMENTER', 'provider', 'test_provider')
    with pytest.raises(InvalidConfigError, match='Invalid database provider!'):
        ResultProcessor(config, False, None, CREDENTIAL_PATH, table_name, condition, 'test_logger')


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@pytest.mark.parametrize(
    'results,error, errorstring, experiment_id',
    [
        (
            {
                'result_field_1': 'result_field_1_value',
                'sin': 'result_field_2_value',
            },
            InvalidResultFieldError,
            f"Invalid result keys: {{'result_field_1'}}",
            0
        ),
    ]
)
def test_process_results_raises_error(create_database_mock, test_connection_mock, results, error, errorstring, experiment_id):
    create_database_mock.return_value = None
    test_connection_mock.return_value = None
    table_name = 'test_table'
    config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))

    result_processor = ResultProcessor(config, False, None, CREDENTIAL_PATH, table_name, experiment_id, 'test_logger')

    with pytest.raises(error, match=errorstring):
        result_processor.process_results(results)


@patch('py_experimenter.utils.get_result_field_names')
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
def test_valid_result_fields(create_database_if_not_existing_mock, test_connection_mock, get_resultfilds_names_mock, existing_result_fields, used_result_fields, subset_boolean):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mock.return_value = None
    get_resultfilds_names_mock.return_value = used_result_fields
    mock_config = utils.load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    assert subset_boolean == ResultProcessor(mock_config, False, None, CREDENTIAL_PATH, 'test_table_name',
                                             0, 'test_logger')._valid_result_fields(existing_result_fields)


@freeze_time('2020-01-01 00:00:00')
@pytest.mark.parametrize(
    'results, expected_results',
    [
        pytest.param(
            {'result_field_1': 'result_field_1_value',
             'result_field_2': 'result_field_2_value'},
            {'result_field_1': 'result_field_1_value',
             'result_field_1_timestamp': '2020-01-01 00:00:00',
             'result_field_2': 'result_field_2_value',
             'result_field_2_timestamp': '2020-01-01 00:00:00'},
            id='default_testcase'
        ),
        pytest.param(
            {}, {},
            id='empty_testcase'
        ),
        pytest.param(
            {'result_field_1': 'result_field_1_value', },
            {'result_field_1': 'result_field_1_value',
             'result_field_1_timestamp': '2020-01-01 00:00:00', },
            id='one_value_testcase'
        ),

    ]
)
def test_add_timestamps_to_results(results, expected_results):
    assert expected_results == ResultProcessor._add_timestamps_to_results(results)


@pytest.fixture
def result_processor():
    config = utils.load_config(os.path.join('test', 'test_logtables', 'sqlite_logtables.cfg'))
    return ResultProcessor(config, False, None, None, 'test_table', 0, 'test_logger')


def test_valid_logtable_logs(result_processor: ResultProcessor):
    assert result_processor._valid_logtable_logs({'test_sqlite_log': {'test': 0}})
    assert not result_processor._valid_logtable_logs({'test_sqlite_log': {'test': 0, 'test2': 1}})
