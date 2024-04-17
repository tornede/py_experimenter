.. _experiment_configuration_file:

=============================
Experiment Configuration File
=============================

The experiment configuration file is primarily used to define the database backend, as well as execution parameters, i.e. keyfields, resultfields, and logtables. An example experiment configuration can be found in the following, covering the main functionality ``PyExperimenter`` provides. Each part is described in the subsections below.

.. code-block:: yaml

    PY_EXPERIMENTER:
      n_jobs: 1

      Database:
        provider: sqlite
        database: py_experimenter
        use_ssh_tunnel: False
        table: 
          name: example_general_usage
          keyfields:
            dataset:
              type: VARCHAR(255)
              values: ['dataset1', 'dataset2', 'dataset3']
            cross_validation_splits:
              type: INT
              values: [3, 5]
            seed:
              type: INT 
              values:
                start: 0
                stop: 5
                step: 1
            kernel:
              type: VARCHAR(255)
              values: ['linear', 'poly', 'rbf', 'sigmoid']
              
          resultfields:
            pipeline: LONGTEXT
            train_f1: DOUBLE
            train_accuracy: DOUBLE
            test_f1: DOUBLE
            test_accuracy: DOUBLE
          result_timestamps: False
                
        logtables:
          pipeline_evaluations:
            kernel: VARCHAR(50)
            f1: DOUBLE
            accuracy: DOUBLE
          incumbents:
            pipeline: LONGTEXT
            performance: DOUBLE
        
      Custom:
        datapath: path/to/data
        
      CodeCarbon:
        offline_mode: False
        measure_power_secs: 25
        tracking_mode: process
        log_level: error
        save_to_file: True
        output_dir: output/CodeCarbon

--------------------
Database Information
--------------------

The ``Database`` section defines the database and its structure.

- ``provider``: The provider of the database connection. Currently, ``sqlite`` and ``mysql`` are supported. In the case of ``mysql`` an additional :ref:`database credential file <database_credential_file>` has to be created.
- ``database``: The name of the database to create or connect to.
- ``use_ssh_tunnel``: Flag to decide if the database is connected via ssh as defined in the :ref:`database credential file <database_credential_file>`. This is ignored if ``sqlite`` is chosen as provider. Optional Parameter, default is False.
- ``table``: Defines the structure and predefined values for the experiment table. 

    - ``name``: The name of the experiment table to create or connect to.
    - ``keyfields``: The keyfields of the table, which define an experiment. More details about the keyfields can be found in the :ref:`keyfields section <keyfields>`.
    - ``resultfields``: The resultfields of the table, i.e. the fields to write resulting information of the experiments to. More details about the resultfields can be found in the :ref:`resultfields section <resultfields>`.
 

.. _keyfields:


Keyfields
---------

Experiments are identified by ``keyfields``, hence, keyfields define the execution of experiments. A keyfield can be thought of as a parameter, whose value defines an experiment together with the values of all other experiments. Each ``keyfield`` is defined by a name and the following information in the ``table`` section of the experiment configuration file:

- ``type``: The type of the keyfield. Supported types are ``VARCHAR``, ``INT``, ``NUMERIC``, ``DOUBLE``, ``LONGTEXT``, ``DATETIME``.
- ``values``: The values the keyfield can take. This can be a comma separated list of values or a range of values. The range of values can be defined by:

    - ``start``: The starting value of the range (including).
    - ``stop``: The end value of the range (excluding).
    - ``step`` (optional): The step size to use to generate all values. Default is ``1``.

In the following, an example of keyfields is given for each typically used type. An in-depth example showcasing the usage general usage can be found within the :ref:`examples section <examples>`.

.. code-block:: yaml

    Database:

      keyfields:

        string_input_name:
          type: VARCHAR(255)
          values: ['dataset1', 'dataset2', 'dataset3']

        int_input_name:
          type: INT
          values: [1, 2, 3, 4, 5]

        int_shortened_input_name:
          type: INT
          values:
            start: 1
            stop: 5
            step: 1

        numeric_input_name:
          type: NUMERIC
          values: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
        numeric_shortened_input_name:
          type: NUMERIC
          values:
            start: 1
            stop: 5
            step: 0.5


.. _resultfields:

Resultfields
------------

