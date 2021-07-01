import configparser
import sys

from mysql.connector import ProgrammingError


def load_config(path):
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

    return table_name, host, user, database, password


def get_keyfields(config):
    """
    Extrect keyfieds from configuration file, clean them by removing all blank spaces and return a list of names and a list of keyfield data
    :param config: Configuration file
    :return: List of cleaned keyfield names and a list of keyfield data
    """

    experiment_config = config['PY_EXPERIMENTER']

    keyfields = experiment_config['keyfields'].split(',')
    keyfield_names = get_field_names(keyfields)

    keyfield_data = []
    for data_name in keyfield_names:
        try:
            data = experiment_config[data_name].split(',')
            clean_data = [d.replace(' ', '') for d in data]
            keyfield_data.append(clean_data)
        except KeyError as err:
            sys.exit('Missing value definitions for %s' % err)

    return keyfield_names, keyfield_data


def get_field_names(fields):
    """
    Clean field names
    :param fields: List of field names
    :return: Cleaned list of field names
    """
    clean_fields = [field.replace(' ', '') for field in fields]
    return [field.split(':')[0] for field in clean_fields]
