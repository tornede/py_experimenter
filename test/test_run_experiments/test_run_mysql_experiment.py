import logging
import os
from math import cos, sin

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
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute(f"SELECT * FROM {experimenter._dbconnector._table_name} WHERE status = 'done'")
    entries = cursor.fetchall()

    assert amount_of_entries == len(entries)

    experimenter._dbconnector.close_connection(connection)


def delete_existing_table(experimenter):
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    try:
        cursor.execute(f"DROP TABLE {experimenter._dbconnector._table_name}")
        experimenter._dbconnector.commit(connection)
        experimenter._dbconnector.close_connection(connection)
    except ProgrammingError as e:
        experimenter._dbconnector.close_connection(connection)
        logging.warning(e)


def test_run_all_mqsql_experiments():
    config_file = os.path.join('test', 'test_run_experiments', 'test_run_mysql_experiment_config.cfg')
    logging.basicConfig(level=logging.DEBUG)
    experimenter = PyExperimenter(config_file=config_file)
    try:
        delete_existing_table(experimenter)
    except ProgrammingError as e:
        logging.warning(e)
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, 1)

    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute(f"SELECT * FROM {experimenter._dbconnector._table_name} WHERE status = 'done'")
    entries = cursor.fetchall()

    assert len(entries) == 1
    entries_without_metadata = entries[0][:3] + (entries[0][4],) + entries[0][6:7] + entries[0][8:10] + (entries[0][-1],)
    assert entries_without_metadata == (1, 1, 1, 'done', 'PyExperimenter', '0.8414709848078965', '0.5403023058681398', None)
    experimenter._dbconnector.close_connection(connection)

    experimenter = PyExperimenter(config_file=config_file)
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute(f"DELETE FROM {experimenter._dbconnector._table_name} WHERE ID = 1")
    experimenter._dbconnector.commit(connection)
    experimenter._dbconnector.close_connection(connection)
    check_done_entries(experimenter, 29)

    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection = experimenter._dbconnector.connect()
    cursor = experimenter._dbconnector.cursor(connection)
    cursor.execute(f"SELECT ID FROM {experimenter._dbconnector._table_name}")
    entries = cursor.fetchall()
    experimenter._dbconnector.close_connection(connection)

    assert len(entries) == 30
    assert set(range(2, 32)) == set(entry[0] for entry in entries)
