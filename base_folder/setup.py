from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Python experimenter'
LONG_DESCRIPTION = 'Missing'

setup(
    name="py_experimenter",
    version=VERSION,
    author="Lukas Gehring",
    author_email="<lgehring@mail.upb.de>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['mysql-connector-python', 'numpy', 'pandas'],
    keywords=['python', 'executor']
)