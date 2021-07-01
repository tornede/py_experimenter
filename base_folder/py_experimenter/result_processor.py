from typing import List

from base_folder.py_experimenter.database_connector import DatabaseConnector


class ResultProcessor:

    def __init__(self, dbconnector: DatabaseConnector, condition: dict, result_fields: List[str]):
        self._dbconnector = dbconnector
        self._where = ' AND '.join([f"{str(key)}='{str(value)}'" for key, value in condition.items()])
        self._result_fields = result_fields

    def process_results(self, results: dict):
        result_fields = list(results.keys())
        result = list(results.values())

        if not self._valid_result_fields(result_fields):
            print("Key does not exist!")
            return False

        self._dbconnector.update_database(result_fields, result, self._where)

    def _valid_result_fields(self, result_fields):
        for result_field in result_fields:
            if result_field not in self._result_fields:
                return False
        return True


