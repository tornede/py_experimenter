import logging
import os
import random
import time

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


def own_function(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    pause = random.randrange(1, int(custom_fields['pause.max']))
    if pause >= int(custom_fields['pause.threshold']):
        raise ValueError("Example error")
    time.sleep(pause)

    result = {'final_pipeline': keyfields['datasetName']}
    result_processor.process_results(result)

    result = {'internal_performance': pause, 'performance_asymmetric_loss': 0}
    result_processor.process_results(result)


logging.basicConfig(level=logging.INFO)

# Create sqlite experimenter.
experimenter = PyExperimenter(config_file=os.path.join('examples', 'example_reset_experiments.cfg'),
                              name='Experimenter before reset')
# To use a mysql database, modify the examples/example_fill_complex.cfg file and change the provider to mysql.
# In addition you need to provide the credentials file config/database_credentials.cfg and confirm that you
# have the permission to create a database/a database exists as defined in the config file.
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

# Reset the experiments that have the status error.
experimenter.reset_experiments(status='error')

# Run the reset experiments again.
experimenter = PyExperimenter(config_file=os.path.join('examples', 'example_reset_experiments.cfg'),
                              name='Experimenter after reset')
experimenter.execute(own_function, max_experiments=-1)
