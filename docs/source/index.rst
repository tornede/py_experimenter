.. image:: _static/py-experimenter-logo.png
   :width: 200px
   :alt: PyExperimenter
   :align: right

==========================================
Welcome to PyExperimenter's documentation!
==========================================

``PyExperimenter`` is a tool to facilitate the setup, documentation, execution, and subsequent evaluation of results from an empirical study of algorithms and in particular is designed to reduce the involved manual effort significantly.
It is intended to be used by researchers in the field of artificial intelligence, but is not limited to those.

The empirical analysis of algorithms is often accompanied by the execution of algorithms for different inputs and variants of the algorithms (specified via parameters) and the measurement of non-functional properties.
Since the individual evaluations are usually independent, the evaluation can be performed in a distributed manner on an HPC system.
However, setting up, documenting, and evaluating the results of such a study is often file-based.
Usually, this requires extensive manual work to create configuration files for the inputs or to read and aggregate measured results from a report file.
In addition, monitoring and restarting individual executions is tedious and time-consuming.

These challenges are addressed by ``PyExperimenter`` by means of a single well defined configuration file and a central database for managing massively parallel evaluations, as well as collecting and aggregating their results.
Thereby, ``PyExperimenter`` alleviates the aforementioned overhead and allows experiment executions to be defined and monitored with ease.

.. note::
   After :ref:`installation <installation>` the easiest way to start is to dive into ``PyExperimenter`` with one of our :ref:`examples <examples>`.

.. toctree::
   :maxdepth: 4
   :hidden:
   :caption: Documentation

   installation
   usage/index
   examples/index
   autoapi/index
   how-to-contribute
   help

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: About PyExperimenter
   
   authors
   license
   changelog
   Repository <https://github.com/tornede/py_experimenter/>

----------------
Acknowledgements
----------------

This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).
