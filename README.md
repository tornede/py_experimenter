# PyExperimenter

The `PyExperimenter` is a tool for the automatic execution of, e.g. machine learning (ML), experiments and capturing corresponding results in a unified manner in a database. It supports both sqlite or mysql backends. The experiments to conduct can be defined via a configuration file or in custom way through code. Based on that, a table with initial properties, e.g. different seeds for an ML algorithm, is filled. During execution, a custom defined function requested to compute the results for a single row of the table. Those results, e.g. performances, can be added to the table at the end of the execution. Errors occurring during the execution are logged in the database. Afterwards, experiment evaluation tables can be easily extracted, e.g. averaging over different seeds. 


## Installation

The `PyExperimenter` module can be easily installed via PyPI, requirements can be found in the [requirements file](requirements.txt). 

```
pip install py-experimenter
```

## General Workflow

To actually execute the `PyExperimenter` the following steps are necessary:
1. The [experiment configuration file](#experiment-configuration-file) has to be created, defining the database provider and the table structure.
    - In case the database provider is `MySQL`, additionally a [database configuration file](#database-configuration-file) has to be created.
3. The general [experiment function](#defining-the-experiment-function) has to be defined.
4. Next, the [experiments can be executed](#executing-the-pyexperimenter), writing the results into the database table.
5. Finally, the results of different experiment configurations can be viewed in the database table, or [extracted to a LaTex table](#obtain-table).

In the [`examples` folder of the repository](examples/), you can find examples for most of the functionality explained here. A complete example of the general usage of `PyExperimenter` can be found in [examples/example_general_usage.ipynb](examples/example_general_usage.ipynb). 


--- 

## Experiment Configuration File
The experiment configuration file is primarily used to define the database backend, as well as execution parameters, i.e. keyfields, and result fields.

```conf
[PY_EXPERIMENTER]
provider = sqlite 
database = database_name
table = table_name 

keyfields = dataset, cross_validation_splits:int, seed:int, kernel
dataset = iris
cross_validation_splits = 5
seed = 2:10:2 
kernel = linear, poly, rbf, sigmoid

cpu.max = 5 

resultfields = pipeline:LONGTEXT, train_f1:DECIMAL, train_accuracy:DECIMAL, test_f1:DECIMAL, test_accuracy:DECIMAL
resultfields.timestamps = false

[CUSTOM] 
path = sample_data
```

- `provider`: Either `sqlite` or `mysql`. In case of `mysql` an additional [database configuration file](#database-configuration-file) has to be created.
- `database`: The name of the database.
- `table`: The name of the table to write the experiment information into.
- `keyfields`: The columns of the table that will define the execution of the experiments. Optionally, the field types can be attached. 
- `resultfields`: The columns of the table that will store the results of the execution of the experiments. Optionally, the field types can be attached. 
- `resultfields.timestamps`: Boolean defining if additional timestamp columns are needed for each resultfield.

Both keyfields and resultfields can have further annotations for the data type. This is done by attaching `:<TYPE>` to the according fields. If no data type is explicitly specified, `VARCHAR(255)` is used.

Keyfields of the experiment configuration, that don't have to be explicitly defined in the list of keyfields, are:
- `cpu.max (int)`: The maximum number of CPUs allowed for each experiment execution. 

Additionally, the user can define which values the keyfields can take on. Usually this is done with a comma separated list of strings or numbers, like `kernel` can be any of the four given values: `linear`, `poly`, `rbf`, or `sigmoid`. Not that strings are not allowed to contain any quotation marks, nor whitespace. 

As this is a tedious task especially for a list of integers, there is the option to define the start and the end of the list, together with the step size in the form: `start:end:stepsize`. In the example, `seed` is meant to be `2, 4, 6, 8, 10`, but instead of the explicit list `2:10:2` is given.

Optionally, custom configurations can be defined under the `CUSTOM` section, which will be ignored when creating or filling the database, but can provide fixed parameters for the actual execution of experiments, like a path to some folder in which the data lays. 

----

## Database Configuration File
When working with `MySQL` an additional database configuration file is needed, containing the credentials to the database:
```
[CREDENTIALS]
host = <host>
user = <user>
password = <password>
```

Per default, this file is located at `config/database_credentials.cfg`. If this is not the case, the according path has to be explicitly given when [executing the `PyExperimenter`](#executing-the-pyexperimenter). 

--- 

## Defining the Experiment Function
The execution of a single experiment has to be defined within a method. The method is called with the `keyfields` of a database entry. The results are meant to be processed to be written into the database, i.e. as `resultfields`. 


```python
import os
from py_experimenter.result_processor import ResultProcessor

def run_experiment(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    # Extracting given parameters
    seed = keyfields['seed']
    path = os.path.join(custom_config['path'], keyfields['dataset'])

    # Do some stuff here

    # Write intermediate results to database    
    resultfields = {
        'pipeline': pipeline, 
        'train_f1': train_f1_micro),
        'train_accuracy': train_accuracy}
    result_processor.process_results(resultfields)

    # Do more some stuff here

    # Write final results to database
    resultfields = {
        'test_f1': np.mean(scores['test_f1_micro']),
        'test_accuracy': np.mean(scores['test_accuracy'])}
    result_processor.process_results(resultfields)
```

---

## Executing the PyExperimenter
The actual execution of the `PyExperimenter` only needs a few lines of code. Please make sure that you have created the [experiment configuration file](#experiment-configuration-file). Below the core functionality is elaborated on.


```python
import logging
from py_experimenter.experimenter import PyExperimenter

logging.basicConfig(level=logging.INFO)

experimenter = PyExperimenter()
experimenter.fill_table_from_config()
experimenter.execute(run_experiment, max_experiments=-1, random_order=True)
```

### Creating a PyExperimenter
A `PyExperimenter` can be created without any further information, assuming the [experiment configuration file](#experiment-configuration-file) can be accessed at its default location.

```python 
experimenter = PyExperimenter()
```

Additionally, further information can be given to the `PyExperimenter`: 
- `config_file`: The path of the [experiment configuration file](#experiment-configuration-file). Default: `config/configuration.cfg`
- `credential_path`: The path of the [database credentials file](#database-configuration-file). Default: `config/database_credentials.cfg`
- `database_name`: The name of the database to manage the experiments.
- `table_name`: The name of the database table to manage the experiments.
- `name`: The name of the experimenter, which will be added to the database table of each executed experiment by this `PyExperimenter`. If using parallel HPC, this is meant to be used for the job ID, so that the according log file can easily be found.

### Fill Table based on the Configuration File
The database table can be filled with the cartesian product of the keyfields defined in the [experiment configuration file](#experiment-configuration-file).
```python 
experimenter.fill_table_from_config()
```

### Fill Table with Specific Rows
Alternatively, or additionally, specific rows can be added to the table. Note that `rows` is a list of dicts, where each dict has to contain all keyfields. In the [repository (examples/example_conditional_grid.ipynb)](examples/example_conditional_grid.ipynb), there is a more complex example with a restricted version of the cartesian product, i.e. a conditional experiment grid, using this method.
```python 
experimenter.fill_table_with_rows(rows=[
    {
        'dataset': 'new_data', 
        'cross_validation_splits': 4, 
        'seed': 42, 
        'kernel': 'poly'
    }
])
```

### Execute Experiments
An experiment can be executed given:
- `run_experiment` is the [experiment funtion](#defining-the-experiment-function) described above.
- `max_experiments` determins how many experiments will be executed by this `PyExperimenter`. If set to `-1`, all experiments will be executed.
- `random_order` determines if the order in which experiments are selected for execution should be random. This is especially important if the execution is parallelized, e.g. on an HPC cluster.  

```python
experimenter.execute(run_experiment, max_experiments=-1, random_order=True)
```

### Reset Experiments
Experiments can be reset based on their status. Therefore, the table rows having a given status will be deleted, and new rows having the same configuration will be created. 

```python
experimenter.reset_experiments(status='error')
```

Each database table contains a `status` column, summarizing the current state of an experiment.
- `created`: All parameters for the experiment instance are defined and the instance is ready for execution.
- `running`: The experiment is currently in execution.
- `done`: The execution of the experiment terminated without interruption and the results are written into the database
- `error`: An error occurred during execution, which is also logged into the database.

### Obtain Table
The current content of the database table can be obtained as `pandas.Dataframe`. This can be further used to generate a result table and export it to LaTex.

```python
result_table = experimenter.get_table()
result_table = result_table.groupby(['dataset']).mean()[['seed']]
print(result_table.to_latex(columns=['seed'], index_names=['dataset']))
```
