import random
import time

from base_folder.py_experimenter.py_experimenter import PyExperimenter
from base_folder.py_experimenter.result_processor import ResultProcessor


def own_function(parameters, result_processor: ResultProcessor):
    pause = random.randrange(1, 10)
    time.sleep(pause)
    rf = result_processor._result_fields

    result = {}
    for r in rf:
        result[r] = pause

    result_processor.process_results(result)


experimenter = PyExperimenter()
#experimenter.fill_table(own_paramerters=[{'datasetName': '1', 'internal_performance_measure':'1', 'featureObjectiveMeasure':'1', 'seed':1}])
experimenter.fill_table()
experimenter.execute(own_function)