---
title: 'PyExperimenter: Easily distribute experiments and track results'
tags:
  - Python
authors:
  - name: Tanja Tornede
    orcid: 0000-0001-9954-462X
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: 1
  - name: Alexander Tornede
    orcid: 0000-0002-2415-2186
    affiliation: 1
  - name: Lukas Fehring
    orcid: 0000-0001-8057-4650
    affiliation: 1
  - name: Lukas Gehring
    affiliation: 1
  - name: Helena Graf
    orcid: 0000-0001-9447-0609
    affiliation: 1
  - name: Jonas Hanselle
    orcid: 0000-0002-1231-4985
    affiliation: 1
  - name: Marcel Wever
    orcid: 0000-0001-9782-6818
    affiliation: 2
  - name: Felix Mohr 
    orcid: 0000-0002-9293-2424
    affiliation: 3
affiliations:
 - name: Department of Computer Science, Paderborn University, Germany
   index: 1
 - name: MCML, Institut for Informatics, LMU Munich, Germany
   index: 2
 - name: Universidad de La Sabana, Chia, Cundinamarca, Colombia
   index: 3
date: 19 Oktober 2022
bibliography: paper.bib

---

# Summary

Executing parameterized experiments, e.g. for machine learning (ML), and capturing their results is a task that should be well prepared.
Thereby, any overhead should be avoided, i.e., having to create multiple configuration files to run an experiment with different seeds, or having to extract information from a log file.
The `PyExperimenter` is a tool for the automatic execution of experiments, e.g. for machine learning (ML), capturing corresponding results in a unified manner in a database. 
The experiments to be executed are defined in advance. All information about an experiment are stored in the database, starting with the configuration, followed by a continously updated status, and closed by the results of the experiment. This allows a parallelization of the execution of experiments, only limited by the number of possible parallel open database connections.


![General schema of `PyExperimenter`.](usage.png)

A general schema of the `PyExperimenter` can be found in Figure 1. The `PyExperimenter` is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing the results of the experiment based on these input parameters. The set of experiments to be executed can be defined through a configuration file listing the domains of each experiment parameter, or manually through code. Those experiment parameters define the experiment grid, based on which the `PyExperimenter` setups the experiment table in the database featuring all experiments identified by their input parameter values and additional information such as the execution status. Once this table has been created, `PyExperimenter` can be run on any machine, including a distributed cluster. Each `PyExperimenter` instance automatically pulls open experiments from the database, executes the experiment function provided by the user with the corresponding experiment parameters defining the experiment and writes back the experiment results computed by the function. Possible errors arising during the execution are logged in the database. In case of failed experiments or other circumstances, a subset of the experiments can be easily reset and executed again. After all experiments are done, the experiment evaluation table can be easily extracted, e.g. averaging over different seeds.


# Related Work

`PyExperimenter` is a Python package supporting easy execution of multiple experiments differing only in their parametrizations. `PyExperimenter` was designed to be used by machine learning researchers and according students, but is not limited to those. The general structure of the project allows using `PyExperimenter` also for other types of experiments, as long as the execution requires the same code parameterized in a different way.  

Compared to other solutions [@mlflow; @wandb], `PyExperimenter` is very lightweight and has only a handful of dependencies. Furthermore it is designed to support simple but effective configurations.

## Statement of Need? 

In comparison to existing experiment-tracking tools, the core features of PyEperimenter are

- full control over the results database
- customizable creation of experiments based on parameters
- experiment runners pulling experiments from the database

Allowing users to have full control over the database in which the results are stored lets them modify the results storage to their specific use-case, which might not fit into the standard stencil of results storage and retrieval of other tools, which are often optimized regarding ease-of-use with incremental, e.g. neural models at the cost of flexibility. At the same time, desired results tables and fields are created by the tool, which, together with the experiment creation and retrieval methods, offers an advantage over a completely manual database administration. [NO NEED TO LEARN QUERY LANGUAGE; JUST USE DB]

[WHICH TOOLS ALLOW FULL CONTROL OF DB]
[THESE OTHER TOOLS DO NOT OFFER THE FOLLOWING INVERTED CONCEPT OF EXPERIMENT CREATION]

[INVERTED FLOW]

In some capacity, there are tools like [WANDB] which offer this inverted setup, although in a limited way. With [WANDB], sweeps that evaluate a number of different configurations as specified by [SPECIFICATION] can be carried out. However, there are only two search methods: grid search and bayesian optimization, and the number of agents carrying out evaluations for the sweep is also limited to 20 as of now.

[OTHER TOOLS ALLOWING INVERTED FLOWS?]

[LIGHT-WEIGHTEDNESS OF PYEXPERIMENTER]

# Acknowledgements

This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).


# References
