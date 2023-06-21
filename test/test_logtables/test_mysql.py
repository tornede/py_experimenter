import os
from configparser import ConfigParser
from math import cos, sin

from freezegun import freeze_time
from mock import call, patch

from py_experimenter.database_connector import DatabaseConnector
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL._create_database_if_not_existing')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL._test_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.fill_table')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.connect')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.cursor')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.fetchall')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.close_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.execute')
def test_tables_created(execute_mock, close_connection_mock, fetchall_mock, cursor_mock, connect_mock, fill_table_mock, test_connection_mock, create_database_mock):
    execute_mock.return_value = None
    fetchall_mock.return_value = None
    close_connection_mock.return_value = None
    cursor_mock.return_value = None
    connect_mock.return_value = None
    fill_table_mock.return_value = None
    create_database_mock.return_value = None
    test_connection_mock.return_value = None
    experimenter = PyExperimenter(os.path.join('test', 'test_logtables', 'mysql_logtables.cfg'))
    experimenter.fill_table_from_config()
    assert execute_mock.mock_calls[1][1][1] == ('CREATE TABLE test_mysql_logtables (ID INTEGER PRIMARY KEY AUTO_INCREMENT, value int DEFAULT NULL,'
                                                'exponent int DEFAULT NULL,creation_date DATETIME DEFAULT NULL,status VARCHAR(255) DEFAULT NULL,'
                                                'start_date DATETIME DEFAULT NULL,name LONGTEXT DEFAULT NULL,machine VARCHAR(255) DEFAULT NULL,'
                                                'sin VARCHAR(255) DEFAULT NULL,cos VARCHAR(255) DEFAULT NULL,end_date DATETIME DEFAULT NULL,'
                                                'error LONGTEXT DEFAULT NULL);')
    assert execute_mock.mock_calls[2][1][1] == ('CREATE TABLE test_mysql_logtables__test_mysql_log (ID INTEGER PRIMARY KEY AUTO_INCREMENT,'
                                                ' experiment_id INTEGER, timestamp DATETIME, test int DEFAULT NULL, FOREIGN KEY (experiment_id)'
                                                ' REFERENCES test_mysql_logtables(ID) ON DELETE CASCADE);')


@freeze_time("2012-01-14 03:21:34")
@patch('py_experimenter.result_processor.DatabaseConnectorMYSQL')
def test_logtable_insertion(database_connector_mock):
    config = ConfigParser()
    config.read(os.path.join('test', 'test_logtables', 'mysql_logtables.cfg'))
    result_processor = ResultProcessor(config, None, None, None, None, None, 0)
    result_processor._table_name = 'table_name'
    table_0_logs = {'test0': 'test', 'test1': 'test'}
    table_1_logs = {'test0': 'test'}
    result_processor.process_logs({'test_table_0': table_0_logs,
                                   'test_table_1': table_1_logs})
    result_processor._dbconnector.prepare_write_query.assert_any_call(
        'table_name__test_table_1', table_1_logs.keys())
    result_processor._dbconnector.prepare_write_query.assert_any_call(
        'table_name__test_table_0', table_0_logs.keys())
    result_processor._dbconnector.execute_queries.assert_called()


@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL._create_database_if_not_existing')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL._test_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.connect')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.cursor')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.commit')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.fetchall')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.close_connection')
@patch('py_experimenter.experimenter.DatabaseConnectorMYSQL.execute')
def test_delete_logtable(execution_mock, close_connection_mock, commit_mocck, fetchall_mock, cursor_mock, connect_mock, test_connection_mock, create_database_mock):
    fetchall_mock.return_value = cursor_mock.return_value = connect_mock.return_value = commit_mocck.return_value = None
    close_connection_mock.return_value = test_connection_mock.return_value = create_database_mock.return_value = execution_mock.return_value = None
    experimenter = PyExperimenter(os.path.join('test', 'test_logtables', 'mysql_logtables.cfg'), use_codecarbon=False)
    experimenter.delete_table()
    execution_mock.assert_has_calls([call(None, 'DROP TABLE IF EXISTS test_mysql_logtables__test_mysql_log'),
                                     call(None, 'DROP TABLE IF EXISTS test_mysql_logtables__test_mysql_log2'),
                                     call(None, 'DROP TABLE IF EXISTS test_mysql_logtables')])


# Integration Test
def own_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(keyfields['value'])**keyfields['exponent']
    cos_result = cos(keyfields['value'])**keyfields['exponent']

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)
    result_processor.process_logs({'test_mysql_log': {'test': 0}, 'test_mysql_log2': {'test': 1}})
    result_processor.process_logs({'test_mysql_log': {'test': 2}, 'test_mysql_log2': {'test': 3}})


def test_integration():
    experimenter = PyExperimenter(os.path.join('test', 'test_logtables', 'mysql_logtables.cfg'))
    try:
        experimenter.delete_table()
    except Exception:
        pass
    experimenter.fill_table_from_config()
    experimenter.execute(own_function, 1)
    connection = experimenter.dbconnector.connect()
    cursor = experimenter.dbconnector.cursor(connection)
    cursor.execute(f"SELECT * FROM test_mysql_logtables__test_mysql_log")
    logtable = cursor.fetchall()
    timesteps = [x[2] for x in logtable]
    non_timesteps = [x[:2] + x[3:] for x in logtable]
    assert non_timesteps == [(1, 1, 0), (2, 1, 2)]
    cursor.execute(f"SELECT * FROM test_mysql_logtables__test_mysql_log2")
    logtable2 = cursor.fetchall()
    timesteps2 = [x[2] for x in logtable2]
    logtable2 = [x[:2] + x[3:] for x in logtable2]
    assert logtable2 == [(1, 1, 1), (2, 1, 3)]
    assert timesteps == timesteps2
