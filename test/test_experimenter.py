import os

import pytest
from mock import patch

from py_experimenter import database_connector, database_connector_mysql
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.experimenter import PyExperimenter

CREDENTIAL_PATH = os.path.join("test", "test_config_files", "load_config_test_file", "mysql_fake_credentials.cfg")


@patch.object(database_connector.DatabaseConnector, "__init__")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
@pytest.mark.parametrize(
    "config_file, table_name, database_name, expected_table_name, expected_database_name, expected_db_connector_class",
    [
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "mysql_test_file.yml"),
            None,
            None,
            "test_table",
            "py_experimenter",
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "mysql_test_file.yml"),
            "changed_table_name",
            None,
            "changed_table_name",
            "py_experimenter",
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "mysql_test_file.yml"),
            None,
            "changed_database_name",
            "test_table",
            "changed_database_name",
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "mysql_test_file.yml"),
            "changed_table_name",
            "changed_database_name",
            "changed_table_name",
            "changed_database_name",
            DatabaseConnectorMYSQL,
        ),
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "sqlite_test_file.yml"),
            None,
            None,
            "test_table",
            "py_experimenter",
            DatabaseConnectorLITE,
        ),
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "sqlite_test_file.yml"),
            "change_table_name",
            None,
            "change_table_name",
            "py_experimenter",
            DatabaseConnectorLITE,
        ),
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "sqlite_test_file.yml"),
            None,
            "changed_db_name",
            "test_table",
            "changed_db_name",
            DatabaseConnectorLITE,
        ),
        (
            os.path.join("test", "test_config_files", "load_config_test_file", "sqlite_test_file.yml"),
            "change_table_name",
            "changed_db_name",
            "change_table_name",
            "changed_db_name",
            DatabaseConnectorLITE,
        ),
    ],
)
def test_init(
    create_database_if_not_existing_mock,
    mock_fn,
    config_file,
    table_name,
    database_name,
    expected_table_name,
    expected_database_name,
    expected_db_connector_class,
):
    mock_fn.return_value = None
    create_database_if_not_existing_mock.return_value = None
    experimenter = PyExperimenter(
        config_file,
        os.path.join("test", "test_config_files", "load_config_test_file", "mysql_fake_credentials.cfg"),
        False,
        table_name,
        database_name,
    )

    assert experimenter.config.database_configuration.table_name == expected_table_name
    assert experimenter.config.database_configuration.database_name == expected_database_name
    assert experimenter.db_connector.__class__ == expected_db_connector_class
