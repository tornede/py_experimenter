import logging
import os
import random

import numpy as np
import pandas
from sklearn.datasets import load_iris
from sklearn.model_selection import cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor

logging.basicConfig(level=logging.INFO)

def run_svm(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    seed = parameters['seed']
    random.seed(seed)
    np.random.seed(seed)

    data = load_iris()

    X = data.data
    y = data.target

    # Create Support Vector Machine with parameters dependent on the kernel
    kernel = parameters['kernel']
    if kernel == 'linear':
        svc = SVC(kernel=parameters['kernel'])
    elif kernel == 'poly':
        svc = SVC(kernel=parameters['kernel'], gamma=parameters['gamma'], coef0=parameters['coef0'], degree=parameters['degree'])
    elif kernel == 'rbf':
        svc = SVC(kernel=parameters['kernel'], gamma=parameters['gamma'])


    model = make_pipeline(StandardScaler(), svc)  

    if parameters['dataset'] != 'iris':
        raise ValueError("Example error")

    scores = cross_validate(model, X, y, cv=parameters['cross_validation_splits'],
        scoring=('accuracy', 'f1_micro'),
        return_train_score=True)
    
    resultfields = {'train_f1': np.mean(scores['train_f1_micro']),
                'train_accuracy': np.mean(scores['train_accuracy'])}
    result_processor.process_results(resultfields)

    resultfields = {'test_f1': np.mean(scores['test_f1_micro']),
                'test_accuracy': np.mean(scores['test_accuracy'])}
    result_processor.process_results(resultfields)

experimenter = PyExperimenter(config_file=os.path.join('examples', 'example_fill_from_combination_svm.cfg'))

# Create parameter configurations for each kernel
combinations = [{'kernel': 'rbf', 'gamma': gamma, 'degree':'nan', 'coef0':'nan'} for gamma in ['0.1','0.3']]
combinations += [{'kernel': 'poly', 'gamma': gamma, 'degree': degree, 'coef0': coef0} for gamma in ['0.1','0.3'] for degree in ['3','4'] for coef0 in ['0.0', '0.1']]
combinations += [{'kernel': 'linear','gamma': 'nan', 'degree':'nan', 'coef0':'nan'}]

print(combinations)

# Fill table with params for linear kernel.
experimenter.fill_table_from_combination(parameters={'seed': ['1', '2', '3', '4', '5'], 
'dataset': ['iris'],
'cross_validation_splits': ['5'] },
fixed_parameter_combinations=combinations)

experimenter.execute(run_svm, max_experiments=-1, random_order=True)

table= experimenter.get_table()

table.to_csv("table.csv")
