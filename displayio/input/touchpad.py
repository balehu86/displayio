from machine import TouchPad,Pin # type: ignore
import time

from ..core.event import EventType, Event

class TouchPin:
    IDLE = 0

    PRESS = 1             # 按下
    RELEASE = 2           # 释放

    CLICK = 3             # 点击
    LONG_PRESS = 4        # 长按
    DOUBLE_CLICK = 5      # 双击

    
    def __init__(self, pin=None, touch_threshold = 100000):
        self.touch = TouchPad(Pin(pin))
        self.state = self.IDLE
        self.press_start_time = 0
        self.touch_threshold = touch_threshold # 触摸数据阈值
        self.last_check_time = 0
        self.long_press_duration = 500  # 长按阈值：500ms
        self.click_min_duration = 8     # 最小点击时间：8ms
        self.click_max_duration = 400   # 最大点击时间：400ms

    def check_input(self):
        touch_value = self.touch.read()
        # 非阻塞的触摸状态机
        if touch_value > self.touch_threshold:
            # 触摸按下
            if self.state == self.IDLE:
                self.state = self.PRESSED
                self.press_start_time = time.ticks_ms()
            
            # 检查长按
            press_duration = time.ticks_diff(time.ticks_ms(),self.press_start_time)
            if press_duration >= self.long_press_duration:
                self.state = self.LONG_PRESS
                return "LONG_PRESS"
        else:
            # 触摸释放
            if self.state == self.PRESSED:
                press_duration = time.ticks_ms() - self.press_start_time
                
                # 检查是否为有效点击
                if (self.click_min_duration < press_duration < 
                    self.click_max_duration):
                    self.state = self.IDLE
                    return "CLICK"
            
            # 重置状态
            self.state = self.IDLE
            self.press_start_time = 0
        
        return None