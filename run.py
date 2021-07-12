import logging
import random
import time

from base_folder.py_experimenter.py_experimenter import PyExperimenter
from base_folder.py_experimenter.result_processor import ResultProcessor


def own_function(parameters, result_processor: ResultProcessor):
    pause = random.randrange(1, 10)

    if pause == 9:
        raise ValueError("Example error")

    time.sleep(pause)

    result = {'final_pipeline': parameters['datasetName']}

    result_processor.process_results(result)

    result = {'internal_performance': pause, 'performance_asymmetric_loss': 0}

    result_processor.process_results(result)


logging.basicConfig(level=logging.DEBUG)
experimenter = PyExperimenter()
#experimenter.fill_table(own_paramerters=[
#    {'datasetName': '1', 'internal_performance_measure': '1', 'featureObjectiveMeasure': '1', 'seed': 1}])
experimenter.fill_table()
experimenter.execute(own_function)
#experimenter.execute(own_function, max_experiments=1, random_order=False)