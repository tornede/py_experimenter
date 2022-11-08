
.. _contribute:

==================
How to Contribute
==================

We would appreciate seeing you contributing to the `PyExperimenter`. If you have any new idea or have found a bug, please first make sure to check the existing `GitHub Issues <github_py_experimenter_issues_>`_. In case someone else have had a similar idea or has found the same bug, you could give further feedback on how to improve. Otherwise, please :ref:`create an according issue <contribute_create_issue>`. You are planning to work on this issue yourself, or you have found another issue you would like to work on? Great! Directly create a comment stating what exactly you are planning to do and :ref:`setup the development workflow <contribute_fork_project>`.

At the end, please make sure that you also :ref:`extended the unit tests <contribute_unit_tests>` and that all unit tests are working correctly. Additionally, please :ref:`update the documentation <contribute_update_documentation>` according to your changes. At the very end, :ref:`create a pull request <contribute_pull_request>` and mention the issue on which the changes are based, which contains important information for the review.


 

.. _contribute_create_issue:

Creating an Issue
------------------

A GitHub issue should contain any information that is needed that a third person understands the problem (in case of a bug) or the vision of a new feature. To create an issue

1. Go to the `GitHub Issues <github_py_experimenter_issues_>`_.
2. Summarize the bug / vision as title of the issue. 
3. Give all neccessary information about the issue, depending on if it is a bug or an improvement.
   
Bug Report
        Give a step-by-step description of what you have done and where the bug occurs, so that it is reproducible. Please also provide the code that produced the bug. Additionally, give some assumption what you think the problem is. And add the ``bug`` label to your issue.

Improvement
        In detail describe the vision of the improvement, how it should be used and how it should work. Please also provide a code example of the usability of the new method / feature. And add the ``enhancement`` label to your issue.

Help 
        Describe the problem you are facing and provice a code example (is suitable). And add the ``help wanted`` label to your issue.



.. _contribute_fork_project:

Setup Development Workflow
---------------------------

The development workflow for the ``PyExperimenter`` is based on the fork-and-branch git workflow as described in this `blog post <fork_and_branch_workflow_>`_. The general steps are as follows:

1. Fork the GitHub repository: Log into GitHub, go to the `PyExperimenter GitHub repository <github_py_experimenter_>`_ and click on ``Fork`` button in the top right corner.
   
2. Clone your GitHub repository fork: On your local machine, go into the folder where you want to clone the repository and clone your fork using the following command, but please ensure to replace ``<username>``.
   
   .. code-block:: 

        git clone https://github.com/<username>/py_experimenter.git

3. Add ``PyExperimenter`` remote: Add the original ``PyExperimenter`` repository as additional remote.
   
   .. code-block:: 

        git remote add upstream https://github.com/tornede/py_experimenter.git

4. Create branch: Make sure that all branches are locally available and switch to the ``develop`` branch. Then create a new branch for your changes, but please ensure to replace ``<feature_branch_name>`` with some meaningful name.
   
   .. code-block:: 

        git fetch --all
        git branch -v -a
        git switch develop
        git checkout -b <feature_branch_name>

5. Create an environment for the development, e.g. using `Anaconda <anaconda_>`_.

   .. code-block:: 

        conda create -n py-experimenter-env python=3.9 
        conda activate py-experimenter-env

6. Install the development dependencies using :ref:`poetry <use_poetry>`.
   
   .. code-block::

        poetry install

7. Make sure to install `pandoc` separately in your anaconda environment `as this article suggests <pandoc_installation_>`_.

   .. code-block::

        conda install pandoc

8. Check tests: Before working on any changes, please make sure that all unit tests are working correctly. Therefore, navigate into the git project folder and execute all unit tests.
   
   .. code-block:: 

        pytest

9. In case some tests are not succeeding due to ``ValueError`` of ``numpy``, try to update that dependency manually and execute the tests again (step 8).

   .. code-block::

        pip install numpy --upgrade

