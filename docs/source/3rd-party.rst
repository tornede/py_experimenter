
.. _3rd_party:

================================
Usage of 3rd Party Dependencies
================================

This part of the documentation refers to 3rd party dependencies, that need to be used actively during development. It contains a short description of the dependency and an explanation on how it is meant to be used for ``PyExperimenter``. 

.. _use_uv:

--------
uv
--------

`uv <uv_>`_ is a fast Python package and project manager. It allows to declare the dependencies of your projects and it will manage (install / update) them for you in a project-local virtual environment (``.venv``). It also allows to build a package which can be uploaded to a package repository and installed via ``pip``.

For installation instructions and further useful commands than the ones listed below, please refer to the `uv documentation <uv_docs_>`_. For example, on macOS and Linux uv can be installed via:

.. code-block::

        curl -LsSf https://astral.sh/uv/install.sh | sh

If you checked out the ``PyExperimenter`` repository, you can install the package together with its development dependencies using uv. To this end, navigate into the git project folder and execute the following command, which will create a virtual environment in ``.venv`` and install the exact versions (as given in ``uv.lock``) used for the development of ``PyExperimenter``:

.. code-block::

        uv sync

Commands can then be executed inside this environment either by prefixing them with ``uv run`` (e.g. ``uv run pytest``) or by activating the environment via ``source .venv/bin/activate``.

You can add a new core dependency that is needed to use ``PyExperimenter`` using the first of the following commands, which will add the latest version of the package to the ``pyproject.toml`` file. If you want to add a specific version, you can use the second following command:

.. code-block::

        uv add <package_name>
        # or
        uv add "<package_name>>=<version>"

Development dependencies are organized in dependency groups: ``test`` contains everything needed to run the unit tests, ``docs`` everything needed to build the documentation, and ``dev`` includes both of them plus further tools (e.g. ``jupyterlab``). ``uv sync`` installs the ``dev`` group by default. A development dependency can be added to one of these groups using the following command, which will add the latest or the given version of the package:

.. code-block::

        uv add --group <test/docs/dev> <package_name>
        # or
        uv add --group <test/docs/dev> "<package_name>>=<version>"

The ``uv.lock`` file will be updated automatically, when doing so. Therefore, ``uv`` tries to resolve the dependencies. If needed dependencies will be updated. If you want to update the ``uv.lock`` file manually (resolve dependencies with the most current library versions), you can use the following command:

.. code-block::

        uv lock --upgrade


The version of ``PyExperimenter`` can be easily updated using the following command. This will update the version in the ``pyproject.toml`` file.

.. code-block::

        uv version --bump <major/minor/patch>

Finally, if you want to build a package, you can use the following command, which will create a ``dist`` folder containing the built package:

.. code-block::

        uv build

.. _uv: https://docs.astral.sh/uv/
.. _uv_docs: https://docs.astral.sh/uv/getting-started/
