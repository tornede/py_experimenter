import os

import pytest
from mock import patch

from py_experimenter import database_connector, database_connector_mysql, experimenter, utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.experimenter import PyExperimenter

CREDENTIAL_PATH = os.path.join('test', 'test_config_files', 'load_config_test_file', 'mysql_fake_credentials.cfg')


@patch.object(database_connector.DatabaseConnector, '__init__')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@pytest.mark.parametrize(
    'config_file, table_name, database_name, expected_table_name, expected_database_name, expected_db_connector_class',
    [
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            None,
            None,
            'test_table',
            'py_experimenter',
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'changed_table_name',
            None,
            'changed_table_name',
            'py_experimenter',
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            None,
            'changed_database_name',
            'test_table',
            'changed_database_name',
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'changed_table_name',
            'changed_database_name',
            'changed_table_name',
            'changed_database_name',
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg'),
            None,
            None,
            'test_table_sqlite',
            'py_experimenter',
            DatabaseConnectorLITE,
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg'),
            'change_table_name',
            None,
            'change_table_name',
            'py_experimenter',
            DatabaseConnectorLITE,
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg'),
            None,
            'changed_db_name',
            'test_table_sqlite',
            'changed_db_name',
            DatabaseConnectorLITE,
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg'),
            'change_table_name',
            'changed_db_name',
            'change_table_name',
            'changed_db_name',
            DatabaseConnectorLITE,
        ),

    ]
)
def test_init(create_database_if_not_existing_mock, mock_fn, config_file, table_name, database_name, expected_table_name, expected_database_name, expected_db_connector_class):
    mock_fn.return_value = None
    create_database_if_not_existing_mock.return_value = None
    experimenter = PyExperimenter(config_file, os.path.join('test', 'test_config_files', 'load_config_test_file',
                                  'mysql_fake_credentials.cfg'), table_name, database_name)

    assert experimenter.get_config_value('PY_EXPERIMENTER', 'table') == expected_table_name
    assert experimenter.get_config_value('PY_EXPERIMENTER', 'database') == expected_database_name
    assert experimenter._dbconnector.__class__ == expected_db_connector_class


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '__init__')
@patch.object(experimenter.PyExperimenter, '_valid_configuration')
@pytest.mark.parametrize(
    'config_file, section_name, key, expected_value',
    [
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'PY_EXPERIMENTER',
            'table',
            'test_table',
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'PY_EXPERIMENTER',
            'cpu.max',
            '5',
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'PY_EXPERIMENTER',
            'value',
            '1,2,3,4,5,6,7,8,9,10',
        ),
    ]
)
def test_get_config_values(mock_valid_config, mcok_database_connector_init, config_file, section_name, key, expected_value):
    mock_valid_config.return_value = True
    mcok_database_connector_init.return_value = None
    assert expected_value == PyExperimenter(config_file).get_config_value(section_name, key)


@patch.object(database_connector.DatabaseConnector, '__init__')
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, '_create_database_if_not_existing')
@pytest.mark.parametrize(
    'config_file, section_name, key, value',
    [
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'DATABASE',
            'table',
            'example_table',
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'PY_EXPERIMENTER',
            'cpu.max',
            '5',
        ),
        (
            os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'),
            'PY_EXPERIMENTER',
            'value',
            '1,2,3,4,5,6,7,8,9,10',
        ),
    ]
)
def test_set_config_values(create_database_if_not_existing_mock, mock_fn, config_file, section_name, key, value):
    create_database_if_not_existing_mock.return_value = None
    mock_fn.return_value = None
    py_experimenter = PyExperimenter(config_file, CREDENTIAL_PATH)
    py_experimenter.set_config_value(section_name, key, value)
    assert py_experimenter.get_config_value(section_name, key) == value


@pytest.mark.parametrize(
    'config_file, valid',
    [
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_file_with_wrong_syntax.cfg'), True),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file_without_keyfields.cfg'), True),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'my_sql_test_file.cfg'), True),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'sqlite_test_file.cfg'), True),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'test_config_with_disallowed_characters.cfg'), True),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'invalid_config_1.cfg'), False),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'invalid_config_2.cfg'), False),
        (os.path.join('test', 'test_config_files', 'load_config_test_file', 'invalid_config_3.cfg'), False),
    ]
)
def test_valid_configuration(config_file, valid):
    config_file = utils.load_config(config_file)
    assert PyExperimenter._valid_configuration(config_file, CREDENTIAL_PATH) == valid
