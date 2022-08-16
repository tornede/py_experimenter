import logging
from math import cos, sin

from mysql.connector.errors import ProgrammingError

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


def own_function(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(parameters['value'])**parameters['exponent']
    cos_result = cos(parameters['value'])**parameters['exponent']

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)


def check_done_entries(experimenter, amount_of_entries):
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute("SELECT * FROM test_table WHERE status = 'done'")
    entries = cursor.fetchall()

    assert amount_of_entries == len(entries)

    experimenter._dbconnector.close_connection(connection)


def delete_existing_table(experimenter):
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    try:
        cursor.execute("DROP TABLE IF EXISTS test_table")
        experimenter._dbconnector.commit(connection)
        experimenter._dbconnector.close_connection(connection)
    except ProgrammingError:
        experimenter._dbconnector.close_connection(connection)
        logging.warning("Table test_table does not exist")


def test_run_all_sqlite_experiments():
    logging.basicConfig(level=logging.DEBUG)
    experimenter = PyExperimenter(config_path='test/test_run_experiments/test_run_sqlite_experiment_config.cfg')
    delete_existing_table(experimenter)
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, 1)

    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute("SELECT * FROM test_table WHERE status = 'done'")
    entries = cursor.fetchall()

    assert len(entries) == 1
    assert entries[0][:6] == (1, 1, 1, '0.8414709848078965', '0.5403023058681398', 'done')
    experimenter._dbconnector.close_connection(connection)

    experimenter = PyExperimenter(config_path='test/test_run_experiments/test_run_sqlite_experiment_config.cfg')
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute("DELETE FROM test_table WHERE ID = 1")
    experimenter._dbconnector.commit(connection)
    experimenter._dbconnector.close_connection(connection)
    check_done_entries(experimenter, 29)

    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute("SELECT ID FROM test_table")
    entries = cursor.fetchall()
    experimenter._dbconnector.close_connection(connection)

    assert len(entries) == 30
    assert set(range(2, 32)) == set(entry[0] for entry in entries)
