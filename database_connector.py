import sys
import numpy as np
from mysql.connector import connect, ProgrammingError, DatabaseError
from datetime import datetime
import pandas as pd
import re

import utils
from utils import extract_db_credentials_and_table_name_from_config


class DatabaseConnector:

    def __init__(self, config):
        self.config = config
        self.table_name, host, user, database, password = extract_db_credentials_and_table_name_from_config(config)

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
        experiment_config = self.config['EXPERIMENT']
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
            [('status', 'VARCHAR(255)'), ('creation_date', 'VARCHAR(255)'), ('start_date', 'VARCHAR(255)'),
             ('end_date', 'VARCHAR(255)')])

        for field, datatype in typed_fields:
            query += '%s %s DEFAULT NULL, ' % (field, datatype)

        # remove last ', '
        query = query[:-2] + ')'

        try:
            self.dbcursor.execute(query)
        except ProgrammingError as err:
            unkown_datatype = str(err.__context__).split("'")[1].split(" ")[0]
            print("Error: '%s' is unknown or not allowed" % unkown_datatype)

    def fill_table(self) -> None:
        """
        Fill table with all combination of keyfield values, if combiation does not exist.
        :param connection: connection to database
        :param table_name: name of the table
        :param config: config file

        """
        keyfield_names, keyfield_data = utils.get_keyfields(self.config)
        # ref: https://www.kite.com/python/answers/how-to-get-all-element-combinations-of-two-numpy-arrays-in-python
        combinations = np.array(np.meshgrid(*keyfield_data)).T.reshape(-1, len(keyfield_data))

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
            if str(combination) in existing_rows:
                continue
            values = np.array2string(combination, separator=',').replace('[', '').replace(']', '')
            values += ",'created'"
            values += ",'%s'" % time.strftime("%m/%d/%Y, %H:%M:%S")
            self.write_to_database(columns_names, values)

    def get_parameters_to_execute(self):
        experiment_config = self.config['EXPERIMENT']

        execute_condition = "status='created'"

        keyfields = experiment_config['keyfields'].split(',')
        keyfield_names = utils.get_field_names(keyfields)

        query = "SELECT %s FROM %s WHERE %s" % (", ".join(keyfield_names), self.table_name, execute_condition)

        self.dbcursor.execute(query)
        parameters = pd.DataFrame(self.dbcursor.fetchall())
        parameters.columns = [i[0] for i in self.dbcursor.description]

        named_parameters = []
        for parameter in parameters.iterrows():
            named_parameters.append(re.sub(' +', '=', parameter[1].to_string()).replace('\n', ','))

        return named_parameters

    def write_to_database(self, column_names, values):
        query = """INSERT INTO %s (%s) VALUES (%s)""" % (self.table_name, column_names, values)
        self.dbcursor.execute(query)
        self.connection.commit()
