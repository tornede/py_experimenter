import logging
from math import cos, sin
import os

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


def own_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    # run the experiment with the given value for the sin and cos function
    sin_result = sin(keyfields['value'])**keyfields['exponent']
    cos_result = cos(keyfields['value'])**keyfields['exponent']

    # write result in dict with the resultfield as key
    result = {'sin': sin_result, 'cos': cos_result}

    # send result to to the database
    result_processor.process_results(result)


logging.basicConfig(level=logging.INFO)

# Create sqlite experimenter.
experimenter = PyExperimenter(config_file=os.path.join('examples', 'example_fill_from_config.cfg'))
# To use a mysql database, modify the examples/example_fill_complex.cfg file and change the provider to mysql.
# In addition you need to provide the credentials file config/database_credentials.cfg and confirm that you
# have the permission to create a database/a database exists as defined in the config file.
# For more information refer to the README.md file.


# Fill database table with combination of values defined in the configuration.
experimenter.fill_table_from_config()

# Execute all experiments.
experimenter.execute(own_function, -1)
