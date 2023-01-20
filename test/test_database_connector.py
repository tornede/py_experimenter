import datetime
import os

import mock
import pytest
from mock import patch

from py_experimenter import database_connector, database_connector_mysql
from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.experiment_status import ExperimentStatus
from py_experimenter.utils import load_config


@pytest.mark.parametrize(
    'combination, existing_rows, keyfield_names, result',
    [
        ({'value': 1, 'exponent': 2}, ['[1 2]'], ['value', 'exponent'], True),
        ({'value': 1, 'exponent': 2}, ['[]'], ['value', 'exponent'], False),
        ({'value': 3, 'exponent': 4}, ['[1 2],', '[3 4]'], ['value', 'exponent'], True),
        ({'value': 3, 'exponent': 4}, ['[1 2],', '[3 4]'], ['exponent', 'value'], False),
        ({'value': 1, 'exponent': 4}, ['[1 2],', '[3 4]'], ['value', 'exponent'], False),
        ({'value': 1}, ['[1]'], ['value'], True),
        ({'value': 1}, ['[2]'], ['value'], False),
    ]
)
def test_check_combination_in_existing_rows(combination, existing_rows, keyfield_names, result):
    assert result == DatabaseConnector._check_combination_in_existing_rows(None, combination, existing_rows, keyfield_names)


