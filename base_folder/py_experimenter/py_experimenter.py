import sys
import base_folder.py_experimenter.utils as utils
import concurrent.futures
from datetime import datetime
from base_folder.py_experimenter.database_connector import DatabaseConnector
from base_folder.py_experimenter.result_processor import ResultProcessor


class PyExperimenter:

    def __init__(self, config_path='config/configuration.cfg', print_log=True) -> None:
        """
        Load configuration and connect to the database.

        :param config_path: Path to the configuration file.
        """

        self.print_log = print_log

        # load and check config for mandatory fields
        self._config = utils.load_config(config_path)
        if not self._valid_configuration():
            # TODO: how to end?
            print("configuration file invalid")
            sys.exit()

        # connect to database
        self._dbconnector = DatabaseConnector(self._config)

        self.log('initialized and connected to database')

    def _valid_configuration(self):
        if not {'host', 'user', 'database', 'password', 'table'}.issubset(set(self._config.options('DATABASE'))):
            return False
        if not {'cpu.max', 'keyfields',
                'resultfields'}.issubset(set(self._config.options('PY_EXPERIMENTER'))):
            return False

        return True

    def fill_table(self) -> None:
        """
        Create (if not exist) and fill table in database with parameter combinations. If there are already entries in
        the table, only parameter combinations for which there is no entry in the database will be added. The status
        of this parameter combination is set to 'created'.
        """
        self.log("create table if not exist")
        self._dbconnector.create_table_if_not_exists()
        self.log("fill table with parameters")
        self._dbconnector.fill_table()
        self.log("parameters successfully inserted to table")

    def execute(self, approach) -> None:
        """
        Execute all parameter combinations from the database with status 'created'. If the execution was successful,
        the results will be written in the database. Any errors that occur during execution are also written to the
        database. After execution, the status of the instance is set to 'done', or 'error'.
        :param approach:
        """

        self.log("start execution of approaches...")
        # load parameters (approach input) and results fields (approach output)
        parameters = self._dbconnector.get_parameters_to_execute()
        result_fields = utils.get_field_names(self._config['PY_EXPERIMENTER']['resultfields'].split(', '))

        # update status to 'running' and set start date
        # TODO: not working (and add machine number)
        # time = datetime.now()
        # time = "'%s'" % time.strftime("%m/%d/%Y, %H:%M:%S")
        # for parameter in parameters:
        #    conditions = parameter.replace(",", "' AND ").replace("=", "='") + "'"
        #    self._dbconnector.update_database(['status', 'start_date'], ["'running'", time], conditions)

        # read cpu.max
        try:
            cpus = int(self._config['PY_EXPERIMENTER']['cpu.max'])
        except ValueError:
            sys.exit('Error in config file: cpu.max must be integer')

        table_name, host, user, database, password = utils.extract_db_credentials_and_table_name_from_config(self._config)
        dbcredentials = dict(host=host, user=user, database=database, password=password)

        # execute approach
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpus) as executor:
            # execute instances parallel
            result_processors = [ResultProcessor(dbcredentials=dbcredentials, table_name=table_name, condition=p, result_fields=result_fields) for p in parameters]
            #result_processors = [ResultProcessor() for p in parameters]
            #result_processors = ["Test" for p in parameters]

            results = executor.map(approach, parameters, result_processors)
            self.log("execution finished")

            # update status to 'done', set end date and write result or error in database
            for i, result in enumerate(results):

                # check number of returned result fields
                if len(result) != len(result_fields):
                    print("Wrong number of returned values!")
                    continue

                result = [f"'{v}'" if isinstance(v, str) else str(v) for v in result]

                conditions = parameters[i].replace(",", "' AND ").replace("=", "='") + "'"

                # finish date
                time = datetime.now()
                time = "'%s'" % time.strftime("%m/%d/%Y, %H:%M:%S")

                # write result to database
                if not self._dbconnector.update_database(result_fields, result, conditions):
                    # write error to database and set status to 'error
                    self._dbconnector.update_database(['status', 'end_date'], ["'error'", time], conditions)
                    continue

                # everything was correct - set status to 'done'
                self._dbconnector.update_database(['status', 'end_date'], ["'done'", time], conditions)
        self.log("all executions finished")

    def log(self, msg: str):
        if self.print_log:
            print("PyExperimenter:", msg)
