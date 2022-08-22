import configparser
import logging

import numpy as np

from py_experimenter.py_experimenter_exceptions import NoConfigFileError, ParameterCombinationError


def load_config(path):
    """
    Load and return configuration file
    :param path: path to the config file
    :return: configuration file
    """
    config = configparser.ConfigParser()
    try:
        with open(path) as f:
            config.read_file(f)
    except FileNotFoundError:
        raise NoConfigFileError(f'Configuration file missing! Please add file: {path}')

    return config


def extract_db_credentials_and_table_name_from_config(config):
    """
    Initialize connection to database based on configuration file. If the tables does not exist, a new one will be
    created automatically
    :param config: Configuration file with database and experiment information
    :return: mysql_connector and table name from the config file
    """
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

    return table_name, host, user, database, password


def get_keyfield_data(config):
    keyfield_names = get_keyfields(config)

    experiment_config = config['PY_EXPERIMENTER']

    keyfield_data = {}
    for keyfield_name in keyfield_names:
        try:
            data = experiment_config[keyfield_name].split(',')
            clean_data = [d.replace(' ', '') for d in data]
            keyfield_data[keyfield_name] = clean_data
        except KeyError as err:
            logging.info(
                "No value definitions for %s. Add it to the configuration file or provide at fill_talbe() call" % err)

    return keyfield_data


def get_keyfields(config):
    keyfield_names = get_field_names(config['PY_EXPERIMENTER']['keyfields'])
    return keyfield_names


def get_resultfields(config):
    result_fields = get_field_names(config['PY_EXPERIMENTER']['resultfields'])
    return result_fields


def get_field_names(fields):
    """
    Clean field names
    :param fields: List of field names
    :return: Cleaned list of field names
    """
    if not fields:
        return []
    fields = fields.rstrip(',')
    fields = fields.split(',')
    clean_fields = [field.replace(' ', '') for field in fields]
    return [field.split(':')[0] for field in clean_fields]


def combine_fill_table_parameters(keyfield_names, parameters, fixed_parameter_combinations):
    def create_combination_from_parameters():
        keyfield_data = list()
        used_keys = list()

        for keyfield_name in keyfield_names:
            if keyfield_name in parameters.keys():
                keyfield_data.append(parameters[keyfield_name])
                used_keys.append(keyfield_name)

        if keyfield_data:
            combinations = np.array(np.meshgrid(*keyfield_data)).T.reshape(-1, len(keyfield_data))
            combinations = [dict(zip(used_keys, combination)) for combination in combinations]
        else:
            combinations = []
        return combinations

    def add_individual_parameters_to_combinations():
        new_combinations = list()
        if combinations:
            for comination in combinations:
                for fixed_parameter_combination in fixed_parameter_combinations:
                    try:
                        new_combination = dict(**comination, **fixed_parameter_combination)
                    except TypeError:
                        raise ParameterCombinationError('There is at least one key that is used more than once!')
                    new_combinations.append(new_combination)
        else:
            new_combinations = fixed_parameter_combinations

        return new_combinations

    combinations = create_combination_from_parameters()

    if fixed_parameter_combinations:
        combinations = add_individual_parameters_to_combinations()

    if not combinations:
        raise ParameterCombinationError('No parameter combination found!')

    for combination in combinations:
        if not len(combination.keys()) == len(set(combination.keys())):
            raise ParameterCombinationError(f'There is at least one key that is used more than once in {str(combination.keys())}!')

        if set(combination.keys()) != set(keyfield_names):
            raise ParameterCombinationError(
                'The number of config_parameters + individual_parameters + parameters does not match the amount of keyfields!')

    return combinations
