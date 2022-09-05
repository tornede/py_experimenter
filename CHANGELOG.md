# Changelog


## v1.0.0 (04/09/2022)

### Feature

- Restructured the experiment configuration file.
    - Added shortcut for a longer list of integers as keyfields.
    - Added the option to have a timestep column for each resultfield.
- Added option to give a name to the `PyExperimenter` instance to improve support of parallel HPC cluster usage.
- Added multiple options to fill tables.
- Improved column order of the database table when it is created.
- Added method to reset parts of the database table based on their status.
- Added method to obtain the current state of the database table as `pandas.Dataframe`, which can be used to easily export result tables, e.g. to LaTeX.
- Improved robustness of database creation and experiment execution.
- Improved error handling.
- Updated and extended the README file according to all changes. 

### Examples

- Added a Jupyter notebook explaining the general usage of the `PyExperimenter`. 
- Added a Jupyter notebook explaining how to fill the database table with a conditional experiment grid. 

### Fix

- Added checked when resetting a table, that only missing rows are added and no duplicated rows are created.
- Fixed writing of string containing quotation marks to the database table.

### Tests

- Added tests for all key components of `PyExperimenter`.


## v0.0.6 (01/03/2022)

- No summary available.


## v0.0.5 (17/01/2022)

- No summary available.


## v0.0.4 (02/11/2021)

- No summary available.


## v0.0.3 (20/10/2021)

- No summary available.


## v0.0.2 (20/10/2021)

- No summary available.


## v0.0.1 (14/10/2021)

- First release of `PyExperimenter`
- No summary available.