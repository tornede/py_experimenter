.. _execution:

============================
Executing PyExperimenter
============================

The actual execution of ``PyExperimenter`` only needs a few lines of code. Please make sure that you have created the :ref:`experiment configuration file <experiment_configuration_file>` and defined the :ref:`experiment function <experiment_function>` beforehand. 

.. code-block:: 

    from py_experimenter.experimenter import PyExperimenter

    experimenter = PyExperimenter()
    experimenter.fill_table_from_config()
    experimenter.execute(run_experiment, max_experiments=-1)

The above code will execute all experiments defined in the :ref:`experiment configuration file <experiment_configuration_file>`. If you want to do something different, e.g. :ref:`fill the database table with specific rows <fill_table_with_rows>`, or :ref:`reset experiments <reset_experiments>`, check out the following sections.

.. _execution_creating_pyexperimenter:

-------------------------
Creating a PyExperimenter
-------------------------

A ``PyExperimenter`` can be created without any further information, assuming the :ref:`experiment configuration file <experiment_configuration_file>` can be accessed at its default location.

.. code-block:: 

    experimenter = PyExperimenter()

Additionally, further information can be given to ``PyExperimenter``:

- ``experiment_configuration_file_path``: The path of the :ref:`experiment configuration file <experiment_configuration_file>`. Default: ``config/experiment_configuration.cfg``.
- ``database_credential_file_path``: The path of the :ref:`database credential file <database_credential_file>`. Default: ``config/database_credentials.cfg``
- ``database_name``: The name of the database to manage the experiments. If given, it will overwrite the database name given in the `experiment_configuration_file_path`.
- ``table_name``: The name of the database table to manage the experiments. If given, it will overwrite the table name given in the `experiment_configuration_file_path`.
- ``use_codecarbon``: Specifies if :ref:`CodeCarbon <experiment_configuration_file_codecarbon>` will be used to track experiment emissions. Default: ``True``. 
- ``name``: The name of the experimenter, which will be added to the database table of each executed experiment. If using the PyExperimenter on an HPC system, this can be used for the job ID, so that the according log file can easily be found. Default: ``PyExperimenter``.
- ``logger_name``: The name of the logger, which will be used to log information about the execution of the PyExperimenter. If there already exists a logger with the given ``logger_name``, it will be used instead. However, the ``log_file`` will be ignored in this case. The logger will then be passed to every component of ``PyExperimenter``, so that all information is logged to the same file. Default: ``py-experimenter``.
- ``log_level``: The log level of the logger. Default: ``INFO``.
- ``log_file``: The path of the log file. Default: ``py-experimenter.log``.	 


-------------------
Fill Database Table
-------------------

The database table can be filled in two ways:

- :ref:`Fill table from experiment configuration file <fill_table_from_config>`
- :ref:`Fill table with specific rows <fill_table_with_rows>`


.. _fill_table_from_config:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Fill Table From Experiment Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The database table can be filled with the cartesian product of the keyfields defined in the :ref:`experiment configuration file <experiment_configuration_file>`.

.. code-block:: 

    experimenter.fill_table_from_config()


.. _fill_table_with_rows:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Fill Table With Specific Rows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, or additionally, specific rows can be added to the table. Note that ``rows`` is a list of dicts, where each dict has to contain a value for each keyfield. A more complex example featuring a conditional experiment grid can be found in the :ref:`examples section <examples>`.

.. code-block:: 

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


-------------------
Execute Experiments
-------------------

An experiment can be executed easily with the following call:

.. code-block:: 

    experimenter.execute(
        experiment_function = run_experiment, 
        max_experiments = -1
        random_order = False
    )

- ``experiment_function`` is the previously defined :ref:`experiment funtion <experiment_function>`.
- ``max_experiments`` determines how many experiments will be executed by this ``PyExperimenter``. If set to ``-1``, it will execute experiments in a sequential fashion until no more open experiments are available.
- ``random_order`` determines if the experiments will be executed in a random order. By default, the parameter is set to ``False``, meaning that experiments will be executed ordered by their ``id``.

.. _reset_experiments:

-----------------
Reset Experiments
-----------------

Each database table contains a ``status`` column, summarizing the current state of an experiment. Experiments can be reset based on these status. If this is done, the table rows having a given status will be deleted, and corresponding new rows without results will be created. A comma separated list of ``status`` has to be provided.

.. code-block:: 
    
    experimenter.reset_experiments(<status>, <status>, ...)

The following status exist:

- ``created``: All parameters for the experiment are defined and the experiment is ready for execution.
- ``running``: The experiment is currently in execution.
- ``done``: The execution of the experiment terminated without interruption and the results are written into the database.
- ``error``: An error occurred during execution, which is also logged into the database.
- ``paused``: The experiment was paused during execution. For more information check :ref:`pausing and unpausing experiments <pausing_and_unpausing_experiments>`.


.. _obtain_results:

--------------
Obtain Results
--------------

The current content of the database table can be obtained as a ``pandas.DataFrame``. This can, for example, be used to generate a result table and export it to LaTeX.

.. code-block:: 

    result_table = experimenter.get_table()
    result_table = result_table.groupby(['dataset']).mean()[['seed']]
    print(result_table.to_latex(columns=['seed'], index_names=['dataset']))


.. _execution_codecarbon:

----------
CodeCarbon
----------

Tracking information about the carbon footprint of experiments is supported via :ref:`CodeCarbon <experiment_configuration_file_codecarbon>`. Tracking is enabled by default, as described in :ref:`how to create a PyExperimenter <execution_creating_pyexperimenter>`. If the tracking is enabled, the according information can be found in the database table ``<table_name>_codecarbon``, which can be easily accessed with the following call:

.. code-block::

    experimenter.get_codecarbon_table()

---------------------------------
Pausing and Unpausing Experiments
---------------------------------

For convenience, we support pausing and unpausing experiments. This means that you can use one experiment to run multiple experiment funcitons, by finishing the first experiment with a pause and then continuing with a second (differing) experiment function.
Note that this function does not support parralelisation and the experimentid has to be given explicitly. For more information check the exmaple.
