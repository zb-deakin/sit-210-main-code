from enum import Enum


class Command(Enum):
    Up = "up"
    Stop = "stop"
    Down = "down"


class Instruction:
    """
    Simple data class for type safety
    """
    shouldMoveUpward: bool = None
    newRequestedLength: float = None

    def __init__(self, _shouldMoveUpward: bool, _newRequestedLength: float):
        self.shouldMoveUpward: bool = _shouldMoveUpward
        self.newRequestedLength: float = _newRequestedLength

    def getValues(self) -> (bool, float):
        return tuple((
            self.shouldMoveUpward,
            self.newRequestedLength)
        )
