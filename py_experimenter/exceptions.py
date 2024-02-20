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


class CreatingTableError(DatabaseError):
    pass


class InvalidResultFieldError(DatabaseError):
    pass


class InvalidLogFieldError(DatabaseError):
    pass


class TableHasWrongStructureError(CreatingTableError):
    pass


class NoExperimentsLeftException(PyExperimenterError):
    pass


class NoPausedExperimentsException(PyExperimenterError):
    pass


class ConfigError(PyExperimenterError):
    pass


class NoConfigFileError(ConfigError, FileNotFoundError):
    pass


class InvalidConfigError(ConfigError):
    pass


class InvalidValuesInConfiguration(ConfigError):
    pass


class MissingLogTableError(ConfigError):
    pass


class InvalidColumnError(Exception):
    pass


class InvalidLogtableError(Exception):
    pass
