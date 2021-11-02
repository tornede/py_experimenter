import logging

from py_experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor

from math import sin, cos


def own_function(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(parameters['value'])**parameters['exponent']
    cos_result = cos(parameters['value'])**parameters['exponent']

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)


logging.basicConfig(level=logging.DEBUG)

# create expermimenter
experimenter = PyExperimenter(config_path='example1_config.cfg')

# fill database table with combination of values defined in the configuration
experimenter.fill_table()

# execute all experiments
experimenter.execute(own_function)
