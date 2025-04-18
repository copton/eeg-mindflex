from enum import Enum


class ActorState(Enum):
    INIT = "init"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    COMPLETED = "completed"
