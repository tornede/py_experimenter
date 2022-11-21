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
    result= {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)


def check_done_entries(experimenter, amount_of_entries):
    connection= experimenter.dbconnector.connect()
    cursor= experimenter.dbconnector.cursor(connection)
    cursor.execute("SELECT * FROM test_table WHERE status = 'done'")
    entries= cursor.fetchall()

    assert amount_of_entries == len(entries)

    experimenter.dbconnector.close_connection(connection)





def test_run_all_sqlite_experiments():
    logging.basicConfig(level=logging.DEBUG)
    experimenter= PyExperimenter(experiment_configuration_file_path=os.path.join('test', 'test_run_experiments', 'test_run_sqlite_experiment_config.cfg'))
    try:
        experimenter.delete_table()
    except Exception:
        pass
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, 1)

    connection= experimenter.dbconnector.connect()
    cursor= experimenter.dbconnector.cursor(connection)
    cursor.execute("SELECT * FROM test_table WHERE status = 'done'")
    entries= cursor.fetchall()

    assert len(entries) == 1
    entries_without_metadata = entries[0][: 3] + (entries[0][4],) + entries[0][6: 7] + entries[0][8: 10] + (entries[0][-1],)
    assert entries_without_metadata == (1, 1, 1, 'done', 'PyExperimenter', '0.8414709848078965', '0.5403023058681398', None)
    experimenter.dbconnector.close_connection(connection)

    experimenter= PyExperimenter(experiment_configuration_file_path=os.path.join('test', 'test_run_experiments', 'test_run_sqlite_experiment_config.cfg'))
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection= experimenter.dbconnector.connect()
    cursor= experimenter.dbconnector.cursor(connection)
    cursor.execute("DELETE FROM test_table WHERE ID = 1")
    experimenter.dbconnector.commit(connection)
    experimenter.dbconnector.close_connection(connection)
    check_done_entries(experimenter, 29)

    experimenter.fill_table_from_config()
    experimenter.execute(own_function, -1)
    check_done_entries(experimenter, 30)
    connection= experimenter.dbconnector.connect()
    cursor= experimenter.dbconnector.cursor(connection)
    cursor.execute("SELECT ID FROM test_table")
    entries= cursor.fetchall()
    experimenter.dbconnector.close_connection(connection)

    assert len(entries) == 30
    assert set(range(2, 32)) == set(entry[0] for entry in entries)
