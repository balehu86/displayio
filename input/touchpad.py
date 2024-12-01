from machine import TouchPad,Pin # type: ignore
import time

class TouchPad():
    def __init__(self, pin=None):
        self.touch = TouchPad(Pin(pin))
    def check(self):
        if self.touch.read() > 100000:
            time.sleep_ms(120)
            if self.touch.read()>100000:
                event=Event(EventType.CLICK,target_position=[0,200])
                display.add_event(event)
                print('changed')