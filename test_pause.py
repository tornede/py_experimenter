import datetime
import os
import random

import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from py_experimenter.experimenter import ExperimentStatus, PyExperimenter
from py_experimenter.result_processor import ResultProcessor

content = """
[PY_EXPERIMENTER]
provider = sqlite
database = py_experimenter
table = example_general_usage

keyfields = dataset, cross_validation_splits:int, seed:int, kernel
dataset = iris
cross_validation_splits = 5
seed = 2:6:2
kernel = linear, poly, rbf, sigmoid

resultfields = pipeline:LONGTEXT, train_f1:DECIMAL, train_accuracy:DECIMAL, test_f1:DECIMAL, test_accuracy:DECIMAL, paused_at_seconds:DOUBLE, resumed_at_seconds:DOUBLE
resultfields.timestamps = false

[CUSTOM]
path = sample_data

[codecarbon]
offline_mode = False
measure_power_secs = 25
tracking_mode = process
log_level = error
save_to_file = True
output_dir = output/CodeCarbon
"""
# Create config directory if it does not exist
if not os.path.exists('config'):
    os.mkdir('config')

# Create config file
experiment_configuration_file_path = os.path.join('config', 'example_general_usage.cfg')
with open(experiment_configuration_file_path, "w") as f:
    f.write(content)


def pause_after_5_seconds(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    import time
    time.sleep(5)
    result_processor.process_results({
        'paused_at_seconds': datetime.datetime.now().timestamp()
    })
    return ExperimentStatus.PAUSED.value


experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration_file_path, name='example_notebook')

experimenter.fill_table_from_config()

experimenter.fill_table_with_rows(rows=[
    {'dataset': 'error_dataset', 'cross_validation_splits': 3, 'seed': 42, 'kernel': 'linear'}])

# showing database table
experimenter.get_table()

experimenter.execute(pause_after_5_seconds, max_experiments=1)


def resume_after_5_seconds(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    result_processor.process_results({
        'resumed_at_seconds': datetime.datetime.now().timestamp()
    })
    seed = parameters['seed']
    random.seed(seed)
    np.random.seed(seed)

    data = load_iris()
    # In case you want to load a file from a path
    # path = os.path.join(custom_config['path'], parameters['dataset'])
    # data = pd.read_csv(path)

    X = data.data
    y = data.target

    model = make_pipeline(StandardScaler(), SVC(kernel=parameters['kernel'], gamma='auto'))
    result_processor.process_results({
        'pipeline': str(model)
    })

    if parameters['dataset'] != 'iris':
        raise ValueError("Example error")

    scores = cross_validate(model, X, y,
                            cv=parameters['cross_validation_splits'],
                            scoring=('accuracy', 'f1_micro'),
                            return_train_score=True
                            )

    result_processor.process_results({
        'train_f1': np.mean(scores['train_f1_micro']),
        'train_accuracy': np.mean(scores['train_accuracy'])
    })

    result_processor.process_results({
        'test_f1': np.mean(scores['test_f1_micro']),
        'test_accuracy': np.mean(scores['test_accuracy'])
    })


experimenter.unpause_experiment(1, resume_after_5_seconds)
