.. PyExperimenter documentation master file, created by
   sphinx-quickstart on Tue Oct 18 11:04:17 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/py-experimenter-logo.png
   :width: 200px
   :alt: PyExperimenter
   :align: right

Welcome to PyExperimenter's documentation!
==========================================

The `PyExperimenter` is a tool for the automatic execution of experiments, e.g. for machine learning (ML), capturing corresponding results in a unified manner in a database. It is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing the results of the experiment based on these input parameters. The set of experiments to be executed can be defined through a configuration file listing the domains of each experiment parameter, or manually through code. Based on the set of experiments defined by the user, `PyExperimenter` creates a table in the database featuring all experiments identified by their input parameter values and additional information such as the execution status. Once this table has been created, `PyExperimenter` can be run on any machine, including a distributed cluster. Each `PyExperimenter` instance automatically pulls open experiments from the database, executes the experiment function provided by the user with the corresponding experiment parameters defining the experiment and writes back the results computed by the function. Possible errors arising during the execution are logged in the database. After all experiments are done, the experiment evaluation table can be easily extracted, e.g. averaging over different seeds.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage/installation


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Acknowledgements
================
This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).
