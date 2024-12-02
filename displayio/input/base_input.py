# ./input/base_input.py
from ..core.event import EventType, Event

class Input:
    def __init__(self):
        pass
    def check_input(self):
        event = Event(EventType.CUSTOM,target_position=[0,0])
        return event