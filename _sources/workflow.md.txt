# General Workflow

The following steps are necessary to execute the `PyExperimenter`:

1. Create the [experiment configuration file](usage.html#experiment-configuration-file), defining the database provider and the table structure.
    - In case the database provider is `MySQL`, additionally a [database configuration file](usage.html#database-configuration-file) has to be created.
2. Define the [experiment function](usage.html#defining-the-experiment-function), computing the experiment result based on the input parameters.
3. [Execute the experiments](usage.html#executing-the-pyexperimenter), writing the results into the database table.
4. Finally, the results of different experiment configurations can be viewed in the database table, or [extracted to a LaTeX table](usage.html#obtain-results).

![General schema of `PyExperimenter`.][workflow]

[workflow]: _static/workflow.png
