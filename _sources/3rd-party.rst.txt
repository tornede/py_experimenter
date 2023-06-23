
.. _3rd_party:

================================
Usage of 3rd Party Dependencies
================================

This part of the documentation refers to 3rd party dependencies, that need to be used actively during development. It contains a short description of the dependency and an explanation on how it is meant to be used for ``PyExperimenter``. 

.. _use_poetry:

--------
Poetry
--------

`Poetry <poetry_>`_ is a dependency management and packaging tool for Python. It allows to declare the dependencies of your projects and it will manage (install / update) them for you. It also allows to build a package which can be uploaded to a package repository and installed via ``pip``. 

For installation instructions and further useful commands than the ones listed below, please refer to the `Poetry documentation <poetry_docs_>`_. Please make sure to follow the described steps: do NOT use ``pip`` or ``conda`` for installation of Poetry itself, and make sure to add Poetry to your PATH. 

If you checked out the ``PyExperimenter`` repository, you can install the development dependencies using Poetry. To this end, navigate into the git project folder and execute the following command which will instll the excact versions used for the development of ``PyExperimenter``:

.. code-block::

        poetry install

You can add a new core dependency that is needed to use ``PyExperimenter`` using the first of the following commands, which will add the latest version of the package to the ``pyproject.toml`` file. If you want to add a specific version, you can use the second following command:

.. code-block::

        poetry add <package_name>
        # or
        poetry add "<package_name>>=<version>"

A development dependency can be added using the following command, which will add the latest or the given version of the package to the ``dev`` dependency group:

.. code-block::

        poetry add --group dev <package_name>
        # or
        poetry add --group dev "<package_name>>=<version>"

The ``poetry.lock`` file will be updated automatically, when doing so. Therefore, ``poetry`` tries to resolve the dependencies. If needed dependencies will be updated. If you want to update the ``poetry.lock`` file manually (resolve dependencies with the most current libary version), you can use the following command:

.. code-block::

        poetry update


The version of ``PyExperimenter`` can be easily updated using the following command. This will update the version in the ``pyproject.toml`` file.

.. code-block::
        
        poetry version <major/minor/patch/prerelease>

Finally, if you want to build a package, you can use the following command, which will create a ``dist`` folder containing the built package:

.. code-block::

        poetry build

.. _poetry: https://python-poetry.org/
.. _poetry_docs: https://python-poetry.org/docs/
