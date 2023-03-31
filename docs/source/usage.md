# Usage

## Experiment Configuration File

The experiment configuration file is primarily used to define the database backend, as well as execution parameters, i.e. keyfields, and result fields.

```
[PY_EXPERIMENTER]
provider = sqlite 
database = database_name
table = table_name 

keyfields = dataset, cross_validation_splits:int, seed:int, kernel
dataset = iris
cross_validation_splits = 5
seed = 2:10:2 
kernel = linear, poly, rbf, sigmoid

n_jobs = 5 

resultfields = pipeline:LONGTEXT, train_f1:DECIMAL, train_accuracy:DECIMAL, test_f1:DECIMAL, test_accuracy:DECIMAL
resultfields.timestamps = false

[CUSTOM] 
path = sample_data
```

- `provider`: Either `sqlite` or `mysql`. In case of `mysql` an additional [database credential file](#database-credential-file) has to be created.
- `database`: The name of the database.
- `table`: The name of the table to write the experiment information into.
- `keyfields`: The columns of the table that will define the execution of the experiments. Optionally, the field types can be attached. For each keyfield, an additional entry to the config file with the same name has to be added, which defines the domain of the keyfield.
- `resultfields`: The columns of the table that will store the results of the execution of the experiments. Optionally, the field types can be attached.
- `resultfields.timestamps`: Boolean defining if additional timestamp columns are needed for each resultfield.

Both keyfields and resultfields can have further annotations for the data type. This is done by attaching `:<TYPE>` to the according fields. If no data type is explicitly specified, `VARCHAR(255)` is used.

Keyfields of the experiment configuration, that do not have to be explicitly defined in the list of keyfields, are:

- `n_jobs (int)`: The maximum number of experiments that will be executed in parallel.

Additionally, the user can define which values the keyfields can take on. Usually this is done with a comma separated list of strings or numbers. In the example above, the key field `kernel` can be any of the four given values: `linear`, `poly`, `rbf`, or `sigmoid`. Note that strings are neither allowed to contain any quotation marks nor whitespace.

As this manual definition can be a tedious task, especially for a list of integers, there is the option to define the start and the end of the list, together with the step size in the form: `start:end:stepsize`. In the example above, `seed` is meant to be `2, 4, 6, 8, 10`, but instead of the explicit list `2:10:2` is given.

Optionally, custom configurations can be defined under the `CUSTOM` section, which will be ignored when creating or filling the database, but can provide fixed parameters for the actual execution of experiments. A common example is the path to some folder in which the data is located.

---

## Database Credential File

When working with `MySQL` as a database provider, an additional database credential file is needed, containing the credentials for accessing the database:

```
[CREDENTIALS]
host = <host>
user = <user>
password = <password>
```

By default, this file is located at `config/database_credentials.cfg`. If this is not the case, the according path has to be explicitly given when [executing `PyExperimenter`](#executing-the-pyexperimenter).

---

## Defining the Experiment Function

The execution of a single experiment has to be defined within a function. The function is called with the `keyfields` of a database entry. The results are meant to be processed to be written into the database, i.e. as `resultfields`.

```python
import os
from py_experimenter.result_processor import ResultProcessor

def run_experiment(keyfields: dict, result_processor: ResultProcessor, custom_fields: dict):
    # Extracting given parameters
    seed = keyfields['seed']
    path = os.path.join(custom_fields['path'], keyfields['dataset'])

    # Do some stuff here

    # Write intermediate results to database    
    resultfields = {
        'pipeline': pipeline, 
        'train_f1': train_f1_micro,
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

The actual execution of `PyExperimenter` only needs a few lines of code. Please make sure that you have created the [experiment configuration file](#experiment-configuration-file). Below the core functionality is elaborated on.

```python
from py_experimenter.experimenter import PyExperimenter

experimenter = PyExperimenter()
experimenter.fill_table_from_config()
experimenter.execute(run_experiment, max_experiments=-1)
```

### Creating a PyExperimenter

A `PyExperimenter` can be created without any further information, assuming the [experiment configuration file](#experiment-configuration-file) can be accessed at its default location.

```python
experimenter = PyExperimenter()
```

Additionally, further information can be given to `PyExperimenter`:

- `experiment_configuration_file_path`: The path of the [experiment configuration file](#experiment-configuration-file). Default: `config/configuration.cfg`
- `database_credential_file_path`: The path of the [database credential file](#database-credential-file). Default: `config/database_credentials.cfg`
- `database_name`: The name of the database to manage the experiments.
- `table_name`: The name of the database table to manage the experiments.
- `name`: The name of the experimenter, which will be added to the database table of each executed experiment by this `PyExperimenter`. If using parallel HPC, this is meant to be used for the job ID, so that the according log file can easily be found.

### Fill Database Table Based on the Configuration File

The database table can be filled with the cartesian product of the keyfields defined in the [experiment configuration file](#experiment-configuration-file).

```python
experimenter.fill_table_from_config()
```

### Fill Table with Specific Rows

Alternatively, or additionally, specific rows can be added to the table. Note that `rows` is a list of dicts, where each dict has to contain a value for each keyfield. A more complex example example featuring a conditional experiment grid using this approach can be found in the [examples section](examples).

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

An experiment can be executed easily with the following call:

```python
experimenter.execute(
    experiment_function = run_experiment, 
    max_experiments = -1
)
```

- `experiment_function` is the [experiment funtion](#defining-the-experiment-function) described above.
- `max_experiments` determines how many experiments will be executed by this `PyExperimenter`. If set to `-1`, it will execute experiments in a sequential fashion until no more open experiments are available.

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

The current content of the database table can be obtained as `pandas.DataFrame`. This can be used to generate a result table and export it to LaTeX.

```python
result_table = experimenter.get_table()
result_table = result_table.groupby(['dataset']).mean()[['seed']]
print(result_table.to_latex(columns=['seed'], index_names=['dataset']))
```

## Logtables

In addition to the stated above functionality, PyExperimenter also support logtables thereby enabling the logging of information into separate tables. They have to be specified in the configuration file by adding a line starting with `logtables = ...`. There are two different ways of defining logtables:

Standard notation:

`logtables = train_scores:log_train_scores...`  
`log_train_scores = f1:DOUBLE, accuracy:DOUBLE, kernel:str`

Shorthand notation

`logtables = ..., test_f1:DOUBLE, test_accuracy:DOUBLE`.

Note that the tables in the database are then called `table_name__logtable_name`. In addition to the specified columns, each logtable has a column `experiment_id` referencing the standard table and `timestamp`.

They can be filled in the execution process by calling
```python
def run_ml(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    ...
	result_processor.process_logs(
		{
			'train_scores': {
				'f1': np.mean(scores['train_f1_micro']),
				'accuracy': np.mean(scores['train_accuracy']),
				'kernel': "'" + kernel + "'"
			},
			'test_f1': {
				'test_f1': np.mean(scores['test_f1_micro'])},
			'test_accuracy': {
				'test_accuracy': np.mean(scores['test_accuracy'])},
		}
	)
	...
```
There is an [in-depth example](examples/example_logtables.ipynb) showcasing the usage of logtables.