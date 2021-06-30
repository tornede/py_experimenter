import random
import time

from py_experimenter import PyExperimenter

def own_function(parameter):
    pause = random.randrange(1, 10)
    print("start", pause)
    time.sleep(pause)
    result = [1, 'test', 4]
    return result


experimenter = PyExperimenter()
experimenter.fill_table()
experimenter.execute(own_function)