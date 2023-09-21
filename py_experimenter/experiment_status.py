from enum import Enum


class ExperimentStatus(Enum):
    CREATED = 'created'
    RUNNING = 'running'
    DONE = 'done'
    ERROR = 'error'
    ALL = 'all'
    PAUSED = 'paused'
