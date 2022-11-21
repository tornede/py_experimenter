# General Workflow

A general schema of `PyExperimenter` can be found in the Figure below.
`PyExperimenter` is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., parameters, and a function computing the results of the experiment based on these parameters.
The set of experiments to be executed can be defined through a configuration file listing the domains of each parameter, or manually through code.
Those parameters define the experiment grid, based on which `PyExperimenter` setups the table in the database featuring all experiments with their input parameter values and additional information such as the execution status.
Once this table has been created, a `PyExperimenter` instance can be run on any machine, including a distributed system.
Each instance automatically pulls open experiments from the database, executes the function provided by the user with the corresponding parameters defining the experiment and writes back the results computed by the function.
Errors arising during the execution are logged in the database.
In case of failed experiments or if desired otherwise, a subset of the experiments can be reset and restarted easily.
After all experiments are done, results can be jointly exported as a `Pandas DataFrame` for further processing, such as generating a LaTeX table averaging results of randomized computations over different seeds.

![General schema of `PyExperimenter`.][workflow]

The following steps are necessary to execute the `PyExperimenter`:

1. Create the [experiment configuration file](usage.html#experiment-configuration-file), defining the database provider and the table structure.
    - In case the database provider is `MySQL`, additionally a [database credential file](usage.html#database-credential-file) has to be created.
2. Define the [experiment function](usage.html#defining-the-experiment-function), computing the experiment result based on the input parameters.
3. [Execute the experiments](usage.html#executing-the-pyexperimenter), writing the results into the database table.
4. Finally, the results of different experiment configurations can be viewed in the database table, or [extracted to a LaTeX table](usage.html#obtain-results).

[workflow]: _static/workflow.png
