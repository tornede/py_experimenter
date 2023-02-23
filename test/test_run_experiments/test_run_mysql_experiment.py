import logging
import os
from math import cos, sin

import pandas as pd
from mysql.connector.errors import ProgrammingError

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


def own_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(keyfields['value'])**keyfields['exponent']
    cos_result = cos(keyfields['value'])**keyfields['exponent']

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)


def check_done_entries(experimenter, amount_of_entries):
    connection = experimenter.dbconnector.connect()
    cursor = experimenter.dbconnector.cursor(connection)
    cursor.execute(f"SELECT * FROM {experimenter.dbconnector.table_name} WHERE status = 'done'")
    entries = cursor.fetchall()

    assert amount_of_entries == len(entries)

    experimenter.dbconnector.close_connection(connection)


def test_run_all_mqsql_experiments():
    experiment_configuration_file_path = os.path.join('test', 'test_run_experiments', 'test_run_mysql_experiment_config.cfg')
    logging.basicConfig(level=logging.DEBUG)
    experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration_file_path)
    try:
        experimenter.delete_table()
    except ProgrammingError as e:
        logging.warning(e)
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, 1)

    connection = experimenter.dbconnector.connect()
    cursor = experimenter.dbconnector.cursor(connection)
    cursor.execute(f"SELECT * FROM {experimenter.dbconnector.table_name} WHERE status = 'done'")
    entries = cursor.fetchall()

    assert len(entries) == 1
    entries_without_metadata = entries[0][:3] + (entries[0][4],) + entries[0][6:7] + entries[0][8:10] + (entries[0][-1],)
    assert entries_without_metadata == (1, 1, 1, 'done', 'PyExperimenter', '0.8414709848078965', '0.5403023058681398', None)
    experimenter.dbconnector.close_connection(connection)

    experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration_file_path)
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter.dbconnector.connect()
    cursor = experimenter.dbconnector.cursor(connection)
    cursor.execute(f"DELETE FROM {experimenter.dbconnector.table_name} WHERE ID = 1")
    experimenter.dbconnector.commit(connection)
    experimenter.dbconnector.close_connection(connection)
    check_done_entries(experimenter, 29)

    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter.dbconnector.connect()
    cursor = experimenter.dbconnector.cursor(connection)
    cursor.execute(f"SELECT ID FROM {experimenter.dbconnector.table_name}")
    entries = cursor.fetchall()
    experimenter.dbconnector.close_connection(connection)

    assert len(entries) == 30
    assert set(range(2, 32)) == set(entry[0] for entry in entries)


def error_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    raise Exception("Error with weird symbos '@#$%&/\()=")


def check_error_entries(experimenter):
    connection = experimenter.dbconnector.connect()
    cursor = experimenter.dbconnector.cursor(connection)
    cursor.execute(f"SELECT * FROM {experimenter.dbconnector.table_name} WHERE status = 'error'")
    entries = cursor.fetchall()
    experimenter.dbconnector.close_connection(connection)
    return entries


def test_run_error_experiment():
    experiment_configuration_file_path = os.path.join('test', 'test_run_experiments', 'test_run_mysql_experiment_config.cfg')
    logging.basicConfig(level=logging.DEBUG)
    experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration_file_path)
    try:
        experimenter.delete_table()
    except ProgrammingError as e:
        logging.warning(e)
    experimenter.fill_table_from_config()
    experimenter.execute(error_function, 1)

    entries = check_error_entries(experimenter)
    assert entries[0][:3] == (1, 1, 1)
    assert entries[0][4] == 'error'
    assert entries[0][6] == 'PyExperimenter'
    assert entries[0][7] == 'vm-tornede4'
    assert entries[0][8] == None
    assert entries[0][9] == None
    assert entries[0][11] == ('Traceback (most recent call last):\n  File'
                              f' "{os.path.join(os.getcwd(),"py_experimenter","experimenter")}.py"'
                              ', line 403, in _execution_wrapper\n    experiment_function(keyfield_values, result_processor,'
                              f' custom_fields)\n  File "{os.path.join(os.getcwd(), "test", "test_run_experiments", "test_run_mysql_experiment")}'
                              '.py", line 81, in error_function\n    '
                              'raise Exception("Error with weird symbos \'@#$%&/\\()=")\nException: Error with weird symbos \'@#$%&/\\()=\n')


def own_function_raising_errors(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    error_code = keyfields['error_code']

    # give list of special characters that frequently cause problems
    characters = ['"', "'", '@', '#', '$', '%', '&', '/', '\\', '(', ')', '=', "`", "`some_text`", "^"]
    if error_code == 0:
        raise Exception("Error with weird symbos" + "".join(characters))
    elif error_code == 1:
        raise LookupError("Error with weird symbos" + "".join(characters))
    elif error_code == 2:
        raise ProgrammingError("Error with weird symbos" + "".join(characters))


def test_raising_error_experiment():
    experimenter = PyExperimenter(experiment_configuration_file_path=os.path.join('test', 'test_run_experiments', 'test_run_mysql_error_config.cfg'),
                                  name='name')

    try:
        experimenter.delete_table()
    except ProgrammingError as e:
        logging.warning(e)

    experimenter.fill_table_from_config()
    experimenter.execute(own_function_raising_errors, -1)
    table = experimenter.get_table()
    'lala'
    table = table[['ID', 'error_code', 'status', 'name']]
    pd.testing.assert_frame_equal(
        table,
        pd.DataFrame(
            {
                'ID': [1, 2, 3],
                'error_code': [0., 1., 2.],
                'status': ['error', 'error', 'error'],
                'name': ['name', 'name', 'name'],
            }
        )
    )

    
    