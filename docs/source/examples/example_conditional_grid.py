################### This is a copy the example_general_usage.ipynb notebook that works with windows and mac #################
# Note that while this file contains all code from the notebook, the explanations are not given

###### First Write Configuration File ######
from multiprocessing import freeze_support # Needed later for windows
from random import randint
from time import sleep
from py_experimenter.result_processor import ResultProcessor
from py_experimenter.experimenter import PyExperimenter
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_validate
from sklearn.datasets import load_iris
import numpy as np
import random
import os

content = """
[PY_EXPERIMENTER]
provider = sqlite 
database = py_experimenter
table = svm_experiment_example

keyfields = dataset, cross_validation_splits:int, seed:int, kernel, gamma:DECIMAL, degree:int, coef0:DECIMAL

resultfields = train_f1:DECIMAL, train_accuracy:DECIMAL, test_f1:DECIMAL, test_accuracy:DECIMAL
resultfields.timestamps = false

[CUSTOM] 
path = sample_data
"""
experiment_configuration_file_path = os.path.join('config', 'example_conditional_grid.cfg')
with open(experiment_configuration_file_path, "w") as f:
    f.write(content)


###### Define the Execution Function ######

def run_svm(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    sleep(randint(0, 5))
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

    svc = SVC()

    model = make_pipeline(StandardScaler(), svc)

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
        'test_accuracy': np.mean(scores['test_accuracy'])})


###### Prepare for Multiprocessing by calling if __name__ == '__main__' and freeze_support() ######

if __name__ == '__main__':
    freeze_support()
    
    ###### Create Experimenter ######
    from py_experimenter.experimenter import PyExperimenter

    experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration_file_path, name="SVM_experimenter_01")
    
    ###### Run Experimenter ######
    # Create parameter configurations for each kernel
    combinations = [{'kernel': 'rbf', 'gamma': gamma, 'degree':'nan', 'coef0':'nan'} for gamma in ['0.1','0.3']]
    combinations += [{'kernel': 'poly', 'gamma': gamma, 'degree': degree, 'coef0': coef0} for gamma in ['0.1','0.3'] for degree in ['3','4'] for coef0 in ['0.0', '0.1']]
    combinations += [{'kernel': 'linear','gamma': 'nan', 'degree':'nan', 'coef0':'nan'}]

    # Fill experimenter
    experimenter.fill_table_from_combination(parameters={'seed': ['1', '2', '3', '4', '5'], 
    'dataset': ['iris'],
    'cross_validation_splits': ['5'] },
    fixed_parameter_combinations=combinations)

    # showing database table
    experimenter.get_table()
    
    ###### Run Experimenter ######
    experimenter.execute(run_svm, max_experiments=-1, random_order=True)

    # showing database table
    table = experimenter.get_table()
    print(table)