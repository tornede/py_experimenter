from typing import List
import mysql.connector
from mysql.connector import errorcode, DatabaseError
from datetime import datetime


class ResultProcessor:

    def __init__(self, dbcredentials: dict, table_name: str, condition: dict, result_fields: List[str]):
        self._dbcredentials = dbcredentials
        self.table_name = table_name
        self._where = ' AND '.join([f"{str(key)}='{str(value)}'" for key, value in condition.items()])
        self._result_fields = result_fields

    def process_results(self, results: dict):
        result_fields = list(results.keys())
        result = list(results.values())

        if not self._valid_result_fields(result_fields):
            print("Key does not exist!")
            return False

        self._update_database(keys=result_fields, values=result)

        new_data = ", ".join([f'{key}={value}' for key, value in zip(result_fields, result)])

        query = """UPDATE %s SET %s WHERE %s""" % (self.table_name, new_data, self._where)

        try:
            self._cnx = mysql.connector.connect(**self._dbcredentials)
            cursor = self._cnx.cursor()

            try:
                cursor.execute(query)
                self._cnx.commit()
            except DatabaseError as err:
                # TODO: try except?
                query = """UPDATE %s SET error="%s" WHERE %s""" % (self.table_name, err, self._where)
                cursor.execute(query)
                self._cnx.commit()

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        else:
            print("Successfully connected to database")
            self._cnx.close()

    def _update_database(self, keys, values):
        """
        Update existing row in database.
        :param keys: Column names that need to be updated
        :param values: New values for the specified columns
        :param where: Condition which row to update
        :return: 0 if error occurred, 1 otherwise.
        """
        new_data = ", ".join([f'{key}={value}' for key, value in zip(keys, values)])

        query = """UPDATE %s SET %s WHERE %s""" % (self.table_name, new_data, self._where)

        try:
            self._cnx = mysql.connector.connect(**self._dbcredentials)
            cursor = self._cnx.cursor()

            try:
                cursor.execute(query)
                self._cnx.commit()
            except DatabaseError as err:
                # TODO: try except?
                query = """UPDATE %s SET error="%s" WHERE %s""" % (self.table_name, err, self._where)
                cursor.execute(query)
                self._cnx.commit()

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        else:
            print("Successfully connected to database")
            self._cnx.close()

    def _change_status(self, status):
        time = datetime.now()
        time = "'%s'" % time.strftime("%m/%d/%Y, %H:%M:%S")
        if status == 'running':
            self._update_database(['status', 'start_date'], ["'running'", time])
        if status == 'done':
            self._update_database(['status', 'end_date'], ["'done'", time])

    def _set_machine(self, machine_id):
        self._update_database(['machine'], [machine_id])


    def _valid_result_fields(self, result_fields):
        for result_field in result_fields:
            if result_field not in self._result_fields:
                return False
        return True

#d = dict(host='isys-otfml.cs.upb.de', user='lgehring', database='lgehring',password='hUqU2XJvZ4wzCiE')
#ResultProcessor(d, None,None)


