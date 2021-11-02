import logging

from base_folder.py_experimenter.py_experimenter import PyExperimenter
from base_folder.py_experimenter.result_processor import ResultProcessor

from math import sin, cos


def own_function(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(parameters['value'])
    cos_result = cos(parameters['value'])

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)


logging.basicConfig(level=logging.DEBUG)

# create expermimenter
experimenter = PyExperimenter(config_path='example2_config.cfg')

# fill database table with combination of values defined in the dict
experimenter.fill_table(parameters={'value': ['1', '2', '3', '4', '5'], 'exponent': ['1', '2', '3']})
# add two more parameter combinations to the database
experimenter.fill_table(individual_parameters=[{'value': '6', 'exponent': '1'}, {'value': '6', 'exponent': '2'}])

# execute all experiments
experimenter.execute(own_function)
