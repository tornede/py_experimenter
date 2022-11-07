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
  - name: Felix Mohr 
    orcid: 0000-0002-9293-2424
    affiliation: 2
  - name: Marcel Wever
    orcid: 0000-0001-9782-6818
    affiliation: 3
affiliations:
 - name: Department of Computer Science, Paderborn University, Germany
   index: 1
 - name: Universidad de La Sabana, Chia, Cundinamarca, Colombia
   index: 2
 - name: MCML, Institut for Informatics, LMU Munich, Germany
   index: 3
date: 7 November 2022
bibliography: paper.bib

---

# Summary

`PyExperimenter` is a tool to facilitate the setup, documentation, execution, and subsequent evaluation of results from an empirical study of algorithms and in particular is designed to reduce the involved manual effort significantly.
It is intended to be used by researchers in the field of artificial intelligence, but is not limited to those.

The empirical analysis of algorithms is often accompanied by the execution of algorithms for different inputs and variants of the algorithms (specified via parameters) and the measurement of non-functional properties.
Since the individual evaluations are usually independent, the evaluation can be performed in a distributed manner on an HPC system.
However, setting up, documenting, and evaluating the results of such a study is often file-based.
Usually, this requires extensive manual work to create configuration files for the inputs or to read and aggregate measured results from a report file.
In addition, monitoring and restarting individual executions is tedious and time-consuming.

These challenges are addressed by `PyExperimenter` by means of a single well defined configuration file and a central database for managing massively parallel evaluations, as well as collecting and aggregating their results.
Thereby, `PyExperimenter` alleviates the aforementioned overhead and allows experiment executions to be defined and monitored with ease.

![General schema of `PyExperimenter`.](usage.png)

A general schema of `PyExperimenter` can be found in Figure 1.
`PyExperimenter` is designed based on the assumption that an experiment is uniquely defined by certain inputs, i.e., parameters, and a function computing the results of the experiment based on these parameters.
The set of experiments to be executed can be defined through a configuration file listing the domains of each parameter, or manually through code.
Those parameters define the experiment grid, based on which `PyExperimenter` setups the table in the database featuring all experiments with their input parameter values and additional information such as the execution status.
Once this table has been created, a `PyExperimenter` instance can be run on any machine, including a distributed system.
Each instance automatically pulls open experiments from the database, executes the function provided by the user with the corresponding parameters defining the experiment and writes back the results computed by the function.
Errors arising during the execution are logged in the database.
In case of failed experiments or if desired otherwise, a subset of the experiments can be reset and restarted easily.
After all experiments are done, results can be jointly exported as a Pandas DataFrame [@pandas] for further processing, such as generating a LaTeX table averaging over different seeds.

## Statement of Need
The recent advances in artificial intelligence have uncovered a need for experiment tracking functionality, leading to the emergence of several tools addressing this issue.
Prominent representatives include Weights and Biases [@wandb], MLFlow [@mlflow], TensorBoard [@tensorboard], neptune.ai [@neptune], Comet.ML [@comet], Aim [@aim], Data Version Control [@dvc], Sacred [@sacred], and Guild.AI [@guildai].
These tools largely assume that users define the configuration of an experiment together with the experiment run itself.
In case of the evaluation of different hyperparameter configurations, this process is suboptimal, since it requires to communicate the hyperparameters through scripts.
This task can become cumbersome to manage as the number of configuration options and desired combinations grows and becomes more complex.
Weights and Biases [@wandb], Polyaxon [@polyaxon], and Comet.ML [@comet] allow so-called sweeps, i.e., hyperparameter optimization, albeit in a limited way.
For a sweep, usually hyperparameters that should be optimized are specified along with the desired search domains, and an optimizer can be selected from a pre-defined list to carry out the optimization.
However, the implementation of this functionality usually imposes several restrictions on the way the sweep can be carried out.

In contrast, `PyExperimenter` follows an inverted workflow.
Instead of experiment runners registering experiments to a tracking entity such as a tracking server or database, the experiments are predefined and runners are pulling open experiments from a database.
Similarly, ClearML [@clearml] and Polyaxon [@polyaxon] support a more generic workflow where experiments are first enqueued in a central orchestration server and agents can then pull tasks from the queue to execute them.
However, both are much more heavyweight than `PyExperimenter` regarding the implementation of both the agents and backend-features. 
Moreover, they are neither completely free nor completely open-source.

In addition to the inverted workflow, a core property of `PyExperimenter` is that the user has direct access to the experiment database, which is usually not the case for alternative tools.
This allows users to view, analyze and modify both the experiment inputs and results directly in the database, although not having to deal with the setup of the database itself.
Sticking to available database technology further does not force the user to learn new query languages just to be able to retrieve files from a database.
Furthermore, `PyExperimenter` offers some convenience functionality like logging errors and the possibility to reset experiments with a specific status such as experiments that failed.

`PyExperimenter` was designed to be used by researchers in the field of artificial intelligence, but is not limited to those.
The general structure of the project allows using `PyExperimenter` for many kinds of experiments as long as they can be defined in terms of input parameters and a correspondingly parameterized function.

# Acknowledgements

This work was partially supported by the German Federal Ministry for Economic Affairs and Climate Action (FLEMING project no.\ 03E16012F) and the German Research Foundation (DFG) within the Collaborative Research Center "On-The-Fly Computing" (SFB 901/3 project no.\ 160364472).

# References
