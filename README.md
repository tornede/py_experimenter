# PyExperimenter

The `PyExperimenter` is a tool for the automatic execution of experiments, e.g. for machine learning (ML), capturing corresponding results in a unified manner in a database. It is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing the results of the experiment based on these input parameters. The set of experiments to be executed can be defined through a configuration file listing the domains of each experiment parameter, or manually through code. Based on the set of experiments defined by the user, `PyExperimenter` creates a table in the database featuring all experiments identified by their input parameter values and additional information such as the execution status. Once this table has been created, `PyExperimenter` can be run on any machine, including a distributed cluster. Each `PyExperimenter` instance automatically pulls open experiments from the database, executes the experiment function provided by the user with the corresponding experiment parameters defining the experiment and writes back the results computed by the function. Possible errors arising during the execution are logged in the database. After all experiments are done, the experiment evaluation table can be easily extracted, e.g. averaging over different seeds.


## Installation

The `PyExperimenter` module can be easily installed via PyPI, requirements can be found in the [requirements file](requirements.txt). 

```
pip install py-experimenter
```

## General Workflow

The following steps are necessary to execute the `PyExperimenter`:
1. Create the [experiment configuration file](#experiment-configuration-file), defining the database provider and the table structure.
    - In case the database provider is `MySQL`, additionally a [database configuration file](#database-configuration-file) has to be created.
3. Define the [experiment function](#defining-the-experiment-function), computing the experiment result based on the input parameters.
4. [Execute the experiments](#executing-the-pyexperimenter), writing the results into the database table.
5. Finally, the results of different experiment configurations can be viewed in the database table, or [extracted to a LaTeX table](#obtain-results).

Detailed examples of most functionality can be found in the [`examples` folder of the repository](examples/). A complete example of the general usage of `PyExperimenter` can be found in [examples/example_general_usage.ipynb](examples/example_general_usage.ipynb). 


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
- `keyfields`: The columns of the table that will define the execution of the experiments. Optionally, the field types can be attached. For each keyfield, an additional entry to the config file with the same name has to be added, which defines the domain of the keyfield.
- `resultfields`: The columns of the table that will store the results of the execution of the experiments. Optionally, the field types can be attached. 
- `resultfields.timestamps`: Boolean defining if additional timestamp columns are needed for each resultfield.

Both keyfields and resultfields can have further annotations for the data type. This is done by attaching `:<TYPE>` to the according fields. If no data type is explicitly specified, `VARCHAR(255)` is used.

Keyfields of the experiment configuration, that do not have to be explicitly defined in the list of keyfields, are:
- `cpu.max (int)`: The maximum number of CPUs allowed for each experiment execution. 

Additionally, the user can define which values the keyfields can take on. Usually this is done with a comma separated list of strings or numbers. In the example above, the key field `kernel` can be any of the four given values: `linear`, `poly`, `rbf`, or `sigmoid`. Note that strings are neither allowed to contain any quotation marks nor whitespace. 

As this manual definition can be a tedious task, especially for a list of integers, there is the option to define the start and the end of the list, together with the step size in the form: `start:end:stepsize`. In the example above, `seed` is meant to be `2, 4, 6, 8, 10`, but instead of the explicit list `2:10:2` is given.

Optionally, custom configurations can be defined under the `CUSTOM` section, which will be ignored when creating or filling the database, but can provide fixed parameters for the actual execution of experiments. A common example is the path to some folder in which the data is located. 

----

## Database Configuration File
When working with `MySQL` as a database provider, an additional database configuration file is needed, containing the credentials for accessing the database:
```
[CREDENTIALS]
host = <host>
user = <user>
password = <password>
```

By default, this file is located at `config/database_credentials.cfg`. If this is not the case, the according path has to be explicitly given when [executing the `PyExperimenter`](#executing-the-pyexperimenter). 

--- 

## Defining the Experiment Function
The execution of a single experiment has to be defined within a function. The function is called with the `keyfields` of a database entry. The results are meant to be processed to be written into the database, i.e. as `resultfields`. 


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

### Fill Database Table Based on the Configuration File
The database table can be filled with the cartesian product of the keyfields defined in the [experiment configuration file](#experiment-configuration-file).
```python 
experimenter.fill_table_from_config()
```

### Fill Table with Specific Rows
Alternatively, or additionally, specific rows can be added to the table. Note that `rows` is a list of dicts, where each dict has to contain a value for each keyfield. A more complex example example featuring a conditional experiment grid using this approach can be found in the [repository (examples/example_conditional_grid.ipynb)](examples/example_conditional_grid.ipynb).

```python 
experimenter.fill_table_with_rows(rows=[
    {
        'dataset': 'new_data', 
        'cross_validation_splits': 4, 
        'seed': 42, 
        'kernel': 'poly'
    },
    {
        'dataset': 'new_data_2', 
        'cross_validation_splits': 4, 
        'seed': 24, 
        'kernel': 'poly'
    }
])
```

### Execute Experiments
An experiment can be executed given:
- `run_experiment` is the [experiment funtion](#defining-the-experiment-function) described above.
- `max_experiments` determines how many experiments will be executed by this `PyExperimenter`. If set to `-1`, it will execute experiments in a sequential fashion until no more open experiments are available.
- `random_order` determines if the order in which experiments are selected for execution should be random. This is especially important to be turned on, if the execution is parallelized, e.g. on an HPC cluster.  

```python
experimenter.execute(run_experiment, max_experiments=-1, random_order=True)
```

### Reset Experiments
Experiments can be reset based on their status. Therefore, the table rows having a given status will be deleted, and corresponding new rows without results will be created. 

```python
experimenter.reset_experiments(status='error')
```

Each database table contains a `status` column, summarizing the current state of an experiment. The following exist: 
- `created`: All parameters for the experiment are defined and the experiment is ready for execution.
- `running`: The experiment is currently in execution.
- `done`: The execution of the experiment terminated without interruption and the results are written into the database
- `error`: An error occurred during execution, which is also logged into the database.

### Obtain Results
The current content of the database table can be obtained as `pandas.Dataframe`. This can be used to generate a result table and export it to LaTeX.

```python
result_table = experimenter.get_table()
result_table = result_table.groupby(['dataset']).mean()[['seed']]
print(result_table.to_latex(columns=['seed'], index_names=['dataset']))
```
