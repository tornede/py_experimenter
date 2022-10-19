<img src="docs/source/_static/py-experimenter-logo.png" alt="PyExperimenter Logo: Python biting a database" width="200px"/>

# PyExperimenter

The `PyExperimenter` is a tool for the automatic execution of experiments, e.g. for machine learning (ML), capturing corresponding results in a unified manner in a database. It is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing the results of the experiment based on these input parameters. The set of experiments to be executed can be defined through a configuration file listing the domains of each experiment parameter, or manually through code. Based on the set of experiments defined by the user, `PyExperimenter` creates a table in the database featuring all experiments identified by their input parameter values and additional information such as the execution status. Once this table has been created, `PyExperimenter` can be run on any machine, including a distributed cluster. Each `PyExperimenter` instance automatically pulls open experiments from the database, executes the experiment function provided by the user with the corresponding experiment parameters defining the experiment and writes back the results computed by the function. Possible errors arising during the execution are logged in the database. After all experiments are done, the experiment evaluation table can be easily extracted, e.g. averaging over different seeds.

For more details check out the [`PyExperimenter` documentation](https://tornede.github.io/py_experimenter/):

- [Installation](https://tornede.github.io/py_experimenter/installation.html)
- [Quick start](https://tornede.github.io/py_experimenter/examples/example_general_usage.html)
- [License](https://tornede.github.io/py_experimenter/license.html)

![General schema of `PyExperimenter`.](docs/source/_static/workflow.png)
