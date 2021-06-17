import sys
import utils
from multiprocessing import Pool

from database_connector import DatabaseConnector

def run(approach):
    config, table_name = utils.load_config_and_table_name('config/configuration.cfg')
    dbconnector = DatabaseConnector(config)
    dbconnector.create_table_if_not_exists()
    dbconnector.fill_table()

    parameters = dbconnector.get_parameters_to_execute()

    try:
        cpus = int(config['EXPERIMENT']['cpu.max'])
    except ValueError:
        sys.exit('Error in config file: cpu.max must be integer')

    with Pool(cpus) as p:
        print(p.map(approach, parameters))

    # TODO: Check results and write to database


def own_function(parameter):
    result = [1, 2, 3]
    return result


run(own_function)
