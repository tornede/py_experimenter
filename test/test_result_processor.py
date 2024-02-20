import logging
import os

import pytest
from freezegun import freeze_time
from mock import patch

from py_experimenter import database_connector_lite, database_connector_mysql, utils
from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.exceptions import InvalidResultFieldError
from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor

CREDENTIAL_PATH = os.path.join("test", "test_config_files", "load_config_test_file", "mysql_fake_credentials.cfg")


@patch.object(database_connector_lite.DatabaseConnectorLITE, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
@pytest.mark.parametrize(
    "config_path, table_name, expected_provider",
    [
        (os.path.join("test", "test_config_files", "load_config_test_file", "mysql_test_file.yml"), "test_table", DatabaseConnectorMYSQL),
        (os.path.join("test", "test_config_files", "load_config_test_file", "sqlite_test_file.yml"), "test_table", DatabaseConnectorLITE),
    ],
)
def test_init(create_database_if_not_existing_mock, test_connection_mysql, test_connection_sqlite, config_path, table_name, expected_provider):
    create_database_if_not_existing_mock.return_value = None
    test_connection_mysql.return_value = None
    test_connection_sqlite.return_value = None

    logger = logging.getLogger("test_logger")

    experimenter = PyExperimenter(config_path, name="test_logger")
    result_processor = ResultProcessor(experimenter.config.database_configuration, experimenter.db_connector, 0, logger)

    assert table_name == result_processor.database_config.table_name
    assert expected_provider == result_processor.db_connector.__class__


@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
@pytest.mark.parametrize(
    "results,error, errorstring, experiment_id",
    [
        (
            {
                "result_field_1": "result_field_1_value",
                "sin": "result_field_2_value",
            },
            InvalidResultFieldError,
            f"Invalid result keys: {{'result_field_1'}}",
            0,
        ),
    ],
)
def test_process_results_raises_error(create_database_mock, test_connection_mock, results, error, errorstring, experiment_id):
    create_database_mock.return_value = None
    test_connection_mock.return_value = None
    table_name = "test_table"

    experimenter = PyExperimenter(os.path.join("test", "test_config_files", "load_config_test_file", "mysql_test_file.yml"), name="test_logger")
    result_processor = ResultProcessor(experimenter.config.database_configuration, experimenter.db_connector, experiment_id, experimenter.logger)
    with pytest.raises(error, match=errorstring):
        result_processor.process_results(results)


@freeze_time("2020-01-01 00:00:00")
@pytest.mark.parametrize(
    "results, expected_results",
    [
        pytest.param(
            {"result_field_1": "result_field_1_value", "result_field_2": "result_field_2_value"},
            {
                "result_field_1": "result_field_1_value",
                "result_field_1_timestamp": "2020-01-01 00:00:00",
                "result_field_2": "result_field_2_value",
                "result_field_2_timestamp": "2020-01-01 00:00:00",
            },
            id="default_testcase",
        ),
        pytest.param({}, {}, id="empty_testcase"),
        pytest.param(
            {
                "result_field_1": "result_field_1_value",
            },
            {
                "result_field_1": "result_field_1_value",
                "result_field_1_timestamp": "2020-01-01 00:00:00",
            },
            id="one_value_testcase",
        ),
    ],
)
def test_add_timestamps_to_results(results, expected_results):
    assert expected_results == ResultProcessor._add_timestamps_to_results(results)


@pytest.fixture
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_test_connection")
@patch.object(database_connector_mysql.DatabaseConnectorMYSQL, "_create_database_if_not_existing")
def result_processor(test_connection_mock, create_database_mock):
    test_connection_mock.return_value = None
    create_database_mock.return_value = None
    experimenter = PyExperimenter(os.path.join("test", "test_logtables", "mysql_logtables.yml"), name="test_logger")
    result_processor = ResultProcessor(experimenter.config.database_configuration, experimenter.db_connector, 0, experimenter.logger)
    return result_processor


def test_valid_logtable_logs(result_processor: ResultProcessor):
    assert result_processor._valid_logtable_logs({"log": {"test": 0}})
    assert not result_processor._valid_logtable_logs({"log": {"test": 0, "test2": 1}})
