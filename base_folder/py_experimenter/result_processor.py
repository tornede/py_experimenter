import logging
from typing import List

from py_experimenter.database_connector_lite import DatabaseConnectorLITE
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL
from datetime import datetime

result_logger = logging.getLogger('result_logger')
result_logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')

file_handler = logging.FileHandler('result.log')
file_handler.setFormatter(formatter)

result_logger.addHandler(file_handler)


class ResultProcessor:
    """
    Class for processing the results from an experiment. Use this class whenever you want to write results to the
    database.
    """

    def __init__(self, config: dict, table_name: str, condition: dict, result_fields: List[str]):
        self.table_name = table_name
        self._where = ' AND '.join([f"{str(key)}='{str(value)}'" for key, value in condition.items()])
        self._result_fields = result_fields

        if config['DATABASE']['provider'] == 'sqlite':
            self._dbconnector = DatabaseConnectorLITE(config)
        elif config['DATABASE']['provider'] == 'mysql':
            self._dbconnector = DatabaseConnectorMYSQL(config)

    def process_results(self, results: dict) -> None:
        """
        Process results from the experiemtn and write them to the database. You can call this method, whenever you
        want to write results to the database.
        :param results: Dictionary with result field name and result value pairs.
        """

        # extract result field names and result values
        result_fields = list(results.keys())
        result = list(results.values())

        # check if result field names exist
        if not self._valid_result_fields(result_fields):
            logging.error("Key does not exist!")
            self._write_error("Key does not exist!")
            return

        # write results to database
        self._dbconnector._update_database(keys=result_fields, values=result, where=self._where)

    # def _update_database(self, keys, values):
    #    logging.info(f"Update '{keys}' with values '{values}' in database")
    #
    #       self._cnx = mysql.connector.connect(**self._dbcredentials)
    #      cursor = self._cnx.cursor()
    #
    #       try:
    #          for key, value in zip(keys, values):
    #             stmt = f"UPDATE {self.table_name} SET {key}=%s WHERE {self._where}"
    #            cursor.execute(stmt, (value,))
    #           result_logger.info(cursor.statement)
    #      self._cnx.commit()
    # except DatabaseError as err:
    #    logging.error(err)
    #   query = """UPDATE %s SET error="%s" WHERE %s""" % (self.table_name, err, self._where)
    #  cursor.execute(query)
    # self._cnx.commit()

    # self._cnx.close()

    def _change_status(self, status):

        # get current time
        time = datetime.now()
        time = time.strftime("%m/%d/%Y, %H:%M:%S")

        # set current time to start date
        if status == 'running':
            self._dbconnector._update_database(keys=['status', 'start_date'], values=["running", time],
                                               where=self._where)

        # set current time to end date
        if status == 'done' or status == 'error':
            self._dbconnector._update_database(keys=['status', 'end_date'], values=[status, time], where=self._where)

    def _write_error(self, error_msg):
        self._dbconnector._update_database(keys=['error'], values=[error_msg], where=self._where)

    def _set_machine(self, machine_id):
        self._dbconnector._update_database(keys=['machine'], values=[machine_id], where=self._where)

    def _not_executed_yet(self) -> bool:
        return self._dbconnector.get_not_executed_yet(where=self._where)

    # def _not_executed_yet(self) -> bool:
    #     not_executed = False
    #
    #     try:
    #         self._cnx = mysql.connector.connect(**self._dbcredentials)
    #         cursor = self._cnx.cursor()
    #
    #         query = "SELECT status FROM %s WHERE %s" % (self.table_name, self._where)
    #
    #         cursor.execute(query)
    #         for result in cursor:
    #             if result[0] == 'created':
    #                 not_executed = True
    #
    #     except mysql.connector.Error as err:
    #         if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    #             logging.error("Something is wrong with your user name or password")
    #         elif err.errno == errorcode.ER_BAD_DB_ERROR:
    #             logging.error("Database does not exist")
    #         else:
    #             logging.error(err)
    #     else:
    #         self._cnx.close()
    #         return not_executed

    def _valid_result_fields(self, result_fields):
        for result_field in result_fields:
            if result_field not in self._result_fields:
                # result field name is not defined in configuration
                return False
        return True
