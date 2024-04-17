.. _distributed_execution:

=====================
Distributed Execution
=====================
To distribute the execution of experiments across multiple machines, you can follow the standard :ref:`procedure of using PyExperimenter <execution>`, with the following additional considerations.

--------------
Database Setup
--------------
You need to have a shared database that is accessible to all the machines and supports concurrent access. Thus, ``SQLite`` is not a good choice for this purpose, which is why we recommend using a ``MySQL`` database instead.

--------
Workflow
--------
While it is theoretically possible for multiple jobs to create new experiments, this introduces the possibility of creating the same experiment multiple times. To prevent this, we recommend the following workflow, where a process is either the ``database handler``, i.e. responsible to create/reset experiment, or a  ``experiment executer`` actually executing experiments. 

.. note:: 
    Make sure to use the same :ref:`experiment configuration file <experiment_configuration_file>`, and :ref:`database credential file <database_credential_file>` for both types. 


Database Handling
-----------------

The ``database handler`` process creates/resets the experiments and stores them in the database once in advance.

.. code-block:: python

    from py_experimenter.experimenter import PyExperimenter

    experimenter = PyExperimenter(
        experiment_configuration_file_path = "path/to/file",
        database_credential_file_path = "path/to/file"
    )
    experimenter.fill_table_from_config()


Experiment Execution
--------------------

Multiple ``experiment executer`` processes execute the experiments in parallel on different machines, all using the same code. In a typical HPC context, each job starts a single ``experiment executer`` process on a different node.

.. code-block:: python
    
    from py_experimenter.experimenter import PyExperimenter

    experimenter.execute(experiment_function, max_experiments=1)
