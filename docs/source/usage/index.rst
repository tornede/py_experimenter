.. _usage:

=================
Usage
=================

A general schema of ``PyExperimenter`` can be found in the Figure below.
``PyExperimenter`` is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., parameters, and a function computing the results of the experiment based on these parameters.
The set of experiments to be executed can be defined through a configuration file listing the domains of each parameter, or manually through code.
Those parameters define the experiment grid, based on which ``PyExperimenter`` setups the table in the database featuring all experiments with their input parameter values and additional information such as the execution status.
Once this table has been created, a ``PyExperimenter`` instance can be run on any machine, including a distributed system.
Each instance automatically pulls open experiments from the database, executes the function provided by the user with the corresponding parameters defining the experiment and writes back the results computed by the function.
Errors arising during the execution are logged in the database.
In case of failed experiments or if desired otherwise, a subset of the experiments can be reset and restarted easily.
Overall, :ref:`CodeCarbon <experiment_configuration_file_codecarbon>` is used to track the carbon emissions of each experiment into a separate table.
After finishing all experiments, results can be jointly exported as a ``Pandas DataFrame`` for further processing, such as generating a LaTeX table averaging results of randomized computations over different seeds.

.. figure:: ../_static/workflow.png
   :width: 600px
   :alt: General schema of PyExperimenter
   :align: center
   
|

The following steps are necessary to execute the ``PyExperimenter``.

1. Create the :ref:`experiment configuration file <experiment_configuration_file>`, defining the database provider and the table structure. In case the database provider is ``MySQL``, additionally a :ref:`database credential file <database_credential_file>` has to be created.
2. Define the :ref:`experiment function <experiment_function>`, computing the experiment result based on the input parameters.
3. :ref:`Execute the experiments <execution>`, writing the results into the database table.
4. Finally, the results of different experiment configurations can be viewed in the database table, or :ref:`extracted to a LaTeX table <obtain_results>`.

.. toctree::
   :maxdepth: 3
   :hidden:
   :caption: Usage

   ./experiment_configuration_file
   ./database_credential_file
   ./experiment_function
   ./execution
