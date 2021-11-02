import configparser
import logging
import sys


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
        if database_config['provider'] == 'sqlite':
            host = None
            user = None
            password = None
        else:
            host = database_config['host']
            user = database_config['user']
            password = database_config['password']
        database = database_config['database']
        table_name = database_config['table'].replace(' ', '')

    except KeyError as err:
        sys.exit('Missing entries in the configuration file! (%s is missing)' % err)

    return table_name, host, user, database, password


def get_keyfields(config):
    experiment_config = config['PY_EXPERIMENTER']

    keyfields = experiment_config['keyfields'].split(',')
    keyfield_names = get_field_names(keyfields)

    return keyfield_names

def get_keyfield_data(config):
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
            logging.error("Missing value definitions for %s. Add it to the configuration file or provide own parameters by using fill_talbe(own_parameters=...)." % err)
            sys.exit()

    return keyfield_data


def get_field_names(fields):
    """
    Clean field names
    :param fields: List of field names
    :return: Cleaned list of field names
    """
    clean_fields = [field.replace(' ', '') for field in fields]
    return [field.split(':')[0] for field in clean_fields]
