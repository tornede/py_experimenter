.. _release_version:

==================
Release Version
==================


.. _contribute_release_preparepypi:

-------------------------
Prepare Test PyPi / PyPi
-------------------------

1. Add repositories to poetry config.

  .. code-block::
    
    poetry config repositories.test-pypi https://test.pypi.org/legacy/
    # pypi is already known by poetry by default

2. Get your access tokens from `Test PyPi <testpypi_token_>`_ and `PyPi <pypi_token_>`_, respectively.

3. Store tokens using poetry config.

  .. code-block::

    poetry config pypi-token.test-pypi pypi-XXXXX...
    poetry config pypi-token.pypi pypi-XXXXX...


.. _contribute_release_testpypi:

-----------------------------
Release Version to Test PyPi
-----------------------------

First, check whether the project is ready for publication on `Test PyPi <testpypi_>`_.

1. Update version, build the project, and publish the project at Test PyPi.

  .. code-block::

    poetry version prerelease
    poetry build
    poetry publish -r test-pypi
    
2. Create a new conda environment and install ``PyExperimenter`` from Test PyPi.

  .. code-block::

    conda create -n pyexperimenter-release python=3.9
    conda activate pyexperimenter-release
    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple py-experimenter==<VERSION>

3. Execute all example notebooks and check the outputs based on the new environment ``pyexperimenter-release``. If anything does not work, fix it and repeat the steps above.


.. _contribute_release_pypi:

-----------------------------
Release Version to PyPi
-----------------------------

.. warning::
   Check the publication on `Test PyPi <contribute_release_testpypi_>`_ before publishing to `PyPi <contribute_release_pypi_>`_!


1. Update version and `add according CHANGELOG information <github_changelog_>`_.

  .. code-block::

    poetry version <major/minor/patch>

2. Create a pull request from ``develop`` to ``main`` and merge it (not squash merge).

3. Create a tag with the according version number for that merge commit.

4. Create a new release for that tag with the version number as title and the latest changelog additions as content. With pressing the button ``Publish release`` the requested files will be attached automatically.

5. Build the project and publish the project at PyPi.

  .. code-block::

    poetry build
    poetry publish

6. Check `PyPi version <pypi_pyexperimenter_>`_. 
   

.. _testpypi: https://test.pypi.org/
.. _testpypi_token: https://test.pypi.org/manage/account/token/
.. _pypi: https://pypi.org/
.. _pypi_token: https://pypi.org/manage/account/token/
.. _pypi_pyexperimenter: https://pypi.org/project/py-experimenter/
.. _github_changelog: https://github.com/tornede/py_experimenter/blob/main/CHANGELOG.rst
