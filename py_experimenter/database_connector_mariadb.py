from configparser import ConfigParser
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL

class DatabaseConnectorMariaDB(DatabaseConnectorMYSQL):

    def __init__(self, experiment_configuration_file_path: ConfigParser, database_credential_file_path):
        super().__init__(experiment_configuration_file_path, database_credential_file_path, explicit_transactions = False)