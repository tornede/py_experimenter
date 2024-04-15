from enum import Enum


class ExperimentStatus(Enum):
    CREATED = "created"
    CREATED_FOR_EXECUTION = "created_for_execution"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    ALL = "all"
    PAUSED = "paused"
