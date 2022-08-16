from setuptools import find_packages, setup

#from pathlib import Path

#this_directory = Path(__file__).parent
#long_description = (this_directory / "PYPIREADME.md").read_text()

VERSION = '0.0.4'

setup(
    name="py_experimenter",
    version=VERSION,
    author="Tanja Tornede, Alexander Tornede",
    author_email="tanja.tornede@upb.de, alexander.tornede@upb.de",
    description="""The PyExperimenter is a tool for the automatic execution of various experiments.""",
    long_description_content_type="text/markdown",
    long_description="""
        The PyExperimenter is a tool for the automatic execution of various experiments. The user can create a function 
        to run a single experiment (we call this function `own_function`, but any function name is possible). The experiment itself, 
        which is defined by its parameters, is then automatically executed by passing the parameters to the `own_function` and writing the
        results into a database. Errors that occur during execution are also captured by the PyExperimenter and written to the database.
        For the complete documentation, please visit GitHub: https://github.com/alexandertornede/py_experimenter
    """,
    packages=find_packages(),
    install_requires=['numpy', 'pandas', 'mysql-connector-python'],
    keywords=['python', 'experiments', 'executor']
)
