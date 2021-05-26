import utils

config = utils.load_config()
db_connection, table_name = utils.get_mysql_connection_and_table_name(config)
