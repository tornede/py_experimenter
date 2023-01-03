import os
from configparser import ConfigParser
from math import cos, sin

from mock import call, patch

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


@patch('py_experimenter.experimenter.DatabaseConnectorLITE._table_exists')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE._test_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.fill_table')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.connect')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.cursor')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.fetchall')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.close_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.execute')
def test_tables_created(execute_mock, close_connection_mock, fetchall_mock, cursor_mock, connect_mock, fill_table_mock, test_connection_mock, table_exists_mock):
    execute_mock.return_value = None
    fetchall_mock.return_value = None
    close_connection_mock.return_value = None
    cursor_mock.return_value = None
    connect_mock.return_value = None
    fill_table_mock.return_value = None
    test_connection_mock.return_value = None
    table_exists_mock.return_value = False
    experimenter = PyExperimenter(os.path.join('test', 'test_logtables', 'sqlite_logtables.cfg'))
    experimenter.fill_table_from_config()
    assert execute_mock.mock_calls[0][1][1] == ('CREATE TABLE test_sqlite_logtables (ID INTEGER PRIMARY KEY AUTOINCREMENT, value int DEFAULT NULL,'
                                                'exponent int DEFAULT NULL,creation_date VARCHAR(255) DEFAULT NULL,status VARCHAR(255) DEFAULT NULL,'
                                                'start_date VARCHAR(255) DEFAULT NULL,name LONGTEXT DEFAULT NULL,machine VARCHAR(255) DEFAULT NULL,'
                                                'sin VARCHAR(255) DEFAULT NULL,cos VARCHAR(255) DEFAULT NULL,end_date VARCHAR(255) DEFAULT NULL,'
                                                'error LONGTEXT DEFAULT NULL);')
    assert execute_mock.mock_calls[1][1][1] == ('CREATE TABLE test_sqlite_log (ID INTEGER PRIMARY KEY AUTOINCREMENT, test int DEFAULT NULL,'
                                                'experiment_id INTEGER, FOREIGN KEY (experiment_id) REFERENCES test_sqlite_logtables(ID) ON DELETE CASCADE);')


@patch('py_experimenter.result_processor.DatabaseConnectorLITE')
def test_logtable_insertion(database_connector_mock):
    config = ConfigParser()
    config.read(os.path.join('test', 'test_logtables', 'sqlite_logtables.cfg'))
    result_processor = ResultProcessor(config, None, None, None, 0)
    result_processor.process_logs({'test_table_0': {'test0': 'test', 'test1': 'test'},
                                   'test_table_1': {'test0': 'test'}})
    result_processor._dbconnector.execute_queries.assert_called()
    result_processor._dbconnector.execute_queries.assert_called_with(
        ['INSERT INTO test_table_0 (test0, test1, experiment_id) VALUES (test, test, 0)',
         'INSERT INTO test_table_1 (test0, experiment_id) VALUES (test, 0)'])


@patch('py_experimenter.experimenter.DatabaseConnectorLITE._test_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.connect')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.cursor')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.commit')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.fetchall')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.close_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorLITE.execute')
def test_delete_logtable(execution_mock, close_connection_mock, commit_mocck, fetchall_mock, cursor_mock, connect_mock, test_connection_mock):
    fetchall_mock.return_value = cursor_mock.return_value = connect_mock.return_value = commit_mocck.return_value = None
    close_connection_mock.return_value = test_connection_mock.return_value = execution_mock.return_value = None
    experimenter = PyExperimenter(os.path.join('test', 'test_logtables', 'sqlite_logtables.cfg'))
    experimenter.delete_table()
    execution_mock.assert_has_calls([call(None, 'DROP TABLE IF EXISTS test_sqlite_log'),call(None, 'DROP TABLE IF EXISTS test_sqlite_log2'), call(None, 'DROP TABLE IF EXISTS test_sqlite_logtables')])


####################### Integration Test
def own_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(keyfields['value'])**keyfields['exponent']
    cos_result = cos(keyfields['value'])**keyfields['exponent']

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)
    result_processor.process_logs({'test_sqlite_log': {'test': 0}, 'test_sqlite_log2': {'test': 1}})
    result_processor.process_logs({'test_sqlite_log': {'test': 2}, 'test_sqlite_log2': {'test': 3}})

def test_integration():
    experimenter = PyExperimenter(os.path.join('test', 'test_logtables', 'sqlite_logtables.cfg'))
    try:
        experimenter.delete_table()
    except Exception:
        pass
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, 1)
    connection = experimenter.dbconnector.connect()
    cursor = experimenter.dbconnector.cursor(connection)
    cursor.execute(f"SELECT * FROM test_sqlite_log")
    logtable = cursor.fetchall()
    assert logtable == [(1, 0, 1), (2, 2, 1)]
    cursor.execute(f"SELECT * FROM test_sqlite_log2")
    logtable2 = cursor.fetchall()
    assert logtable2 == [(1, 1, 1), (2, 3, 1)]
    
    
    
    
    
    