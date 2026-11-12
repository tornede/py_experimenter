.. _release_version:

==================
Release Version
==================


.. _contribute_release_preparepypi:

-------------------------
Prepare Test PyPi / PyPi
-------------------------

1. Get your access tokens from `Test PyPi <testpypi_token_>`_ and `PyPi <pypi_token_>`_, respectively.

2. Provide the token to ``uv publish``, either via the ``--token`` argument or via the ``UV_PUBLISH_TOKEN`` environment variable. Make sure to use the token matching the index you publish to.

  .. code-block::

    export UV_PUBLISH_TOKEN=pypi-XXXXX...


.. _contribute_release_testpypi:

-----------------------------
Release Version to Test PyPi
-----------------------------

First, check whether the project is ready for publication on `Test PyPi <testpypi_>`_.

1. Update version, build the project, and publish the project at Test PyPi.

  .. code-block::

    uv version --bump patch --bump alpha
    uv build
    uv publish --publish-url https://test.pypi.org/legacy/ --token <TEST_PYPI_TOKEN>
    
2. Create a new, empty virtual environment outside of the repository and install ``PyExperimenter`` from Test PyPi.

  .. code-block::

    uv venv pyexperimenter-release --python 3.10
    source pyexperimenter-release/bin/activate
    uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --index-strategy unsafe-best-match py-experimenter==<VERSION>

3. Execute all example notebooks and check the outputs based on the new environment ``pyexperimenter-release``. If anything does not work, fix it and repeat the steps above.


.. _contribute_release_pypi:

-----------------------------
Release Version to PyPi
-----------------------------

.. warning::
   Check the publication on `Test PyPi <contribute_release_testpypi_>`_ before publishing to `PyPi <contribute_release_pypi_>`_!


1. Update version and `add according CHANGELOG information <github_changelog_>`_.

  .. code-block::

    uv version --bump <major/minor/patch>

2. Create a pull request from ``develop`` to ``main`` and merge it (not squash merge).

3. Create a tag with the according version number for that merge commit.

4. Create a new release for that tag with the version number as title and the latest changelog additions as content. With pressing the button ``Publish release`` the requested files will be attached automatically.

5. Build the project and publish the project at PyPi.

  .. code-block::

    uv build
    uv publish --token <PYPI_TOKEN>

6. Check `PyPi version <pypi_pyexperimenter_>`_. 
   

.. _testpypi: https://test.pypi.org/
.. _testpypi_token: https://test.pypi.org/manage/account/token/
.. _pypi: https://pypi.org/
.. _pypi_token: https://pypi.org/manage/account/token/
.. _pypi_pyexperimenter: https://pypi.org/project/py-experimenter/
.. _github_changelog: https://github.com/tornede/py_experimenter/blob/main/CHANGELOG.rst
