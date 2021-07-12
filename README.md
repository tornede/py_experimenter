# PyExperimenter

## Installation and configuration
In order to install the package via pip use the command
```
pip install py_experimenter
```
You can also download the git repositiory and import the py_experimenter manually.

After the installation you need to create a configuration file with information about the database and the experiment.
Please use the `example_config.clg` as an example. You can also define custom configuration filds under the
`CUSTOM` section in the configuration file. Those parameters will not affect the experimenter but will be passed
to the user function as a dictionary.

## First Steps
To use the PyExperimenter for your experiments, create a function with 3 parameters.
```
def own_function(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
```
This function will be called by the PyExperimenter to process each instance of the experiment.

## Further usage