@patch.object(database_connector.DatabaseConnector, '_table_has_correct_structure')
@patch.object(database_connector.DatabaseConnector, '_table_exists')
@patch.object(database_connector.DatabaseConnector, 'cursor')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'fetchall')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'close_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'execute')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'connect')
@patch.object(database_connector.DatabaseConnector, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
def test_create_table_if_not_exists(create_database_if_not_existing_mock, test_connection_mock, connect_mock, execute_mock, close_connection_mock, fetchall_mock, cursor_mock, table_exists_mock, table_has_correct_structure_mock):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mock.return_value = None
    connect_mock.return_value = None
    cursor_mock.return_value = None
    execute_mock.return_value = None
    fetchall_mock.return_value = None
    close_connection_mock.return_value = None
    table_exists_mock.return_value = True
    table_has_correct_structure_mock.return_value = True
    experiment_configuration_file_path = load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    database_connector = DatabaseConnectorMYSQL(experiment_configuration_file_path, database_credential_file_path=os.path.join(
        'test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg'))
    database_connector.create_table_if_not_existing()
    create_table_string = create_table_string = ('CREATE TABLE test_table (ID int NOT NULL AUTO_INCREMENT, value int DEFAULT NULL,exponent int DEFAULT NULL,'
                                                 'creation_date VARCHAR(255) DEFAULT NULL,status VARCHAR(255) DEFAULT NULL,start_date VARCHAR(255) DEFAULT NULL,'
                                                 'name LONGTEXT DEFAULT NULL,machine VARCHAR(255) DEFAULT NULL,sin VARCHAR(255) DEFAULT NULL,'
                                                 'cos VARCHAR(255) DEFAULT NULL,end_date VARCHAR(255) DEFAULT NULL,error LONGTEXT DEFAULT NULL, PRIMARY KEY (ID))'
                                                 )
    execute_mock.assert_has_calls(
        [
            mock.call(None, "SHOW TABLES LIKE 'test_table'"),
            mock.call(None, create_table_string)
        ]
    )


@pytest.mark.parametrize(
    'experiment_configuration_file_path, parameters, fixed_parameter_combination, write_to_database_keys, write_to_database_values',
    [
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
         {'value': [1, 2], 'exponent': [3, 4]},
         [],
         ['value,exponent,status,creation_date'],
         [
             [1, 3, ExperimentStatus.CREATED.value],
             [1, 4, ExperimentStatus.CREATED.value],
             [2, 3, ExperimentStatus.CREATED.value],
             [2, 4, ExperimentStatus.CREATED.value]
        ]),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
         {},
         [{'value': 1, 'exponent': 3}, {'value': 1, 'exponent': 4}],
         ['value,exponent,status,creation_date'],
         [
             [1, 3, ExperimentStatus.CREATED.value],
             [1, 4, ExperimentStatus.CREATED.value],
        ]),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file_3_parameters.cfg'),
         {'value': [1, 2], },
         [{'exponent': 3, 'other_value': 5}],
         ['value,exponent,other_value,status,creation_date'],
         [
             [1, 3, 5, ExperimentStatus.CREATED.value],
             [2, 3, 5, ExperimentStatus.CREATED.value],
        ]
        ),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file_3_parameters.cfg'),
         {'value': [1, 2], 'exponent': [3, 4], },
         [{'other_value': 5}],
         ['value,exponent,other_value,status,creation_date'],
         [
             [1, 3, 5, ExperimentStatus.CREATED.value],
             [1, 4, 5, ExperimentStatus.CREATED.value],
             [2, 3, 5, ExperimentStatus.CREATED.value],
             [2, 4, 5, ExperimentStatus.CREATED.value],
        ]
        ),
    ]
)
@patch.object(database_connector.DatabaseConnector, '_write_to_database')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_get_existing_rows')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
def test_fill_table(
        create_database_if_not_existing_mock,
        test_connection_mock,
        get_existing_rows_mock,
        write_to_database_mock,
        experiment_configuration_file_path,
        parameters,
        fixed_parameter_combination,
        write_to_database_keys,
        write_to_database_values):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mock.return_value = None
    get_existing_rows_mock.return_value = []
    write_to_database_mock.return_value = None

    experiment_configuration = load_config(experiment_configuration_file_path)
    database_connector = DatabaseConnectorMYSQL(
        experiment_configuration,
        database_credential_file_path=os.path.join('test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg'))
    database_connector.fill_table(parameters, fixed_parameter_combination)
    args = write_to_database_mock.call_args_list

    assert len(args) == len(write_to_database_values)
    for expected_args, arg in zip(write_to_database_values, args):
        assert write_to_database_keys == arg[0][0]
        assert expected_args == arg[0][1][:-1]
        datetime_from_string_argument = datetime.datetime.strptime(arg[0][1][-1], '%Y-%m-%d %H:%M:%S')
        assert datetime_from_string_argument.day == datetime.datetime.now().day
        assert datetime_from_string_argument.hour == datetime.datetime.now().hour
        assert datetime_from_string_argument.minute - datetime.datetime.now().minute <= 2


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'connect')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'close_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'cursor')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'execute')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'commit')
def test_delete_experiments_with_condition(commit_mock, execute_mock, cursor_mock, close_conenction_mock, connect_mock, create_database_if_not_existing_mock, _test_connection_mock):
    create_database_if_not_existing_mock.return_value = None
    _test_connection_mock.return_value = None
    connect_mock.return_value = None
    close_conenction_mock.return_value = None
    execute_mock.return_value = None
    cursor_mock.return_value = None
    commit_mock.return_value = None

    experiment_configuration_file_path = load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    database_connector = DatabaseConnectorMYSQL(
        experiment_configuration_file_path,
        database_credential_file_path=os.path.join(
            'test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg')
    )

    database_connector._delete_experiments_with_condition(f'WHERE status = "{ExperimentStatus.CREATED.value}"')

    args = execute_mock.call_args_list
    assert len(args) == 1
    assert args[0][0][1] == f'DELETE FROM test_table WHERE status = "{ExperimentStatus.CREATED.value}"'


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'connect')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'cursor')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'execute')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'commit')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'fetchall')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'get_structure_from_table')
def test_get_experiments_with_condition(get_structture_from_table_mock, fetchall_mock, commit_mock, execute_mock, cursor_mock, connect_mock, create_database_if_not_existing_mock, _test_connection_mock):
    create_database_if_not_existing_mock.return_value = None
    _test_connection_mock.return_value = None
    connect_mock.return_value = None
    execute_mock.return_value = None
    cursor_mock.return_value = None
    commit_mock.return_value = None
    fetchall_mock.return_value = [(1, 2,), ]
    get_structture_from_table_mock.return_value = ['value', 'exponent']
    experiment_configuration_file_path = load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    database_connector = DatabaseConnectorMYSQL(
        experiment_configuration_file_path,
        database_credential_file_path=os.path.join(
            'test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg')
    )
    database_connector._get_experiments_with_condition(f'WHERE status = "{ExperimentStatus.CREATED.value}"')

    assert execute_mock.call_args_list[0][0][1] == f'SELECT * FROM test_table WHERE status = "{ExperimentStatus.CREATED.value}"'


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_test_connection')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'connect')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'cursor')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'execute')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, 'commit')
def test_delete_table(commit_mock, execute_mock, cursor_mock, connect_mock, create_database_if_not_existing_mock, _test_connection_mock):
    create_database_if_not_existing_mock.return_value = None
    _test_connection_mock.return_value = None
    connect_mock.return_value = None
    execute_mock.return_value = None
    cursor_mock.return_value = None
    commit_mock.return_value = None
    experiment_configuration_file_path = load_config(os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'))
    database_connector = DatabaseConnectorMYSQL(
        experiment_configuration_file_path,
        database_credential_file_path=os.path.join(
            'test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg')
    )
    database_connector.delete_table()

    assert execute_mock.call_count == 1
    assert execute_mock.call_args[0][1] == 'DROP TABLE IF EXISTS test_table'
