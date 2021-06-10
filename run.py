import sys
import utils
from multiprocessing import Pool


def run(approach):
    config = utils.load_config()
    connection, table_name = utils.get_mysql_connection_and_table_name(config)
    utils.fill_table(connection, table_name, config)

    parameters = utils.get_parameters_from_table(connection, table_name, config)

    try:
        cpus = int(config['EXPERIMENT']['cpu.max'])
    except ValueError:
        sys.exit('Error in config file: cpu.max must be integer')
    results = []
    with Pool(cpus) as p:
        results.append(p.map(approach, parameters))

    # TODO: Check results and write to database
    # print(results)


def own_function(parameter):
    print("Run apporach with", parameter)

    result = [1, 2, 3]
    return result


run(own_function)
