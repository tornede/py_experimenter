from setuptools import find_packages, setup

#from pathlib import Path

#this_directory = Path(__file__).parent
#long_description = (this_directory / "PYPIREADME.md").read_text()

VERSION = '1.0.0'

setup(
    name="py_experimenter",
    version=VERSION,
    author="Tanja Tornede, Alexander Tornede, Lukas Fehring, Lukas Gehring, Helena Graf, Jonas Hanselle, Marcel Wever, Felix Mohr",
    author_email="tanja.tornede@upb.de, alexander.tornede@upb.de, fehring2@mail.uni-paderborn.de, helena.graf@upb.de, jonas.hanselle@upb.de, marcel.wever@ifi.lmu.de, felix.mohr@unisabana.edu.co",    
    description="""
        The PyExperimenter is a tool for the automatic execution of experiments, e.g. for machine learning (ML), capturing corresponding results in a unified manner in a database.
    """,
    long_description_content_type="text/markdown",
    long_description="""
        The PyExperimenter is a tool for the automatic execution of experiments, e.g. for machine learning (ML), 
        capturing corresponding results in a unified manner in a database. It is designed based on the assumption 
        that an experiment is uniquely defined by certain inputs, i.e., experiment parameters, and a function computing 
        the results of the experiment based on these input parameters. The set of experiments to be executed can be 
        defined through a configuration file listing the domains of each experiment parameter, or manually through code. 
        Based on the set of experiments defined by the user, PyExperimenter creates a table in the database featuring 
        all experiments identified by their input parameter values and additional information such as the execution 
        status. Once this table has been created, PyExperimenter can be run on any machine, including a distributed 
        cluster. Each PyExperimenter instance automatically pulls open experiments from the database, executes the 
        experiment function provided by the user with the corresponding experiment parameters defining the experiment 
        and writes back the results computed by the function. Possible errors arising during the execution are logged 
        in the database. After all experiments are done, the experiment evaluation table can be easily extracted, e.g. 
        averaging over different seeds.
        For the complete documentation, please visit GitHub: https://github.com/tornede/py_experimenter
    """,
    packages=find_packages(),
    install_requires=['numpy', 'pandas', 'mysql-connector-python', 'pytest', 'mock'],
    keywords=['python', 'experiments', 'database', 'executor']
)