The results of the experiments will be stored in the database in the form of ``resultfields``. They are optional and are also contained in the ``table`` section of the experiment configuration file. Each resultfield consists of a name and type. Supported types are ``VARCHAR``, ``INT``, ``NUMERIC``, ``DOUBLE``, ``LONGTEXT``, ``DATETIME``. Additionally, it is possible to store the timestamps at which the results have been obtained in the database (Default is ``False``). They are :ref:`filled with the information provided by the experiment function <experiment_function_resultfields>`.

In the following, an example of resultfields is given for two typically used types. An in-depth example showcasing the usage general usage can be found within the :ref:`examples section <examples>`.

.. code-block:: yaml

    Database:

      resultfields:
        pipeline: LONGTEXT
        performance: DOUBLE
      result_timestamps: False


.. _logtables:

Logtables
---------

In addition to the functionality stated above, ``PyExperimenter`` also supports ``logtables``, thereby enabling the logging of information into separate tables. This is helpful in cases where one is interested in the intermediate results of an experiment. Logtables have to be specified within the ``Database`` section of the experiment configuration file. The logtables are defined similarly to the :ref:`resultfields <resultfields>` by a name for the logtable and the fields it contains. The fields are defined by a name and type. Supported types depend on the underlying database. They genereally include, but are not limited to ``VARCHAR``, ``INT``, ``NUMERIC``, ``DOUBLE``, ``LONGTEXT``, ``DATETIME``, and ``BOOLEAN``. Logtables automatically contain the ``experiment_id (INT)`` of the experiment the logtable entry belongs to, as well as a ``timestamp (DATETIME)`` of when it has been created.

The logtables are automatically created in the database and can be found with a modified name, which has the name of the main table as a prefix: ``<table_name>__<logtable_name>``. They are :ref:`filled with the information provided by the experiment function <experiment_function_logtables>`.

An example of two commonly used logtable is given below. An in-depth example showcasing the usage of logtables can be found within the :ref:`examples section <examples>`.

.. code-block:: yaml

    Database:

      logtables:

        pipeline_evaluations:
          kernel: VARCHAR(50)
          f1: DOUBLE
          accuracy: DOUBLE

        incumbents:
          pipeline: LONGTEXT
          performance: DOUBLE


---------------------
Execution Information 
---------------------

Furthermore, it is possible to define parameters for execution. They will not be part of the database but are only used when executing ``PyExperimenter``. Currently, the following parameter is supported:

- ``n_jobs: <INT>``: The maximum number of experiments that will be executed in parallel. Default is ``1``.


-------------
Custom Fields
-------------

Optionally, custom fields can be defined under the ``Custom`` section, which will be ignored when creating or filling the database, but can provide fixed parameters for the actual execution of experiments. A common example is the path to some folder in which the data is located. The values of such custom fields are passed to the experiment function.

.. code-block:: yaml

    Custom:
        datapath: path/to/data


.. _experiment_configuration_file_codecarbon:

----------
CodeCarbon
----------

Tracking information about the carbon footprint of experiments is supported via `CodeCarbon <https://mlco2.github.io/codecarbon/>`_. It is enabled by default, if you want to completely deactivate it, please check the :ref:`documentation on how to execute PyExperimenter <execution>`.

Per default, ``CodeCarbon`` will track the carbon footprint of the whole machine, including the execution of the experiment function. It measures the power consumption every 15 seconds and estimates the carbon emissions based on the region of the device. The resulting information is saved to a file in the ``output/CodeCarbon`` as well as written into its own table in the database, called ``<table_name>_codecarbon``. A description about how to access the data can be found in the :ref:`CodeCarbon explanation of the execution of PyExperimenter <execution_codecarbon>`.

``CodeCarbon`` can be configured via its own section in the experiment configuration file. The default configuration is shown below, but can be extended by any of the parameters listed in the `CodeCarbon documentation <https://mlco2.github.io/codecarbon/usage.html#configuration>`_. During the execution, the section will be automatically copied into a ``.codecarbon.config`` file in you working directory, as this is required by ``CodeCarbon``.

.. code-block:: yaml

    CodeCarbon:
      offline_mode: False
      measure_power_secs: 25
      tracking_mode: process
      log_level: error
      save_to_file: True
      output_dir: output/CodeCarbon
