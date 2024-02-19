.. _experiment_configuration_file:

=============================
Experiment Configuration File
=============================

The experiment configuration file is primarily used to define the database backend, as well as execution parameters, i.e. keyfields, resultfields, and logtables. An example experiment configuration can be found in the following, covering the main functionality ``PyExperimenter`` provides. Each paragraph is described in the subsections below.

.. code-block:: yaml

    PY_EXPERIMENTER:
        n_jobs: 1

        Database:
            provider: sqlite
            database: py_experimenter
            table: 
                name: example_general_usage
                keyfields:
                    dataset:
                        type: VARCHAR(255)
                        values: ['iris']
                    cross_validation_splits:
                        type: INT
                        values: [5]
                    seed:
                        type: int 
                        values:
                            start: 2
                            stop: 7
                            step: 2
                    kernel:
                        type: VARCHAR(255)
                        values: ['linear', 'poly', 'rbf', 'sigmoid']
            result_timestamps: False
            resultfields:
                pipeline: LONGTEXT
                train_f1: DECIMAL
                train_accuracy: DECIMAL
                test_f1: DECIMAL
                test_accuracy: DECIMAL

        Custom:
            datapath: sample_data
        
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

The ``Database`` section defines the database and its structure. It contains the ``provider`` of the database connection (either ``sqlite`` or ``mysql``). Furthermore, the name of the ``database`` has to be given. Additionally, there is a subsection called ``table``, which contains the name of the table, the optional :ref: `keyfields <keyfields>`, and the optional :ref: `resultfields <resultfields>`.


.. note::
   In the case of ``mysql`` an additional :ref:`database credential file <database_credential_file>` has to be created.


.. _keyfields:

---------
Keyfields
---------

Experiments are identified by ``keyfields``, hence, keyfields define the execution of experiments. A keyfield can be thought of as a parameter, whose value defines an experiment together with the values of all other experiments. For example, if our experiment was to compute the exponential function for several input values, the input would be a keyfield.
.. code-block:: yaml

    keyfields:
        input_value:
            type: NUMERIC
            values: <keyfield_values>

    
For each keyfield, a type has to be defined (supported types depent on the provided database). Additionally, the values have to be defined. This can be done either with a list of values, or a range of values. The range of values can be defined by ``start``, ``stop`` and the optional ``step`` size. In the above example, this would result in 

.. code-block:: yaml

    keyfields:
        input_value:
            type: NUMERIC
            values:
                start: 1
                stop: 10
                step: 1

for ranges and

.. code-block:: yaml

    keyfields:
        input_value:
            type: NUMERIC
            values: [1, 2, 3, 4, 5, 6, 7, 8, 9]



for lists.

Note that ranges are defined by their ``start``, their ``stop``, and the optional ``step`` size. The step size is optional and defaults to ``1``. The stop is not included in the range.

.. _resultfields:

------------
Resultfields
------------

The results of the experiments will be stored in the database in the form of ``resultfields``. They are optional and are also contained in the ``tabl`` section of the experiment configuration file. The resultfields are defined in the following way:

.. code-block:: yaml

    resultfields:
        pipeline: LONGTEXT
        train_f1: DECIMAL

with the name of the resultfield, followed by its type.
Additionally, it is possible to store the timestamps at which the results have been obtained in the database. This can be done by adding the following line to the experiment configuration file (Default is ``False``).

.. code-block:: yaml

    result_timestamps: False
        resultfields:
        pipeline: LONGTEXT

.. note::

   The ``resultfields`` are optional. If they are not specified, the database will only contain the keyfields and the according experiment id.


.. _logtables:

---------
Logtables
---------

In addition to the functionality stated above, ``PyExperimenter`` also supports ``logtables`` thereby enabling the logging of information into separate tables. This is helpful in cases where one is interested in the intermediate results of an experiment, which one might regularly want to write to the database. Logtables have to be specified to the ``DATABASE`` section of the experiment configuration file. The logtables are defined similarly to the ``resultfields`` in  the following way:	

.. code-block:: yaml

    logtables:
      train_scores:
        f1: DOUBLE
        accuracy: DOUBLE
        kernel: VARCHAR(50)


Note that the name of the logtable is modified in the databse to ``<maintable_name>_<logtable_name>``.

Additionally lotgables have the following fields:

- ``experiment_id (int)``: The id of the experiment the logtable entry belongs to.
- ``timestamp (datetime)``: The timestamp the logtable entry has been created.

An in-depth example showcasing the usage of logtables can be found within the :ref:`examples section <examples>`.


---------------------
Execution Information 
---------------------

Furthermore, it is possible to define parameters for execution. They will not be part of the database but are only used to configure the PyExperimenter. Currently, the following parameters are supported:

- ``n_jobs: <int>``: The maximum number of experiments that will be executed in parallel. Default is ``1``.


-------------
Custom Fields
-------------

Optionally, custom fields can be defined under the ``CUSTOM`` section, which will be ignored when creating or filling the database, but can provide fixed parameters for the actual execution of experiments. A common example is the path to some folder in which the data is located. The values of such custom fields are passed to the experiment function.

.. code-block:: yaml

    Custom:
        datapath: sample_data


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
