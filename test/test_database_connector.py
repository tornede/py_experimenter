import datetime
import logging
import os

import pytest
from mock import patch
from omegaconf import OmegaConf

from py_experimenter import database_connector, database_connector_lite, database_connector_mysql, utils
from py_experimenter.config import DatabaseCfg
from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.experiment_status import ExperimentStatus
from py_experimenter.experimenter import PyExperimenter

CONFIG_PATH = os.path.join("test", "test_config_files", "load_config_test_file", "sqlite_test_file.yml")
CREDENTIAL_PATH = os.path.join("test", "test_config_files", "load_config_test_file", "mysql_fake_credentials.cfg")


@patch.object(database_connector.DatabaseConnector, "_test_connection")
def test_constructor(test_connetion_mock):
    test_connetion_mock.return_value = None

    config = OmegaConf.load(CONFIG_PATH)

    logger = logging.getLogger("test_logger")
    config = DatabaseCfg.extract_config(config, logger)
    connector = DatabaseConnectorLITE(config, False, logger)

    assert connector.database_configuration == config
    assert connector.logger == logger
    assert connector.use_codecarbon == False

    assert list(config.keyfields.keys()) == ["value", "exponent"]


@pytest.mark.parametrize(
    "combination, existing_rows, result",
    [
        ({"value": 1, "exponent": 2}, [{"value": 1, "exponent": 2}], True),
        ({"value": 1, "exponent": 2}, [], False),
        ({"value": 3, "exponent": 4}, [{"value": 1, "exponent": 2}, {"value": 3, "exponent": 4}], True),
        ({"value": 1, "exponent": 4}, [{"value": 1, "exponent": 2}, {"value": 3, "exponent": 4}], False),
        ({"value": 1}, [{"value": 1}], True),
        ({"value": 1}, [{"value": 2}], False),
    ],
)
def test_check_combination_in_existing_rows(combination, existing_rows, result):
    assert result == DatabaseConnector._check_combination_in_existing_rows(None, combination, existing_rows)


@pytest.fixture
@patch.object(database_connector_lite.DatabaseConnectorLITE, "_test_connection")
def connector(test_connection_mock):
    test_connection_mock.return_value = None
    experimenter = PyExperimenter(CONFIG_PATH, use_codecarbon=False)
    connector = experimenter.db_connector
    return connector


@patch.object(database_connector_lite.DatabaseConnectorLITE, "connect")
@patch.object(database_connector_lite.DatabaseConnectorLITE, "cursor")
@patch.object(database_connector_lite.DatabaseConnectorLITE, "_table_exists")
@patch.object(database_connector.DatabaseConnector, "execute")
@patch.object(database_connector.DatabaseConnector, "close_connection")
def test_create_table_if_not_existing(
    close_connection_mock, execute_mock, table_exists_mock, cursor_mock, connection_mock, connector: DatabaseConnector
):
    connection_mock.return_value = None
    cursor_mock.return_value = None
    table_exists_mock.return_value = False
    execute_mock.return_value = None
    close_connection_mock.return_value = None

    connector.create_table_if_not_existing()

    expected_crate_table_statement = (
        "CREATE TABLE test_table (ID INTEGER PRIMARY KEY AUTOINCREMENT, value int DEFAULT NULL,exponent int DEFAULT NULL,"
        "creation_date DATETIME DEFAULT NULL,status VARCHAR(255) DEFAULT NULL,start_date DATETIME DEFAULT NULL,"
        "name LONGTEXT DEFAULT NULL,machine VARCHAR(255) DEFAULT NULL,sin FLOAT DEFAULT NULL,cos FLOAT DEFAULT NULL,"
        "end_date DATETIME DEFAULT NULL,error LONGTEXT DEFAULT NULL);"
    )

    assert execute_mock.call_count == 1
    assert execute_mock.call_args[0][1] == expected_crate_table_statement


