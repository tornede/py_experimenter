import logging
from configparser import ConfigParser
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

from py_experimenter.exceptions import ConfigError, NoConfigFileError, ParameterCombinationError


def load_config(path):
    """
    Load and return configuration file.
    :param path: path to the config file
    :return: configuration file
    """
    config = ConfigParser()
    try:
        with open(path) as f:
            config.read_file(f)
    except FileNotFoundError:
        raise NoConfigFileError(f'Configuration file missing! Please add file: {path}')

    return config


def get_keyfield_data(config):
    keyfields = get_keyfields(config)

    experiment_config = config['PY_EXPERIMENTER']

    keyfield_data = {}
    for keyfield_name, keyfield_type in keyfields:
        keyfield_values = experiment_config[keyfield_name].replace(' ', '').split(',')

        if keyfield_type.startswith('int'):
            final_data = _generate_int_data(keyfield_values)

        else:
            final_data = keyfield_values
        try:
            keyfield_data[keyfield_name] = final_data
        except KeyError as err:
            logging.info(
                "No value definitions for %s. Add it to the configuration file or provide at fill_table() call" % err)

    return keyfield_data


def extract_db_credentials_and_table_name_from_config(config):
    """
    Initialize connection to database based on configuration file. If the tables does not exist, a new one will be
    created automatically.
    :param config: Configuration file with database and experiment information
    :return: mysql_connector and table name from the config file
    """
    database_config = config['PY_EXPERIMENTER']
    if database_config['provider'] == 'sqlite':
        host = None
        user = None
        password = None
    else:
        host = database_config['host']
        user = database_config['user']
        password = database_config['password']
    database = database_config['PY_EXPERIMENTER']
    table_name = database_config['table'].replace(' ', '')

    return table_name, host, user, database, password


def get_keyfield_names(config: ConfigParser) -> List[str]:
    keyfield_names = get_keyfields(config)
    return [name for name, _ in keyfield_names]


def get_keyfields(config: ConfigParser) -> List[Tuple[str, str]]:
    keyfield_names = extract_columns(config['PY_EXPERIMENTER']['keyfields'])
    return keyfield_names


def get_result_field_names(config: ConfigParser) -> List[str]:
    result_fields = get_resultfields(config)
    return [name for name, _ in result_fields]


def get_resultfields(config: ConfigParser) -> List[Tuple[str, str]]:
    result_fields = extract_columns(config['PY_EXPERIMENTER']['resultfields'])
    return result_fields


def extract_columns(fields: str) -> List[Tuple[str, str]]:
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
    typed_fields = [tuple(field.split(':')) if len(field.split(':')) == 2 else (field, 'VARCHAR(255)') for
                    field in clean_fields]
    return typed_fields


def timestamps_for_result_fields(config: ConfigParser) -> bool:
    if config.has_option('PY_EXPERIMENTER', 'resultfields.timestamps'):
        timestamp_on_result_fields = config.getboolean('PY_EXPERIMENTER', 'resultfields.timestamps')
    else:
        timestamp_on_result_fields = False
    return timestamp_on_result_fields


def add_timestep_result_columns(result_field_configuration):
    result_fields_with_timestamp = list()
    for result_field in result_field_configuration:
        result_fields_with_timestamp.append(result_field)
        result_fields_with_timestamp.append((f'{result_field[0]}_timestamp', 'VARCHAR(255)'))
    return result_fields_with_timestamp


def extract_logtables(config: ConfigParser, experiment_table_name: str) -> Optional[Dict[str, List[str]]]:
    logtable_configs = dict()
    if config.has_option('PY_EXPERIMENTER', 'logtables'):
        logtable_definitions = [logtable_name.strip().split(':') for logtable_name in config['PY_EXPERIMENTER']['logtables'].split(',')]
    else:
        logtable_definitions = list()

    for logtable_definer, column_definer in logtable_definitions:
        logtable_name = f'{experiment_table_name}__{logtable_definer}'
        if config.has_option('PY_EXPERIMENTER', column_definer):
            logtable_configs[logtable_name] = extract_columns(config['PY_EXPERIMENTER'][column_definer])
        else:
            logtable_configs[logtable_name] = [(logtable_definer, column_definer)]
    return logtable_configs


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
            for combination in combinations:
                for fixed_parameter_combination in fixed_parameter_combinations:
                    try:
                        new_combination = dict(**combination, **fixed_parameter_combination)
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
        if len(combination.keys()) != len(set(combination.keys())):
            raise ParameterCombinationError(f'There is at least one key that is used more than once in {str(combination.keys())}!')

        if set(combination.keys()) != set(keyfield_names):
            raise ParameterCombinationError(
                'The number of config_parameters + individual_parameters + parameters does not match the amount of keyfields!')

    return combinations


def _generate_int_data(keyfield_values):
    final_data = []
    for data_definition in keyfield_values:
        if ':' in data_definition:

            if data_definition.startswith(':') or data_definition.endswith(':') or '::' in data_definition:
                raise ConfigError(f'{data_definition} is not a valid integer range')

            integer_range = data_definition.split(':')

            if len(integer_range) not in (2, 3):
                raise ConfigError(f'{data_definition} is not a valid integer range')

            try:
                start = int(integer_range[0])
                stop = int(integer_range[1])
            except ValueError:
                raise ConfigError(f'{data_definition} is not a valid integer range')

            if len(integer_range) == 3:
                try:
                    step = int(integer_range[2])
                except ValueError:
                    raise ConfigError(f'{data_definition} is not a valid integer range')

            else:
                step = 1

            if start >= stop:
                raise ConfigError(f'end of range {stop} is smaller than, or equal to start of range {start}')

            final_data += list(range(start, stop + 1, step))
        else:
            final_data.append(int(data_definition))

    final_data = sorted(list(set(final_data)))
    return final_data


def get_timestamp_representation() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
