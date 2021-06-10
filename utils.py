import configparser
import re
import sys

import numpy as np
import pandas as pd

from mysql.connector import connect, ProgrammingError, DatabaseError


def load_config(path='config/configuration.cfg'):
    """
    Load and return configuration file
    :param path: path to the config file
    :return: configuration file
    """
    config = configparser.ConfigParser()

    try:
        config.read_file(open(path))
    except FileNotFoundError:
        sys.exit('Configuration file missing! Please add file: %s' % path)

    return config


def get_mysql_connection_and_table_name(config):
    """
    Initialize connection to database based on configuration file. If the tables does not exist, a new one will be
    created automatically
    :param config: Configuration file with database and experiment information
    :return: mysql_connector and table name from the config file
    """
    try:
        database_config = config['DATABASE']
        host = database_config['host']
        user = database_config['user']
        database = database_config['database']
        password = database_config['password']
        table_name = database_config['table']

        connection = connect(
            host=host,
            user=user,
            database=database,
            password=password
        )

    except KeyError as err:
        sys.exit('Missing entries in the configuration file! (%s is missing)' % err)

    except ProgrammingError:
        sys.exit('Connection to the database %s could not be established. Please check your credentials.' % database)

    except DatabaseError as err:
        sys.exit(err.__context__)

    create_table_if_not_exists(connection, table_name, config['EXPERIMENT'])

    return connection, table_name


def create_table_if_not_exists(connection, table_name, experiment_config) -> None:
    """
    Check if tables does exist. If not, a new table will be created.
    :param mysql_connection: mysql_connector to the database
    :param table_name: name of the table from the config
    :param experiment_config: experiment section of the config file
    """

    cursor = connection.cursor(buffered=True)
    cursor.execute('SHOW TABLES')
    for table in cursor:
        if table[0] == table_name:
            return

    query = create_new_table_query(table_name, experiment_config)

    try:
        cursor.execute(query)
    except ProgrammingError as err:
        unkown_datatype = str(err.__context__).split("'")[1].split(" ")[0]
        print("Error: '%s' is unknown or not allowed" % unkown_datatype)


def create_new_table_query(table_name: str, experiment_config) -> str:
    """
    Create new table based on config file
    :param table_name: name of the new table
    :param experiment_config: experiment section of the config file
    :return: query string for new table
    """
    query = 'CREATE TABLE ' + table_name + ' ('
    fields = experiment_config['keyfields'].split(',') + experiment_config['resultfields'].split(',')
    clean_fields = [field.replace(' ', '') for field in fields]
    typed_fields = [tuple(field.split(':')) if len(field.split(':')) == 2 else (field, 'VARCHAR(255)') for
                    field in clean_fields]

    typed_fields.extend([('status', 'VARCHAR(255)'), ('creation_date', 'VARCHAR(255)'), ('start_data', 'VARCHAR(255)'),
                         ('end_data', 'VARCHAR(255)')])

    for field, datatype in typed_fields:
        query += '%s %s DEFAULT NULL, ' % (field, datatype)

    # remove last ', '
    query = query[:-2] + ')'

    return query


def fill_table(connection, table_name, config) -> None:
    """
    Fill table with all combination of keyfield values, if combiation does not exist.
    :param connection: connection to database
    :param table_name: name of the table
    :param config: config file
    """
    experiment_config = config['EXPERIMENT']

    keyfields = experiment_config['keyfields'].split(',')
    keyfield_names = get_field_names(keyfields)

    keyfield_data = []
    for data_name in keyfield_names:
        try:
            data = experiment_config[data_name].split(',')
            clean_data = [d.replace(' ', '') for d in data]
            keyfield_data.append(clean_data)
        except KeyError as err:
            print('Missing value definitions for %s' % err)

    # ref: https://www.kite.com/python/answers/how-to-get-all-element-combinations-of-two-numpy-arrays-in-python
    combinations = np.array(np.meshgrid(*keyfield_data)).T.reshape(-1, len(keyfield_data))

    cursor = connection.cursor()
    columns_names = np.array2string(np.array(keyfield_names), separator=',') \
        .replace('[', '') \
        .replace(']', '') \
        .replace("'", "")
    cursor.execute("SELECT %s FROM %s" % (columns_names, table_name))
    existing_rows = list(map(np.array2string, np.array(cursor.fetchall())))

    for combination in combinations:
        if str(combination) in existing_rows:
            continue
        values = np.array2string(combination, separator=',').replace('[', '').replace(']', '')
        query = """INSERT INTO %s (%s) VALUES (%s)""" % (table_name, columns_names, values)
        cursor.execute(query)
        connection.commit()

def get_parameters_from_table(connection, table_name, config):
    experiment_config = config['EXPERIMENT']

    resultfields = experiment_config['resultfields'].split(',')
    resultfield_names = get_field_names(resultfields)
    resultfield_conditions = " IS NULL AND ".join(resultfield_names) + " IS NULL"

    keyfields = experiment_config['keyfields'].split(',')
    keyfield_names = get_field_names(keyfields)

    cursor = connection.cursor()
    query = "SELECT %s FROM %s WHERE %s" % (", ".join(keyfield_names), table_name, resultfield_conditions)

    cursor.execute(query)
    parameters = pd.DataFrame(cursor.fetchall())
    parameters.columns = [i[0] for i in cursor.description]
    cursor.close()

    named_parameters = []
    for parameter in parameters.iterrows():
        named_parameters.append(re.sub(' +', '=', parameter[1].to_string()).replace('\n', ','))

    return named_parameters

def get_field_names(fields):
    clean_fields = [field.replace(' ', '') for field in fields]
    return [field.split(':')[0] for field in clean_fields]