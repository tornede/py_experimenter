class PyExperimenterError(Exception):
    pass


class ParameterCombinationError(PyExperimenterError):
    pass


class DatabaseError(PyExperimenterError):
    pass


class DatabaseCreationError(DatabaseError):
    pass


class DatabaseConnectionError(DatabaseError):
    pass


class DatabaseQueryError(DatabaseError):
    pass


class EmptyFillDatabaseCallError(DatabaseError):
    pass


class TableError(DatabaseError):
    pass


class InvalidResultFieldError(DatabaseError):
    pass


class TableHasWrongStructureError(TableError):
    pass


class ConfigError(PyExperimenterError):
    pass


class NoConfigFileError(ConfigError, FileNotFoundError):
    pass


class InvalidConfigError(ConfigError):
    pass


class InvalidValuesInConfiguration(ConfigError):
    pass
