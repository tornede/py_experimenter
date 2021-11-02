from typing import List


class DatabaseConnector:

    def create_table_if_not_exists(self) -> None:
        """
        Check if tables does exist. If not, a new table will be created.
        :param mysql_connection: mysql_connector to the database
        :param table_name: name of the table from the config
        :param experiment_config: experiment section of the config file
        """
        pass

    def fill_table(self, individual_parameters=None, parameters=None) -> None:
        """
        Fill table with all combination of keyfield values, if combiation does not exist.
        :param connection: connection to database
        :param table_name: name of the table
        :param config: config file

        """
        pass

    def get_parameters_to_execute(self) -> List[dict]:
        pass

    def _write_to_database(self, keys, values) -> None:
        """
        Write new row(s) to database
        :param keys: Column names
        :param values: Values for column names
        """
        pass


    def _update_database(self, keys, values, where):
        pass

    def get_not_executed_yet(self, where) -> bool:
        pass
