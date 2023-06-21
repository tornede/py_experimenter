import os
from unittest.mock import patch

import pandas
import pytest

from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.experimenter import PyExperimenter


@pytest.fixture(scope='module')
def experimenter_sqlite():
    # Create config directory if it does not exist
    if not os.path.exists('config'):
        os.mkdir('config')

    # Create config file
    content = """
    [PY_EXPERIMENTER]
    provider = sqlite 
    database = py_experimenter
    table = example_logtables
    
    keyfields = dataset, cross_validation_splits:int, seed:int
    dataset = iris
    cross_validation_splits = 5
    seed = 1,2,3,4,5
    
    resultfields = best_kernel_f1:VARCHAR(50), best_kernel_accuracy:VARCHAR(50)
    resultfields.timestamps = false
    
    logtables = train_scores:log_train_scores, test_f1:DOUBLE, test_accuracy:DOUBLE 
    log_train_scores = f1:DOUBLE, accuracy:DOUBLE, kernel:VARCHAR(50)
    
    [CUSTOM] 
    path = sample_data
    """
    experiment_configuration = os.path.join('config', 'example_logtables.cfg')
    with open(experiment_configuration, "w") as f:
        f.write(content)

    experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration, name='example_notebook')
    yield experimenter

    experimenter.delete_table()


def test_delete_table_sqlite(experimenter_sqlite):
    with patch.object(DatabaseConnector, 'connect', return_value=None), \
            patch.object(DatabaseConnector, 'cursor', return_value=None), \
            patch.object(DatabaseConnector, 'commit', return_value=None):

        with patch.object(DatabaseConnector, 'execute', return_value=None) as mock_execute:
            experimenter_sqlite.delete_table()

            assert mock_execute.call_count == 5
            assert mock_execute.call_args_list[0][0][1] == 'DROP TABLE IF EXISTS example_logtables__train_scores'
            assert mock_execute.call_args_list[1][0][1] == 'DROP TABLE IF EXISTS example_logtables__test_f1'
            assert mock_execute.call_args_list[2][0][1] == 'DROP TABLE IF EXISTS example_logtables__test_accuracy'
            assert mock_execute.call_args_list[3][0][1] == 'DROP TABLE IF EXISTS example_logtables_codecarbon'
            assert mock_execute.call_args_list[4][0][1] == 'DROP TABLE IF EXISTS example_logtables'


def test_get_table_sqlite(experimenter_sqlite):
    with patch.object(DatabaseConnector, 'connect', return_value=None), \
            patch.object(pandas, 'read_sql', return_value=pandas.DataFrame()), \
            patch.object(DatabaseConnector, 'close_connection', return_value=None) as mock_close:

        df = experimenter_sqlite.get_codecarbon_table()

        assert df.empty is True
