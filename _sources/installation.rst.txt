.. _installation:

=================
Installation
=================

The ``PyExperimenter`` package requires Python 3.10 or newer and can be easily installed via PyPI: 

.. code-block:: 

        pip install py-experimenter

Thereby, the following dependencies are automatically installed:

.. literalinclude:: ../../pyproject.toml
    :language: toml
    :start-at: dependencies = [
    :end-at: ]

.. note::
    To run the :ref:`example notebooks <examples>`, a Jupyter environment is required, which is not installed automatically. It can be installed e.g. via ``pip install jupyterlab``.
