import logging
import sys
from typing import List

import mysql
import numpy as np
from mysql.connector import connect, ProgrammingError
from datetime import datetime
import pandas as pd
import utils as utils


class DatabaseConnector:

    def __init__(self, config):
        self.config = config
        self.table_name, host, user, database, password = utils.extract_db_credentials_and_table_name_from_config(
            config)
        self._db_credentials = dict(host=host, user=user, database=database, password=password)

        # try connection to database and exit program if connection not possible
        try:
            connection = connect(**self._db_credentials)

        except mysql.connector.Error as err:
            logging.error(err)
            sys.exit(1)

        else:
            connection.close()

    def create_table_if_not_exists(self) -> None:
        """
        Check if tables does exist. If not, a new table will be created.
        :param mysql_connection: mysql_connector to the database
        :param table_name: name of the table from the config
        :param experiment_config: experiment section of the config file
        """
        experiment_config = self.config['PY_EXPERIMENTER']

        try:
            connection = connect(**self._db_credentials)
            cursor = connection.cursor()

            cursor.execute(f"SHOW TABLES LIKE '{self.table_name}'")

            # load column names from config
            fields = experiment_config['keyfields'].split(',') + experiment_config['resultfields'].split(',')

            # remove whitespace
            clean_fields = [field.replace(' ', '') for field in fields]

            # (name, type) - default type is 'VARCHAR(255)'
            typed_fields = [tuple(field.split(':')) if len(field.split(':')) == 2 else (field, 'VARCHAR(255)') for
                            field in clean_fields]

            # exit if table already exist
            if cursor.fetchall():
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.table_name}'")

                # ignore ID and the last six columns since they are not defined by the user
                columns = [k[0] for k in cursor.fetchall()][1:-6]
                config_columns = [k[0] for k in typed_fields]

                # check if fields in config match with columns in database
                if set(columns) == set(config_columns):
                    return

                logging.error("Keyfields or resultfields from the configuration do not match columns in the existing "
                              "table. Please change your configuration or delete the table in your database.")
                sys.exit()

            # extend experiment columns by pyexperimenter columns
            typed_fields.extend(
                [('status', 'VARCHAR(255)'), ('machine', 'VARCHAR(255)'), ('creation_date', 'VARCHAR(255)'),
                 ('start_date', 'VARCHAR(255)'),
                 ('end_date', 'VARCHAR(255)'), ('error', 'LONGTEXT')])

            # set default value for each column to NULL
            columns = ['%s %s DEFAULT NULL' % (field, datatype) for field, datatype in typed_fields]

            stmt = f"CREATE TABLE {self.table_name} (ID int NOT NULL AUTO_INCREMENT, {','.join(columns)}, PRIMARY KEY (ID))"

            try:
                cursor.execute(stmt)
            except ProgrammingError:
                logging.error("An error occurred while creating the table in the database. Please check the "
                              "configuration file for allowed characters and data types for the keyfields and resultfields "
                              "as well as the table name.")
                sys.exit(1)

        except mysql.connector.Error as err:
            logging.error(err)
            sys.exit(1)

        else:
            connection.close()

    def fill_table(self, individual_parameters=None, parameters=None) -> None:
        """
        Fill table with all combination of keyfield values, if combiation does not exist.
        :param connection: connection to database
        :param table_name: name of the table
        :param config: config file

        """

        # ref: https://www.kite.com/python/answers/how-to-get-all-element-combinations-of-two-numpy-arrays-in-python
        keyfield_names = utils.get_keyfields(self.config)

        if individual_parameters is None:
            if parameters is None:
                keyfield_data = utils.get_keyfield_data(self.config)
            else:
                keyfield_data = list(parameters.values())

            combinations = np.array(np.meshgrid(*keyfield_data)).T.reshape(-1, len(keyfield_data))
            combinations = [dict(zip(keyfield_names, combination)) for combination in combinations]
        else:
            combinations = individual_parameters

        # check if combinations exist
        if len(combinations) == 0:
            return

        if individual_parameters is not None:
            _number_of_keys = 0
            for key in combinations[0].keys():

                if key not in keyfield_names:
                    logging.error(f"Keyfield '{key}' is not defined in configuration file")
                    sys.exit()

                _number_of_keys += 1

            if _number_of_keys != len(keyfield_names):
                logging.error(f"{len(keyfield_names) - _number_of_keys} keyfield(s) missing! Please check passed parameters contain all keyfields defined in the configuration file.")
                sys.exit()



        columns_names = np.array2string(np.array(keyfield_names), separator=',') \
            .replace('[', '') \
            .replace(']', '') \
            .replace("'", "")

        try:
            connection = connect(**self._db_credentials)
            cursor = connection.cursor()
            cursor.execute(f"SELECT {columns_names} FROM {self.table_name}")
            existing_rows = list(map(np.array2string, np.array(cursor.fetchall())))

        except mysql.connector.Error as err:
            logging.error(err)
            sys.exit(1)

        else:
            connection.close()

        columns_names += ",status"
        columns_names += ",creation_date"

        time = datetime.now()
        for combination in combinations:
            if ("['" + "' '".join([str(value) for value in combination.values()]) + "']") in existing_rows:
                continue
            values = list(combination.values())
            values.append("created")
            values.append("%s" % time.strftime("%m/%d/%Y, %H:%M:%S"))

            self._write_to_database(columns_names.split(', '), values)

    def get_parameters_to_execute(self) -> List[dict]:
        experiment_config = self.config['PY_EXPERIMENTER']

        execute_condition = "status='created'"

        keyfields = experiment_config['keyfields'].split(',')
        keyfield_names = utils.get_field_names(keyfields)

        stmt = f"SELECT {', '.join(keyfield_names)} FROM {self.table_name} WHERE {execute_condition}"

        try:
            connection = connect(**self._db_credentials)
            cursor = connection.cursor()

            try:
                cursor.execute(stmt)
            except ProgrammingError as e:
                logging.error(str(e) + "\nPlease check if 'fill_table()' was called correctly.")
                sys.exit(1)

            parameters = pd.DataFrame(cursor.fetchall())
            if parameters.empty:
                return []
            parameters.columns = [i[0] for i in cursor.description]

        except mysql.connector.Error as err:
            logging.error(err)
            sys.exit(1)

        else:
            connection.close()

        named_parameters = [dict(parameter.to_dict()) for _, parameter in parameters.iterrows()]

        return named_parameters

    def _write_to_database(self, keys, values) -> None:
        """
        Write new row(s) to database
        :param keys: Column names
        :param values: Values for column names
        """
        if len(keys[0].split(',')) != len(values):
            logging.error('Keyfield(s) missing! Please check passed parameters contain all keyfields defined in the configuration file.')
            sys.exit(1)

        keys = ", ".join(keys)
        values = "'" + "', '".join([str(value) for value in values]) + "'"

        stmt = f"INSERT INTO {self.table_name} ({keys}) VALUES ({values})"

        try:
            connection = connect(**self._db_credentials)
            cursor = connection.cursor()

            cursor.execute(stmt)
            connection.commit()

        except mysql.connector.Error as err:
            logging.error(err)
            sys.exit(1)

        else:
            connection.close()
