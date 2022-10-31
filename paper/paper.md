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
date: 31 Oktober 2022
bibliography: paper.bib

---

# Summary

Executing parameterized experiments, e.g. for machine learning (ML), and capturing their results is a task that should be well prepared.
Thereby, any overhead should be avoided, i.e., having to create multiple configuration files to run an experiment with different seeds, or having to extract information from a log file.
The `PyExperimenter` is a tool for the automatic execution of experiments, e.g. for machine learning (ML), capturing corresponding results in a unified manner in a database.
The experiments to be executed are defined in advance. All information about an experiment are stored in a database, starting with the configuration, followed by a continously updated status, and closed by the results of the experiment. This allows a parallelization of the execution of experiments, only limited by the number of possible parallel open database connections.

![General schema of `PyExperimenter`.](usage.png)

A general schema of the `PyExperimenter` can be found in Figure 1. The `PyExperimenter` is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing the results of the experiment based on these input parameters. The set of experiments to be executed can be defined through a configuration file listing the domains of each experiment parameter, or manually through code. Those experiment parameters define the experiment grid, based on which the `PyExperimenter` setups the experiment table in the database featuring all experiments identified by their input parameter values and additional information such as the execution status. Once this table has been created, `PyExperimenter` can be run on any machine, including a distributed cluster. Each `PyExperimenter` instance automatically pulls open experiments from the database, executes the experiment function provided by the user with the corresponding experiment parameters defining the experiment and writes back the experiment results computed by the function. Possible errors arising during the execution are logged in the database. In case of failed experiments or other circumstances, a subset of the experiments can be easily reset and executed again. After all experiments are done, the experiment evaluation table can be easily extracted, e.g. averaging over different seeds.

## Statement of Need

There are already many experiment tracking tools available, especially for machine learning, like Weights and Biases [@wandb], MLFlow [@mlflow], TensorBoard [@tensorboard], Aim [@aim], Comet [@comet], Data Version Control [@dvc], Sacred [@sacred], Guild.AI [@guildai] and neptune.ai [@neptune]. These tools largely assume that users define the configuration of an experiment together with the experiment run itself. In case of the evaluation of different hyperparameter configurations, this process is suboptimal, since it requires to communicate the hyperparameters through scripts. This task can become cumbersome to manage as the number of configuration options and desired combinations grows and becomes more complex. Weights and Biases [@wandb], Polyaxon [@polyaxon], and Comet [@comet] allow so-called sweeps, i.e., hyperparameter optimizations, albeit in a limited way. For a sweep, usually hyperparameters that should be optimized are specified along with the desired search domains, and an optimizer can be selected from a pre-defined list to carry out the optimization. However, the implementation of this functionality usually imposes several restrictions on the way the sweep can be carried out. The `PyExperimenter` follows an inverted workflow. Instead of experiment runners reporting configurations to a tracking entity such as a tracking server or database, the configurations are predefined and runners are pulling configuration values from a database of open experiments. ClearML [@clearml] and Polyaxon [@polyaxon] support a workflow where experiments are first enqueued in a central orchestration server and agents can then pull tasks from the queue to execute in a more universal way. However, both are much more heavyweight than the `PyExperimenter`, regarding the implementation of both the agents and backend-features, and are further neither completely open-source nor free.

In addition to the inverted workflow, a core property of the `PyExperimenter` is that the user has direct access to the experiment database, which is not usually the case for alternative tools. Allowing users to have full control over the database in which the results are stored lets them modify the results storage to their specific needs, which might not fit into the standard stencil of result storage and retrieval of other tools. In case a MySQL backend is needed, a tradeoff of the `PyExperimenter` is that the user needs to provide the database. The `PyExperimenter` then creates desired tables and fields, which together with the experiment creation and retrieval methods offers an advantage over a completely manual database administration. Sticking to available database technology further does not force the user to learn new query languages just to be able to retrieve files from a database.

Furthermore, the `PyExperimenter` offers some convinience functionality, like logging errors or the possibility to reset experiments with a specific status, like failed ones. 

The `PyExperimenter` was designed to be used by, e.g., machine learning, researchers and according students, but is not limited to those. The general structure of the project allows using the `PyExperimenter` also for other types of experiments, as long as the execution requires the same code parameterized in a different way.  

# Acknowledgements

This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).

# References
