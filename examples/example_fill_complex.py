import logging
import random
import time

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


def own_function(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    pause = random.randrange(1, int(custom_config['pause.max']))
    if pause >= int(custom_config['pause.threshold']):
        raise ValueError("Example error")
    time.sleep(pause)

    result = {'final_pipeline': parameters['datasetName']}
    result_processor.process_results(result)

    result = {'internal_performance': pause, 'performance_asymmetric_loss': 0}
    result_processor.process_results(result)


logging.basicConfig(level=logging.INFO)

# Create sqlite experimenter.
experimenter = PyExperimenter(config_path='examples/example_fill_complex.cfg')
# To use a mysql database, modify the examples/example_fill_complex.cfg file and change the provider to mysql.
# In addition you need to provide the credentials file config/database_credentials.cfg and make sure that the database exists.
# For more information refer to the README.md file.

# Fill database table with combination of values defined in the dict.
experimenter.fill_table_from_combination(
    parameters={'datasetName': ['1', '2'],
                'internal_performance_measure': ['1'],
                'featureObjectiveMeasure': ['1'],
                'seed': [0, 1, 2]})

# Execute the first experiment from the database.
experimenter.execute(own_function, max_experiments=1, random_order=False)

# Execute random experiment from the database.
experimenter.execute(own_function, max_experiments=1, random_order=True)

experimenter.execute(own_function, -1)
