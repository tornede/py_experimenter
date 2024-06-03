import os
from unittest.mock import patch

import pandas
import pytest

from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.experimenter import PyExperimenter


@pytest.fixture(scope="module")
def experimenter_mysql():
    # Create config directory if it does not exist
    if not os.path.exists("config"):
        os.mkdir("config")

    configuration_path = os.path.join("test", "test_codecarbon", "configs", "test_config_mysql.yml")
    with patch.object(DatabaseConnectorMYSQL, "_test_connection", return_value=None):
        experimenter = PyExperimenter(experiment_configuration_file_path=configuration_path, use_ssh_tunnel=False)

    yield experimenter

    experimenter.delete_table()


def test_delete_table_mysql(experimenter_mysql):
    with patch.object(DatabaseConnectorMYSQL, "connect", return_value=None), patch.object(
        DatabaseConnectorMYSQL, "close_connection", return_value=None
    ), patch.object(DatabaseConnector, "cursor", return_value=None), patch.object(DatabaseConnector, "commit", return_value=None):
        with patch.object(DatabaseConnector, "execute", return_value=None) as mock_execute:
            experimenter_mysql.delete_table()

            assert mock_execute.call_count == 5
            assert mock_execute.call_args_list[0][0][1] == "DROP TABLE IF EXISTS example_logtables__train_scores"
            assert mock_execute.call_args_list[1][0][1] == "DROP TABLE IF EXISTS example_logtables__test_f1"
            assert mock_execute.call_args_list[2][0][1] == "DROP TABLE IF EXISTS example_logtables__test_accuracy"
            assert mock_execute.call_args_list[3][0][1] == "DROP TABLE IF EXISTS example_logtables_codecarbon"
            assert mock_execute.call_args_list[4][0][1] == "DROP TABLE IF EXISTS example_logtables"


def test_get_table_mysql(experimenter_mysql):
    with patch.object(DatabaseConnectorMYSQL, "connect", return_value=None),  patch.object(
        pandas, "read_sql", return_value=pandas.DataFrame()
    ), patch.object(DatabaseConnectorMYSQL, "close_connection", return_value=None) as mock_close:
        df = experimenter_mysql.get_codecarbon_table()

        assert df.empty is True
