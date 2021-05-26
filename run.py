import utils
import numpy as np


def fill_table(db_connection, table_name, config):
    experiment_config = config['EXPERIMENT']

    keyfields = experiment_config['keyfields'].split(',')
    clean_keyfields = [keyfield.replace(' ', '') for keyfield in keyfields]
    keyfield_names = [keyfield.split(':')[0] for keyfield in clean_keyfields]

    keyfield_data = []
    for data_name in keyfield_names:
        try:
            data = experiment_config[data_name].split(',')
            clean_data = [d.replace(' ', '') for d in data]
            keyfield_data.append(clean_data)
        except KeyError as err:
            print('Missing value definitions for %s' % err)

    # ref: https://www.kite.com/python/answers/how-to-get-all-element-combinations-of-two-numpy-arrays-in-python
    combinations = np.array(np.meshgrid(*keyfield_data)).T.reshape(-1, len(keyfield_data))

    cursor = db_connection.cursor()
    columns_names = np.array2string(np.array(keyfield_names), separator=',').replace('[', '').replace(']', '').replace("'", "")
    cursor.execute("SELECT %s FROM %s" % (columns_names, table_name))
    existing_rows = list(map(np.array2string, np.array(cursor.fetchall())))

    for combination in combinations:
        if str(combination) in existing_rows:
            continue
        values = np.array2string(combination, separator=',').replace('[', '').replace(']', '')
        query = """INSERT INTO %s (%s) VALUES (%s)""" % (table_name, columns_names, values)
        cursor.execute(query)
        db_connection.commit()


config = utils.load_config()
db_connection, table_name = utils.get_mysql_connection_and_table_name(config)
fill_table(db_connection, table_name, config)
