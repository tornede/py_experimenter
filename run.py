import random
import time

from base_folder.py_experimenter.py_experimenter import PyExperimenter


def own_function(parameters: dict, result_processor):
    print(parameters)
    print(result_processor)
    pause = random.randrange(1, 10)
    print("start", pause)
    time.sleep(pause)
    result = [1, 'test', 4]
    return result


experimenter = PyExperimenter()
experimenter.fill_table()
experimenter.execute(own_function)