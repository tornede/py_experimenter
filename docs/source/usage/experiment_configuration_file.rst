.. _experiment_configuration_file:

=============================
Experiment Configuration File
=============================

The experiment configuration file is primarily used to define the database backend, as well as execution parameters, i.e. keyfields, resultfields, and logtables. An example experiment configuration can be found in the following, covering the main functionality ``PyExperimenter`` provides. Each paragraph is described in the subsections below.

.. code-block:: 

    [PY_EXPERIMENTER]
    provider = sqlite 
    database = database_name
    table = table_name 

    keyfields = dataset, cross_validation_splits:int, seed:int, kernel
    dataset = iris
    cross_validation_splits = 5
    seed = 2:10:2 
    kernel = linear, poly, rbf, sigmoid

    resultfields = pipeline:LONGTEXT, train_f1:DECIMAL, train_accuracy:DECIMAL, test_f1:DECIMAL, test_accuracy:DECIMAL
    resultfields.timestamps = false

    logtables = new_best_performance:INT, epochs:LogEpochs
    LogEpochs = runtime:FLOAT, performance:FLOAT

    n_jobs = 5 

    [CUSTOM] 
    path = sample_data

    [codecarbon]
    offline_mode = False
    measure_power_secs = 15
    tracking_mode = machine
    log_level = error
    save_to_file = True
    output_dir = output/CodeCarbon

--------------------
Database Information
--------------------

The database information have to be defined in the experiment configuration file. It contains the ``provider`` of the database connection (either ``sqlite`` or ``mysql``). Furthermore, the name of the ``database`` has to be given, together with the name of the ``table`` to write the experiment information into.


.. note::
   In case of ``mysql`` an additional :ref:`database credential file <database_credential_file>` has to be created.


.. _keyfields:

---------
Keyfields
---------

Experiments are identified by ``keyfields``, hence, keyfields define the execution of experiments. A keyfield can be thought of as a parameter, whose value defines an experiment together with the values of all other experiments. For example, if our experiment was to compute the exponential function for several input values, the input would be a keyfield. They have to be specified in the experiment configuration file by adding a line containing a comma separated list of ``keyfield_name``. Furthermore, each keyfield can be further annotated by a ``keyfield_datatype``, which is specified by adding a standard datatype to the according field. If no datatype is explicitly specified, ``VARCHAR(255)`` is used.

.. code-block:: 

    keyfields = <keyfield_name>[:<keyfield_datatype>], ...
    
For each keyfield, an additional entry starting with the same ``keyfield_name`` has to be added to the experiment configuration file, which defines the domain, i.e., possible values, of the keyfield. Usually this is done with a comma separated list of strings or numbers. In the example below, the key field ``kernel`` can be any of the four given values: ``linear``, ``poly``, ``rbf``, or ``sigmoid``. Note that strings are neither allowed to contain any quotation marks nor whitespace. Alternatively, this can be :ref:`defined via code <fill_table_with_rows>`.

As the manual definition can be a tedious task, especially for a list of integers, there is the option to define the start and the end of the list, together with the step size in the form: ``start:end:stepsize``. In the example below, ``seed`` is meant to be ``2, 4, 6, 8, 10``, but instead of the explicit list ``2:10:2`` is given.

.. code-block:: 

    keyfields = dataset, cross_validation_splits:int, seed:int, kernel
    dataset = iris
    cross_validation_splits = 5
    seed = 2:10:2 
    kernel = linear, poly, rbf, sigmoid


.. _resultfields:

------------
Resultfields
------------

The results of the experiments will be stored in the database in the form of ``resultfields``. They are optional and can be be specified in the experiment configuration file by adding a line containing a comma separated list of ``resultfield_name`` and according ``resultfield_datatype``. The datatype can be defined as explained above for :ref:`keyfields <keyfields>`, and if no datatype is explicitly specified, ``VARCHAR(255)`` is used. Note that in case some resultfield should contain arbitrarily long strings, ``LONGTEXT`` should be used as datatype.

