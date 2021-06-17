import configparser
import re
import sys

import numpy as np
import pandas as pd

from mysql.connector import connect, ProgrammingError, DatabaseError


def load_config_and_table_name(path):
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

    return config, config['DATABASE']['table']


def extract_db_credentials_and_table_name_from_config(config):
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

    except KeyError as err:
        sys.exit('Missing entries in the configuration file! (%s is missing)' % err)

    except ProgrammingError:
        sys.exit('Connection to the database %s could not be established. Please check your credentials.' % database)

    #create_table_if_not_exists(connection, table_name, config['EXPERIMENT'])

    return table_name, host, user, database, password


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

def get_keyfields(config):
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

    return keyfield_names, keyfield_data

def get_field_names(fields):
    clean_fields = [field.replace(' ', '') for field in fields]
    return [field.split(':')[0] for field in clean_fields]