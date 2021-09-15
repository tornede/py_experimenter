import logging
import random
import time

from base_folder.py_experimenter.py_experimenter import PyExperimenter
from base_folder.py_experimenter.result_processor import ResultProcessor


def own_function(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    pause = random.randrange(1, int(custom_config['pause.max']))

    if pause >= int(custom_config['pause.threshold']):
        raise ValueError("Example error")

    time.sleep(pause)

    result = {'final_pipeline': parameters['datasetName']}

    result_processor.process_results(result)

    result = {'internal_performance': pause, 'performance_asymmetric_loss': 0}

    result_processor.process_results(result)


logging.basicConfig(level=logging.DEBUG)
experimenter = PyExperimenter(config_path='config/example_config.cfg')

experimenter.fill_table(individual_parameters=[
    {'datasetName': '-1', 'internal_performance_measure': '0', 'featureObjectiveMeasure': '0', 'seed': 0}])

#experimenter.fill_table(
#    parameters={'datasetName': ['1', '2'], 'internal_performance_measure': ['1'], 'featureObjectiveMeasure': ['1'], 'seed': [0,1,2]})

#experimenter.fill_table()

experimenter.execute(own_function)
# experimenter.execute(own_function, max_experiments=1, random_order=False)