.. code-block:: 

    resultfields = <resultfield_name>[:<resultfield_datatype>], ...

Additionally, it is possible to store the timestamps at which the results have been obtatined in the database. This can be done by adding the following line to the experiment configuration file (Default is ``False``).

.. code-block:: 

    resultfields.timestamps = True

.. note::

   The ``resultfields`` are optional. If they are not specified, the database will only contain the keyfields and the according experiment id.


.. _logtables:

---------
Logtables
---------

In addition to the functionality stated above, ``PyExperimenter`` also supports ``logtables`` thereby enabling the logging of information into separate tables. This is helpful in cases where one is intereted in intermediate results of an experiment, which one might regularily want to write to the databse. Logtables have to be specified in the experiment configuration file by adding a line containing a comma separated list of ``logtable_name`` and according ``logtable_datatype``. Note that the tables in the database are prefixed with the experiment table name, i.e., they are called ``<table_name>__<logtable_name>``.

.. code-block:: 

    logtables = <logtable_name>:<logtable_datatype>, ...
    
If the logtable should contain only a single column, you can directly use a standard datatype, like ``INT`` in this example.

.. code-block:: 

    logtables = new_best_performance:INT, ...

If a logtable should contain more than one field, you can define custom ``logtable_datatype`` by listing the field names and the corresponding datatypes in the same format as :ref:`keyfields <keyfields>`. In the example below, the logtable would be called ``epochs`` and has the datatype ``LogEpochs``, which is define in the line below. It features two fields with the names ``runtime``, and ``performance``, having the corresponding column types ``FLOAT``, and ``FLOAT``. 

.. code-block:: 

    logtables = epochs:LogEpochs, ...
    LogEpochs = runtime:FLOAT, performance:FLOAT

Note that every logtable, however it is defined, additionally has the following fields:

- ``experiment_id (int)``: The id of the experiment the logtable entry belongs to.
- ``timestamp (datetime)``: The timestamp the logtable entry has been created.

An in-depth example showcasing the usage of logtables can be found within the :ref:`examples section <examples>`.


---------------------
Execution Information 
---------------------

Furthermore it is possible to define parameters for execution. They will not be part of the database, but are only used to configure the PyExperimenter. Currently, the following parameters are supported:

- ``n_jobs (int)``: The maximum number of experiments that will be executed in parallel. Default is ``1``.


-------------
Custom Fields
-------------

Optionally, custom fields can be defined under the ``CUSTOM`` section, which will be ignored when creating or filling the database, but can provide fixed parameters for the actual execution of experiments. A common example is the path to some folder in which the data is located. The values of such custom fields are passed to the experiment function.

.. code-block:: 

    [CUSTOM] 
    path = sample_data


.. _experiment_configuration_file_codecarbon:

----------
CodeCarbon
----------

Tracking information about the carbon footprint of experiments is supported via `CodeCarbon <https://mlco2.github.io/codecarbon/>`_. It is enabled by default, if you want to completely deactivate it, please check the :ref:`documentation on how to execute PyExperimenter <execution>`.

Per default, ``CodeCarbon`` will track the carbon footprint of the whole machine, including the execution of the experiment function. It measures the power consumption every 15 seconds and estimates the carbon emissions based on the region of the device. The resulting information is saved to a file in the ``output/CodeCarbon`` as well as written into its own table in the database, called ``<table_name>_codecarbon``. A description about how to access the data can be found in the :ref:`CodeCarbon explanation of the execution of PyExperimenter <execution_codecarbon>`.

``CodeCarbon`` can be configured via its own section in the experiment configuration file. The default configuration is shown below, but can be extended by any of the parameters listed in the `CodeCarbon documentation <https://mlco2.github.io/codecarbon/usage.html#configuration>`_. During the execution, the section will be automatically copied into a ``.codecarbon.config`` file in you working directory, as this is required by ``CodeCarbon``.

.. code-block:: 

    [codecarbon]
    measure_power_secs = 15
    tracking_mode = machine
    log_level = error
    save_to_file = True
    output_dir = output/CodeCarbon
    offline_mode = False
