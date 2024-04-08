.. _distributed_execution:

=====================
Distributed Execution
=====================
To distribute the execution of experiments across multiple machines, you can follow the standard :ref:`precedure of using the py-experimenter <execution>`, with the following additional steps:

--------------
Database Setup
--------------
To distribute the execution of experiments, you need to have a shared database that is accessible to all the machines and supports concurrent access. It follows that ``sqlite`` is not a good choice for this purpose. We recommend using a ``MySQL`` database.

--------
Workflow
--------
While it is theoretically possible for multiple jobs to create new experiments, this introduces the possibility of creating the same experiment multiple times. To avoid this, we recommend the following workflow, where a process is either the ``master``, or a  ``worker`` process:

- The ``master`` creates the experiments and stores them in the database.

.. code-block:: python

    from py_experimenter.experimenter import PyExperimenter
    experimenter = PyExperimenter(
        experiment_configuration_file_path = "path/to/file",
        database_credential_file_path = "path/to/file"
    )
    experiemnter.fill_table_from_config()

- Multiple ``workers`` execute the experiments in parallel.

.. code-block:: python
    
    from py_experimenter.experimenter import PyExperimenter
    experimenter.execute(experiment_function, max_experiments=1)

For this workflow to work, both the master and worker processes need to be based on the same
:ref:`configuration file <experiment_configuration_file>`, and :ref:`database credential file <database_credential_file>`. 