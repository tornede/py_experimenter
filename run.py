import random
import time

from base_folder.py_experimenter.py_experimenter import PyExperimenter
from base_folder.py_experimenter.result_processor import ResultProcessor


def own_function(parameters, result_processor):
    print(parameters)
    #print(result_processor)
    pause = random.randrange(1, 10)
    print("start", pause)
    time.sleep(pause)
    #result = [1, 'test', 4]
    rf = result_processor._result_fields

    result = {}
    for r in rf:
        result[r] = pause

    result_processor.process_results(result)
    #return result


experimenter = PyExperimenter()
experimenter.fill_table()
experimenter.execute(own_function)