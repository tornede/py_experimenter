import logging
import sys
from typing import List

import numpy as np
from mysql.connector import connect, ProgrammingError, DatabaseError
from datetime import datetime
import pandas as pd
import re
import base_folder.py_experimenter.utils as utils


class DatabaseConnector:

    def __init__(self, config):
        self.config = config
        self.table_name, host, user, database, password = utils.extract_db_credentials_and_table_name_from_config(
            config)

        try:
            self.connection = connect(
                host=host,
                user=user,
                database=database,
                password=password
            )
            self.dbcursor = self.connection.cursor()
        except DatabaseError as err:
            sys.exit(err.__context__)

    def create_table_if_not_exists(self) -> None:
        """
        Check if tables does exist. If not, a new table will be created.
        :param mysql_connection: mysql_connector to the database
        :param table_name: name of the table from the config
        :param experiment_config: experiment section of the config file
        """
        experiment_config = self.config['PY_EXPERIMENTER']
        self.dbcursor.execute('SHOW TABLES')
        table_exists = False
        for table in self.dbcursor:
            if table[0] == self.table_name:
                table_exists = True

        if table_exists:
            return

        query = 'CREATE TABLE ' + self.table_name + ' ('
        fields = experiment_config['keyfields'].split(',') + experiment_config['resultfields'].split(',')
        clean_fields = [field.replace(' ', '') for field in fields]
        typed_fields = [tuple(field.split(':')) if len(field.split(':')) == 2 else (field, 'VARCHAR(255)') for
                        field in clean_fields]

        typed_fields.extend(
            [('status', 'VARCHAR(255)'), ('machine', 'INTEGER'), ('creation_date', 'VARCHAR(255)'),
             ('start_date', 'VARCHAR(255)'),
             ('end_date', 'VARCHAR(255)'), ('error', 'VARCHAR(255)')])

        for field, datatype in typed_fields:
            query += '%s %s DEFAULT NULL, ' % (field, datatype)

        # remove last ', '
        query = query[:-2] + ')'

        try:
            self.dbcursor.execute(query)
        except ProgrammingError as err:
            unkown_datatype = str(err.__context__).split("'")[1].split(" ")[0]
            print("Error: '%s' is unknown or not allowed" % unkown_datatype)

    def fill_table(self, own_parameters=None) -> None:
        """
        Fill table with all combination of keyfield values, if combiation does not exist.
        :param connection: connection to database
        :param table_name: name of the table
        :param config: config file

        """

        # ref: https://www.kite.com/python/answers/how-to-get-all-element-combinations-of-two-numpy-arrays-in-python
        keyfield_names = utils.get_keyfields(self.config)

        if own_parameters is None:
            keyfield_data = utils.get_keyfield_data(self.config)
            combinations = np.array(np.meshgrid(*keyfield_data)).T.reshape(-1, len(keyfield_data))
            combinations = [dict(zip(keyfield_names, combination)) for combination in combinations]
        else:
            combinations = own_parameters

        # check if combinations exist
        if len(combinations) == 0:
            return

        if own_parameters is not None:
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

        self.dbcursor.execute("SELECT %s FROM %s" % (columns_names, self.table_name))
        existing_rows = list(map(np.array2string, np.array(self.dbcursor.fetchall())))

        columns_names += ",status"
        columns_names += ",creation_date"

        time = datetime.now()
        for combination in combinations:
            if ("['" + "' '".join([str(value) for value in combination.values()]) + "']") in existing_rows:
                continue
            values = list(combination.values())
            values.append("created")
            values.append("%s" % time.strftime("%m/%d/%Y, %H:%M:%S"))

            self.write_to_database(columns_names.split(', '), values)

    def get_parameters_to_execute(self) -> List[dict]:
        experiment_config = self.config['PY_EXPERIMENTER']

        execute_condition = "status='created'"

        keyfields = experiment_config['keyfields'].split(',')
        keyfield_names = utils.get_field_names(keyfields)

        query = "SELECT %s FROM %s WHERE %s" % (", ".join(keyfield_names), self.table_name, execute_condition)

        self.dbcursor.execute(query)
        parameters = pd.DataFrame(self.dbcursor.fetchall())
        if parameters.empty:
            return []
        parameters.columns = [i[0] for i in self.dbcursor.description]

        named_parameters = [dict(parameter.to_dict()) for _, parameter in parameters.iterrows()]

        return named_parameters

    def write_to_database(self, keys, values) -> None:
        """
        Write new row(s) to database
        :param keys: Column names
        :param values: Values for column names
        """
        keys = ", ".join(keys)
        values = "'" + "', '".join([str(value) for value in values]) + "'"

        query = """INSERT INTO %s (%s) VALUES (%s)""" % (self.table_name, keys, values)

        self.dbcursor.execute(query)
        self.connection.commit()

    def update_database(self, keys, values, where):
        """
        Update existing row in database.
        :param keys: Column names that need to be updated
        :param values: New values for the specified columns
        :param where: Condition which row to update
        :return: 0 if error occurred, 1 otherwise.
        """
        new_data = ", ".join([f'{key}={value}' for key, value in zip(keys, values)])

        query = """UPDATE %s SET %s WHERE %s""" % (self.table_name, new_data, where)

        try:
            self.dbcursor.execute(query)
            self.connection.commit()
        except DatabaseError as err:
            # TODO: try except?
            query = """UPDATE %s SET error="%s" WHERE %s""" % (self.table_name, err, where)
            self.dbcursor.execute(query)
            self.connection.commit()
            return 0
        return 1
