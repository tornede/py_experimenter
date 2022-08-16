---
title: 'PyExperimenter: easily execute experiments and track results'
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
date: 16 August 2022
bibliography: paper.bib

---

# Summary

The `PyExperimenter` is a tool for the automatic execution of, e.g. machine learning (ML) experiments and capturing corresponding results in a unified manner in a database. It supports both sqlite or mysql backends. The experiments to conduct can be defined via a configuration file or in custom way through code. Based on that, a table with initial properties, e.g. different seeds for an ML algorithm, is filled. During execution, a custom defined function requested to compute the results for a single row of the table. Those results, e.g. performances, can be added to the table at the end of the execution. Errors occurring during the execution are logged in the database. Afterwards, experiment evaluation tables can be easily extracted, e.g. averaging over different seeds. 

`PyExperimenter` is designed to be parallelized. The level of parallelization is defined by the overall number of available threads divided by the parallelization of the custom function. In case of no parallelization of the custom function, the number of available threads decided the maximal possible parallelization.


# Statement of Need

`PyExperimenter` is a Python package supporting easy execution of multiple experiments differing only in their parametrizations. `PyExperimenter` was designed to be used by machine learning researchers and according students, but is not limited to those. The general structure of the project allows using `PyExperimenter` also for other types of experiments, as long as the execution requires the same code parameterized in a different way.  

Compared to other solutions [@mlflow; @wandb], `PyExperimenter` is very lightweight and has only a handful of dependencies. Furthermore it is designed to support simple but effective configurations. 


# Example Usage
ToDo

# Acknowledgements

This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).


# References
