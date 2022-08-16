import logging
from math import cos, sin
import os

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


def own_function(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(parameters['value'])**parameters['exponent']
    cos_result = cos(parameters['value'])**parameters['exponent']

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)


logging.basicConfig(level=logging.INFO)

# Create sqlite experimenter.
experimenter = PyExperimenter(config_path=os.path.join('examples','example_fill_from_combination_complex.cfg'))
# To use a mysql database, modify the examples/example_fill_complex.cfg file and change the provider to mysql.
# In addition you need to provide the credentials file config/database_credentials.cfg and make sure that the database exists.
# For more information refer to the README.md file.


# Fill database table with combination of values defined the parameter argument, and fixed_parameter_combinations argument.
experimenter.fill_table_from_combination(parameters={'value': ['1', '2', '3', '4', '5'], 'exponent': ['1', '2', '3']},
                                         fixed_parameter_combinations=[
                                             {'test_individual_parameter_1': '1', 'test_individual_parameter_2': '2'},
                                             {'test_individual_parameter_1': '3', 'test_individual_parameter_2': '4'}
]
)

# Execute all experiments.
experimenter.execute(own_function, -1)
