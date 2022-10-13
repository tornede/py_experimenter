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
    affiliation: 1
  - name: Lukas Gehring
    affiliation: 1
  - name: Helena Graf
    affiliation: 1
  - name: Jonas Hanselle
    affiliation: 1
  - name: Marcel Wever
    affiliation: 2
  - name: Felix Mohr
    affiliation: 3
affiliations:
 - name: Department of Computer Science, Paderborn University, Germany
   index: 1
 - name: Institut of Informatics, University of Munich, Germany
   index: 2
 - name: Universidad de La Sabana, Chia, Cundinamarca, Colombia
   index: 3
date: 13 Oktober 2022
bibliography: paper.bib

---

# Summary

The `PyExperimenter` is a tool for the automatic execution of experiments, e.g. for machine learning (ML), capturing corresponding results in a unified manner in a database. It is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing the results of the experiment based on these input parameters. The set of experiments to be executed can be defined through a configuration file listing the domains of each experiment parameter, or manually through code. Those experiment parameters define the experiment grid, based on which the `PyExperimenter` setups the experiment table in the database featuring all experiments identified by their input parameter values and additional information such as the execution status. Once this table has been created, `PyExperimenter` can be run on any machine, including a distributed cluster. Each `PyExperimenter` instance automatically pulls open experiments from the database, executes the experiment function provided by the user with the corresponding experiment parameters defining the experiment and writes back the experiment results computed by the function. Possible errors arising during the execution are logged in the database. In case of failed experiments or other circumstances, a subset of the experiments can be easily reset and executed again. After all experiments are done, the experiment evaluation table can be easily extracted, e.g. averaging over different seeds. A general schema of the `PyExperimenter` can be found in Figure 1.

![General schema of `PyExperimenter`.](usage.png)


# Related Work

`PyExperimenter` is a Python package supporting easy execution of multiple experiments differing only in their parametrizations. `PyExperimenter` was designed to be used by machine learning researchers and according students, but is not limited to those. The general structure of the project allows using `PyExperimenter` also for other types of experiments, as long as the execution requires the same code parameterized in a different way.  

Compared to other solutions [@mlflow; @wandb], `PyExperimenter` is very lightweight and has only a handful of dependencies. Furthermore it is designed to support simple but effective configurations.


# Acknowledgements

This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).


# References