@pytest.mark.parametrize(
    "experiment_configuration_file_path, parameters, write_to_database_keys, write_to_database_values",
    [
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "mysql_test_file.yml"),
            [{"value": 1, "exponent": 3}, {"value": 1, "exponent": 4}, {"value": 2, "exponent": 3}, {"value": 2, "exponent": 4}],
            ["value", "exponent", "creation_date", "status"],
            [
                {"value": 1, "exponent": 3, "status": "created"},
                {"value": 1, "exponent": 4, "status": "created"},
                {"value": 2, "exponent": 3, "status": "created"},
                {"value": 2, "exponent": 4, "status": "created"},
            ],
        ),
    ],
)
@patch.object(database_connector.DatabaseConnector, "_write_to_database")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_get_existing_rows")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
def test_fill_table(
    create_database_if_not_existing_mock,
    test_connection_mock,
    get_existing_rows_mock,
    write_to_database_mock,
    experiment_configuration_file_path,
    parameters,
    write_to_database_keys,
    write_to_database_values,
):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mock.return_value = None
    get_existing_rows_mock.return_value = []
    write_to_database_mock.return_value = None
    logger = logging.getLogger("test_logger")

    config = OmegaConf.load(experiment_configuration_file_path)
    experiment_configuration = DatabaseCfg.extract_config(config, logger)
    database_connector = DatabaseConnectorMYSQL(
        experiment_configuration,
        False,
        CREDENTIAL_PATH,
        logger=logger,
    )

    database_connector.fill_table(parameters)
    combinations = write_to_database_mock.call_args_list[0][0][0]

    assert isinstance(combinations, list)
    assert len(combinations) == len(write_to_database_values)
    for combination, expected_entry in zip(combinations, write_to_database_values):
        assert list(combination.keys()) == write_to_database_keys
        assert isinstance(combination, dict)
        entry_without_date = {key: value for key, value in combination.items() if key != "creation_date"}
        assert expected_entry == entry_without_date
        datetime_from_string_argument = datetime.datetime.strptime(combination["creation_date"], "%Y-%m-%d %H:%M:%S")
        assert datetime_from_string_argument.day == datetime.datetime.now().day
        assert datetime_from_string_argument.hour == datetime.datetime.now().hour
        assert datetime_from_string_argument.minute - datetime.datetime.now().minute <= 2


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "connect")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "start_ssh_tunnel")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "close_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "cursor")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "execute")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "commit")
def test_delete_experiments_with_condition(
    commit_mock, execute_mock, cursor_mock, close_conenction_mock, ssh_mock, connect_mock, create_database_if_not_existing_mock, _test_connection_mock
):
    create_database_if_not_existing_mock.return_value = None
    _test_connection_mock.return_value = None
    connect_mock.return_value = None
    ssh_mock.return_value = None
    close_conenction_mock.return_value = None
    execute_mock.return_value = None
    cursor_mock.return_value = None
    commit_mock.return_value = None
    logger = logging.getLogger("test_logger")

    config = OmegaConf.load(CONFIG_PATH)
    experiment_configuration = DatabaseCfg.extract_config(config, logger)
    database_connector = DatabaseConnectorMYSQL(experiment_configuration, False, CREDENTIAL_PATH, logger=logger)

    database_connector._delete_experiments_with_condition(f'WHERE status = "{ExperimentStatus.CREATED.value}"')

    args = execute_mock.call_args_list
    assert len(args) == 1
    assert args[0][0][1] == f'DELETE FROM test_table WHERE status = "{ExperimentStatus.CREATED.value}"'


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "connect")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "cursor")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "execute")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "commit")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "fetchall")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "get_structure_from_table")
def test_get_experiments_with_condition(
    get_structture_from_table_mock,
    fetchall_mock,
    commit_mock,
    execute_mock,
    cursor_mock,
    connect_mock,
    create_database_if_not_existing_mock,
    _test_connection_mock,
):
    create_database_if_not_existing_mock.return_value = None
    _test_connection_mock.return_value = None
    connect_mock.return_value = None
    execute_mock.return_value = None
    cursor_mock.return_value = None
    commit_mock.return_value = None

    get_structture_from_table_mock.return_value = ["value", "exponent"]

    fetchall_mock.return_value = [
        (
            1,
            2,
        ),
    ]
    logger = logging.getLogger("test_logger")

    config = OmegaConf.load(CONFIG_PATH)
    experiment_configuration = DatabaseCfg.extract_config(config, logger)
    database_connector = DatabaseConnectorMYSQL(experiment_configuration, False, CREDENTIAL_PATH, logger=logger)

    database_connector._get_experiments_with_condition(f'WHERE status = "{ExperimentStatus.CREATED.value}"')

    assert execute_mock.call_args_list[0][0][1] == f'SELECT * FROM test_table WHERE status = "{ExperimentStatus.CREATED.value}"'


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "connect")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "close_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "cursor")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "execute")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "commit")
def test_delete_table(
    commit_mock, execute_mock, cursor_mock, close_connection_mock, connect_mock, create_database_if_not_existing_mock, _test_connection_mock
):
    create_database_if_not_existing_mock.return_value = None
    _test_connection_mock.return_value = None
    connect_mock.return_value = None
    close_connection_mock.return_value = None
    execute_mock.return_value = None
    cursor_mock.return_value = None
    commit_mock.return_value = None

    logger = logging.getLogger("test_logger")

    config = OmegaConf.load(CONFIG_PATH)
    experiment_configuration = DatabaseCfg.extract_config(config, logger)
    database_connector = DatabaseConnectorMYSQL(experiment_configuration, False, CREDENTIAL_PATH, logger=logger)

    database_connector.delete_table()

    assert execute_mock.call_count == 1
    assert execute_mock.call_args[0][1] == "DROP TABLE IF EXISTS test_table"
