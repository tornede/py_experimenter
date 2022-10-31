---
title: 'PyExperimenter: Easily distribute experiments and track results'
tags:
  - Python
  - Experiments
  - Executor
  - Database
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
date: 31 Oktober 2022
bibliography: paper.bib

---

# Summary

Executing parameterized experiments, e.g. for machine learning (ML), and capturing their results is a tedious task without proper tool support.
In particular, one is often confronted with considerable overhead, i.e., having to create multiple configuration files to run an experiment with different seeds, or having to extract information from a log file to analyze the results.
The `PyExperimenter` is a tool for the automatic execution of a set of experiments, e.g. for machine learning (ML), well defined via a single configuration file and for capturing corresponding results in a unified manner in a database.
Thereby the `PyExperimenter` alleviates the aforementioned overhead and allows for easy to define and monitor experiment executions. To this end, both the status and the results of each experiment is bookkeeped in a joint database allowing to coordinate a massively parallel execution.

![General schema of `PyExperimenter`.](usage.png)

A general schema of the `PyExperimenter` can be found in Figure 1. The `PyExperimenter` is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing the results of the experiment based on these input parameters. The set of experiments to be executed can be defined through a configuration file listing the domains of each experiment parameter, or manually through code. Those experiment parameters define the experiment grid, based on which the `PyExperimenter` setups the experiment table in the database featuring all experiments with their input parameter values and additional information such as the execution status. Once this table has been created, `PyExperimenter` can be run on any machine, including a distributed cluster. Each `PyExperimenter` instance automatically pulls open experiments from the database, executes the experiment function provided by the user with the corresponding experiment parameters defining the experiment and writes back the experiment results computed by the function. Possible errors arising during the execution are logged in the database. In case of failed experiments or other circumstances, a subset of the experiments can be reset easily and executed again. After all experiments are done, all results can be jointly exported as a Pandas Dataframe [@pandas] for further processing, such as generating a LaTex table averaging over different seeds.

## Statement of Need

There are already many experiment tracking tools available, especially for machine learning, like Weights and Biases [@wandb], MLFlow [@mlflow], TensorBoard [@tensorboard], Aim [@aim], Comet.ML [@comet], Data Version Control [@dvc], Sacred [@sacred], Guild.AI [@guildai] and neptune.ai [@neptune]. These tools largely assume that users define the configuration of an experiment together with the experiment run itself. In case of the evaluation of different hyperparameter configurations, this process is suboptimal, since it requires to communicate the hyperparameters through scripts. This task can become cumbersome to manage as the number of configuration options and desired combinations grows and becomes more complex. Weights and Biases [@wandb], Polyaxon [@polyaxon], and Comet.ML [@comet] allow so-called sweeps, i.e., hyperparameter optimizations, albeit in a limited way. For a sweep, usually hyperparameters that should be optimized are specified along with the desired search domains, and an optimizer can be selected from a pre-defined list to carry out the optimization. However, the implementation of this functionality usually imposes several restrictions on the way the sweep can be carried out.

In contrast, the `PyExperimenter` follows an inverted workflow. Instead of experiment runners registering experiments to a tracking entity such as a tracking server or database, the experiments are predefined and runners are pulling open experiments from a database. Similarly, ClearML [@clearml] and Polyaxon [@polyaxon] support a workflow where experiments are first enqueued in a central orchestration server and agents can then pull tasks from the queue to execute in a more universal way. However, both are much more heavyweight than the `PyExperimenter`, regarding the implementation of both the agents and backend-features, and are further neither completely open-source nor free.

In addition to the inverted workflow, a core property of the `PyExperimenter` is that the user has direct access to the experiment database, which is not usually the case for alternative tools. This allows users to view, analyze and modify both the experiment inputs and results directly in the database, although not having to deal with the setup of the database itself. Sticking to available database technology further does not force the user to learn new query languages just to be able to retrieve files from a database.

Furthermore, the `PyExperimenter` offers some convinience functionality, like logging errors or the possibility to reset experiments with a specific status, like failed ones.

The `PyExperimenter` was designed to be used by, e.g., machine learning, researchers and according students, but is not limited to those. The general structure of the project allows using the `PyExperimenter` also for other types of experiments, as long as the execution requires the same code parameterized in a different way.  

# Acknowledgements

This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).

# References
