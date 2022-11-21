=========
Changelog
=========

v1.1.0 (21/11/2022)
===================

Feature
-------

- Improve Documentation
    - Added documentation using Sphinx, therefore a workflow was created to build and push the website.
    - The build documentation will be pushed to a separate branch ``gh-pages``.
    - The API of the class PyExperimenter has been updated to be accessible via documentation.
    - Updated README to refer to the documentation.
- Converted project to pyproject.toml using Poetry
    - Created pyproject.toml via Poetry.
    - Added all dependencies for PyExperimenter itself as well as for the development.
- Updated Experiment Handling
    - The experiment configuration field ``cpu.max`` was renamed to ``n_jobs``. 
    - ``PyExperimenter.execute()`` now spawns as many workers as defined by ``j_jobs``.
    - The open experiment will not be pulled once in advance, but within each call of the ``PyExperimenter._execution_wrapper()``. This is completely handled by the ``SELECT`` call, including the ``randomize`` (if given), and limits the results to ``1``. In the same transaction of pulling an open experiment, its status is set to ``running``. 
    - An open experiment is only pulled if ``max_experiments`` has not been reached (except for ``-1``).
- File holding all exceptions was renamed.
- Modified functionality to reset experiments
    - Added Enum ``ExperimentStatus``.
    - Modified ``experimenter.reset_experiments()`` to be able to get
        - single ``ExperimentStatus`` 
        - list of ``ExperimentStatus`` 
        - ``"all"`` to reset all ``ExperimentStatus`` 
    - Added method ``experimenter.delete_table()``.
- Finalized paper draft

Examples
--------
- Updated due to latest changes and renamings
- Referenced documentation within examples

Fix
---

- Bugfix of wrong column order when writing to DB
- Unfavorable pulling experiments has been changed (see above)


Tests
-----

- Add workflow to automatically check tests
    - Adds a simple test runner using GitHub Actions. 
    - Uses poetry to install the package and locked dependencies.
    - Caching the virtual environment. This prevents having to install it every time and cuts down on CI roundtrip times.
    - It tests a matrix of various python versions (3.7, 3.8, 3.9) and OS versions (Ubuntu, MacOS, Windows). Python 3.10 is excluded for now, since installing some of the dependencies takes a very long time.


v1.0.0 (04/09/2022)
===================

Feature
-------

- Restructured the experiment configuration file.
    - Added shortcut for a longer list of integers as keyfields.
    - Added the option to have a timestep column for each resultfield.
- Added option to give a name to the ``PyExperimenter`` instance to improve support of parallel HPC cluster usage.
- Added multiple options to fill tables.
- Improved column order of the database table when it is created.
- Added method to reset parts of the database table based on their status.
- Added method to obtain the current state of the database table as ``pandas.Dataframe``, which can be used to easily export result tables, e.g. to LaTeX.
- Improved robustness of database creation and experiment execution.
- Improved error handling.
- Updated and extended the README file according to all changes. 

Examples
--------

- Added a Jupyter notebook explaining the general usage of the ``PyExperimenter``. 
- Added a Jupyter notebook explaining how to fill the database table with a conditional experiment grid. 

Fix
---

- Added checked when resetting a table, that only missing rows are added and no duplicated rows are created.
- Fixed writing of string containing quotation marks to the database table.

Tests
-----
- Added tests for all key components of ``PyExperimenter``.


v0.0.6 (01/03/2022)
===================

- No summary available.


v0.0.5 (17/01/2022)
===================

- No summary available.


v0.0.4 (02/11/2021)
===================

- No summary available.


v0.0.3 (20/10/2021)
===================
- No summary available.


v0.0.2 (20/10/2021)
===================
- No summary available.


v0.0.1 (14/10/2021)
===================

- First release of ``PyExperimenter``
- No summary available.
