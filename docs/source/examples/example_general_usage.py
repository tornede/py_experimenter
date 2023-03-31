################### This is a copy the example_general_usage.ipynb notebook that works with windows and mac #################
# Note that while this file contains all code from the notebook, the explanations are not given

###### First Write Configuration File ######

from multiprocessing import freeze_support
from py_experimenter.experimenter import PyExperimenter
from sklearn.model_selection import cross_validate
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.datasets import load_iris
from py_experimenter.result_processor import ResultProcessor
import numpy as np
import random
import os

content = """
[PY_EXPERIMENTER]
provider = sqlite 
database = automl_conf_2023
table = best_paper_table 

keyfields = dataset, cross_validation_splits:int, seed:int, kernel
dataset = iris
cross_validation_splits = 5
seed = 2:6:2 
kernel = linear, poly, rbf, sigmoid

resultfields = pipeline:LONGTEXT, train_f1:DECIMAL, train_accuracy:DECIMAL, test_f1:DECIMAL, test_accuracy:DECIMAL
resultfields.timestamps = false

[CUSTOM] 
path = sample_data
"""
experiment_configuration_file_path = os.path.join('config', 'example_general_usage.cfg')
with open(experiment_configuration_file_path, "w") as f:
    f.write(content)


###### Define the Execution Function ######

def run_ml(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
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


###### Prepare for Multiprocessing by calling if __name__ == '__main__' and freeze_support() ######

if __name__ == '__main__':
    freeze_support()

    ###### Create PyExperimenter Object ######

    experimenter = PyExperimenter(experiment_configuration_file_path=experiment_configuration_file_path, name='example_notebook')

    ###### Fill Table ######

    experimenter.fill_table_from_config()

    experimenter.fill_table_with_rows(rows=[
        {'dataset': 'new_data', 'cross_validation_splits': 3, 'seed': 42, 'kernel': 'linear'}])

    # showing database table
    table = experimenter.get_table()
    print("Table before execution")
    print(table)

    ###### Execute all Experiments ######
    experimenter.execute(run_ml, max_experiments=-1, random_order=True)

    # showing database table
    talbe = experimenter.get_table()
    print("Table after execution")
    print(table)

    ###### Reset Experiments ######

    experimenter.reset_experiments('error')

    # showing database table
    table = experimenter.get_table()
    print(table)

    ###### Execute reset Experiments ######

    experimenter.execute(run_ml, max_experiments=-1, random_order=True)

    # showing database table
    table = experimenter.get_table()
    print(table)

    ###### Create Output ######

    result_table_agg = experimenter.get_table().groupby(['dataset']).mean()
    print(result_table_agg)

    ###### Create Latex Table ######

    print(result_table_agg.to_latex(columns=['test_f1'], index_names=['dataset']))
