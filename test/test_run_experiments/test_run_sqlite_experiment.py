import logging
import os
import socket
from math import cos, sin
from tempfile import TemporaryFile

from pymysql.err import ProgrammingError
import pandas as pd

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


def own_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(keyfields["value"]) ** keyfields["exponent"]
    cos_result = cos(keyfields["value"]) ** keyfields["exponent"]

    # write result in dict with the resultfield as key
    result = {"sin": sin_result, "cos": cos_result}

    # send result to to the database
    result_processor.process_results(result)


def check_done_entries(experimenter, amount_of_entries):
    connection = experimenter.db_connector.connect()
    cursor = experimenter.db_connector.cursor(connection)
    cursor.execute("SELECT * FROM test_table WHERE status = 'done'")
    entries = cursor.fetchall()

    assert amount_of_entries == len(entries)

    experimenter.db_connector.close_connection(connection)


def test_run_all_sqlite_experiments():
    logging.basicConfig(level=logging.DEBUG)
    config_path = os.path.join("test", "test_run_experiments", "test_run_sqlite_experiment_config.yml")
    experimenter = PyExperimenter(config_path, use_codecarbon=False)
    try:
        experimenter.delete_table()
    except Exception:
        pass
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, max_experiments=1)

    connection = experimenter.db_connector.connect()
    cursor = experimenter.db_connector.cursor(connection)
    cursor.execute("SELECT * FROM test_table WHERE status = 'done'")
    entries = cursor.fetchall()

    assert len(entries) == 1
    entries_without_metadata = entries[0][:3] + (entries[0][4],) + entries[0][6:7] + entries[0][8:10] + (entries[0][-1],)
    assert entries_without_metadata == (1, 1, 1, "done", "PyExperimenter", 0.8414709848078965, 0.5403023058681398, None)
    experimenter.db_connector.close_connection(connection)

    experimenter = PyExperimenter(config_path, use_codecarbon=False)
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter.db_connector.connect()
    cursor = experimenter.db_connector.cursor(connection)
    cursor.execute("DELETE FROM test_table WHERE ID = 1")
    experimenter.db_connector.commit(connection)
    experimenter.db_connector.close_connection(connection)
    check_done_entries(experimenter, 29)

    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter.db_connector.connect()
    cursor = experimenter.db_connector.cursor(connection)
    cursor.execute("SELECT ID FROM test_table")
    entries = cursor.fetchall()
    experimenter.db_connector.close_connection(connection)

    assert len(entries) == 30
    assert set(range(2, 32)) == set(entry[0] for entry in entries)


def error_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    raise Exception("Error with weird symbos '@#$%&/\()=")


def check_error_entries(experimenter: PyExperimenter):
    connection = experimenter.db_connector.connect()
    cursor = experimenter.db_connector.cursor(connection)
    cursor.execute(f"SELECT * FROM {experimenter.config.database_configuration.table_name} WHERE status = 'error'")
    entries = cursor.fetchall()
    experimenter.db_connector.close_connection(connection)
    return entries


def test_run_error_experiment():
    experiment_configuration_file_path = os.path.join("test", "test_run_experiments", "test_run_sqlite_experiment_config.yml")
    logging.basicConfig(level=logging.DEBUG)
    experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration_file_path, use_codecarbon=False)
    try:
        experimenter.delete_table()
    except ProgrammingError as e:
        logging.warning(e)
    experimenter.fill_table_from_config()
    experimenter.execute(error_function, 1)

    entries = check_error_entries(experimenter)
    assert entries[0][:3] == (1, 1, 1)
    assert entries[0][4] == "error"
    assert entries[0][6] == "PyExperimenter"
    assert entries[0][7] == socket.gethostname()
    assert entries[0][8] == None
    assert entries[0][9] == None
    for message in [
        "in _execute_experiment",
        "experiment_function(keyfield_values, result_processor, self.config.custom_configuration.custom_values)",
        "raise Exception(",
        "Error with weird symbos '@#$%&/\\()=",
    ]:
        assert message in entries[0][11]


def own_function_raising_errors(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    error_code = keyfields["error_code"]

    # give list of special characters that frequently cause problems
    characters = ['"', "'", "@", "#", "$", "%", "&", "/", "\\", "(", ")", "=", "`", "`some_text`", "^"]
    if error_code == 0:
        raise Exception("Error with weird symbos" + "".join(characters))
    elif error_code == 1:
        raise LookupError("Error with weird symbos" + str(characters))
    elif error_code == 2:
        raise ProgrammingError("Error with weird symbos" + str(characters))


def test_raising_error_experiment():
    path = os.path.join('test', 'test_run_experiments', 'test_run_sqlite_error_config.yml')
    experimenter = PyExperimenter(experiment_configuration_file_path=path, name='name', use_codecarbon=False)

    try:
        experimenter.delete_table()
    except ProgrammingError as e:
        logging.warning(e)

    experimenter.fill_table_from_config()
    experimenter.execute(own_function_raising_errors, -1)
    table = experimenter.get_table()
    table = table[['ID', 'error_code', 'status', 'name']]
    pd.testing.assert_frame_equal(
        table,
        pd.DataFrame(
            {
                'ID': [1, 2, 3],
                'error_code': [0, 1, 2],
                'status': ['error', 'error', 'error'],
                'name': ['name', 'name', 'name'],
            }
        )
    )

def run_boolean_experiment(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    if keyfields["value"] == True:
        result = True
        result_processor.process_results({"given_bool": result})
    elif keyfields["value"] == False:
        result = False
        result_processor.process_results({"given_bool": result})

def test_boolean_in_table():
    path = os.path.join('test',"test_run_experiments",  'sqlite_bool_test_file.yml')
    
    experimenter = PyExperimenter(experiment_configuration_file_path=path, name='name', use_codecarbon=False)
    experimenter.delete_table()
    experimenter.fill_table_from_config() 
    experimenter.execute(run_boolean_experiment, 2)
    
    table = experimenter.get_table()
    assert table["given_bool"].dtype == int
    assert table["value"].dtype == int
    assert (table["value"] == [1,0]).all()
    assert (table["given_bool"] == [1,0]).all()
    assert (table["status"] == ["done", "done"]).all()
    