10. Finally you can start working on the planned changes! At any time, you can push your changes to the ``origin`` remote.
   
   .. code-block:: 

        git push origin <feature_branch_name>


.. _use_poetry:

How to use Poetry
-----------------

`Poetry <poetry_>`_ is a dependency management and packaging tool for Python. It allows to declare the dependencies of your projects and it will manage (install / update) them for you. It also allows to build a package which can be uploaded to a package repository and installed via ``pip``. 

For installation instructions and further useful commands than the ones listed below, please refer to the `Poetry documentation <poetry_docs_>`_. Please make sure to follow the described steps: do NOT use ``pip`` or ``conda`` for installation of Poetry itself, and make sure to add Poetry to your PATH. 

If you checked out the ``PyExperimenter`` repository, you can install the development dependencies using Poetry. To this end, navigate into the git project folder and execute the following command:

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

The ``poetry.lock`` file will be updated automatically, when doing so. If you want to update the ``poetry.lock`` file manually, you can use the following command:

.. code-block::

        poetry update

Finally, if you want to build a package, you can use the following command, which will create a ``dist`` folder containing the built package:

.. code-block::

        poetry build

.. _contribute_unit_tests:

Extend Unit Tests 
------------------

To provide a good usability of the ``PyExperimenter`` it is mandatory to extend and update the unit tests for all changes. The tests are located in the ``test`` folder of the project, using the same folder structure than the actual code. Additionally, it is important to execute all unit tests to ensure no other functionality has been affected. Therefore, navigate into the git project folder and execute all unit tests.

.. code-block:: 

        pytest

All tests except one should will succeed without any adaptions. But the test for the mysql provider needs credentials to a mysql database. 

.. code-block::

        test/test_run_experiments/test_run_mysql_experiment.py

If you have a mysql database available, `create a database credential file <create_database_credential_file_>`_ with the according information and execute the tests again. This time, all tests should succeed without further adaptions.


.. _contribute_update_documentation:

Update Documentation
---------------------

The documentation of the ``PyExperimenter`` is key to all users to understand the functionality and the usability. Therefore, the documentation should be updated according to the changes. It is located in the ``docs`` folder of the project. Please check that the documentation can be built by first generating it locally. Therefore, navigate into the git project folder and execute shinx. The builded website can be found in the project folder ``output/documentation/``.

.. code-block::

        sphinx-build -b html docs/source/ output/documentation/


.. _contribute_pull_request:

Create Pull Request
--------------------

After all changes are made, including  :ref:`tests <contribute_unit_tests>` and :ref:`documentation <contribute_update_documentation>`, make sure to commit and :ref:`push <contribute_fork_project>` all your changes. 

Afterwards, go to the `PyExperimenter GitHub Pull Requests <github_py_experimenter_pulls_>`_ and create a new pull request. 

1. Make sure to select the correct source and destination repositories and according branches. The source repository is your fork, and the source branch is the ``<feature_branch_name>``. The destination repository is ``tornede/py_experimenter`` and the destination branch is ``develop``.

2. Provide a full description of the changes you did. 

3. Reference the according issue you either created or have selected at the very beginning.


.. _anaconda: https://docs.anaconda.com/anaconda/install/
.. _fork_and_branch_workflow: https://blog.scottlowe.org/2015/01/27/using-fork-branch-git-workflow/
.. _github_py_experimenter: https://github.com/tornede/py_experimenter/
.. _github_py_experimenter_issues: https://github.com/tornede/py_experimenter/issues
.. _github_py_experimenter_pulls: https://github.com/tornede/py_experimenter/pulls
.. _create_database_credential_file: https://tornede.github.io/py_experimenter/usage.html#database-credential-file
.. _pandoc_installation: https://stackoverflow.com/questions/62398231/building-docs-fails-due-to-missing-pandoc
.. _poetry: https://python-poetry.org/
.. _poetry_docs: https://python-poetry.org/docs/
