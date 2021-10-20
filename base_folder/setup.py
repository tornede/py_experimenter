from setuptools import setup, find_packages
#from pathlib import Path

#this_directory = Path(__file__).parent
#long_description = (this_directory / "PYPIREADME.md").read_text()

VERSION = '0.0.3'

setup(
    name="py_experimenter",
    version=VERSION,
    author="Lukas Gehring",
    author_email="lgehring@mail.upb.de",
    description="""The PyExperimenter is a tool for the automatic execution of various experiments.""",
    long_description_content_type="text/markdown",
    long_description="""
    With the PyExperimenter user can create a function that run one single experiment (we call this function `own_function`, but any function name is possible). The experiment itself,
    which is defined by its parameters, is then automatically executed by passing the parameters to the `own_function` and writing the
    results in a database. Errors that occur during execution are also captured by the PyExperimenter and written to the database.
    For the complete documentation, please visit the GitHub: https://github.com/lukasgehring/py_experimenter""",
    packages=find_packages(),
    install_requires=['mysql-connector-python', 'numpy', 'pandas'],
    keywords=['python', 'executor']
)