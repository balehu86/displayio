from machine import TouchPad,Pin # type: ignore
import time
from .base_input import Input
from ..core.event import Event

class TouchPin(Input):
    def __init__(self, pin, target_widget=None, target_position=None, touch_threshold = 100000):

        super().__init__(TouchPad(Pin(pin)),
                         target_widget=target_widget,
                         target_position=target_position)
        
        # 触摸数据阈值
        self.touch_threshold = touch_threshold 
        
    def check_input(self):
        touch_value = self.input.read()
        current_time = time.ticks_ms()
        # 非阻塞的触摸状态机
        if touch_value > self.touch_threshold:
            # 触摸按下
            if self.state == self.IDLE:
                self.state = self.PRESS
                self.press_start_time = current_time
            
            # 检查长按
            press_duration = time.ticks_diff(current_time,self.press_start_time)
            if press_duration >= self.long_press_duration:
                self.state = self.LONG_PRESS
                return Event(self.LONG_PRESS,
                             target_widget=self.target_widget,
                             target_position=self.target_position)
        else:
            # 触摸释放
            if self.state==self.PRESS or self.state==self.LONG_PRESS:
                press_duration = time.ticks_diff(current_time, self.press_start_time)         
                
                # 有效点击检测
                if self.click_min_duration < press_duration < self.click_max_duration:
                    # 首次点击
                    if self.click_count == 0:
                        self.click_count = 1
                        self.last_click_time = current_time
                        self.state = self.IDLE
                        return Event(self.CLICK, 
                                     target_widget=self.target_widget, 
                                     target_position=self.target_position)
                    # 双击检测
                    elif self.click_count == 1:
                        click_interval = time.ticks_diff(current_time, self.last_click_time)
                        
                        if click_interval <= self.double_click_max_interval:
                            # 双击确认
                            self.click_count = 0
                            self.last_click_time = current_time
                            self.state = self.IDLE
                            return Event(self.DOUBLE_CLICK, 
                                         target_widget=self.target_widget, 
                                         target_position=self.target_position)
                        else:
                            # 超出双击窗口，重置状态
                            self.last_click_time = current_time
                            self.state = self.IDLE
                            return Event(self.CLICK, 
                                        target_widget=self.target_widget, 
                                        target_position=self.target_position)

            self.state = self.IDLE        
        return None