from machine import Pin # type: ignore
import time
from .base_input import Input
from ..core.event import Event

class Switch(Input):
    __slots__ = ('mode', 'threshold', 'pin', 'press_start_time'
                 'last_release_time', 'click_min_duration', 'click_max_duration',
                 'long_press_duration', 'double_click_max_interval')
    
    PULL_UP = Pin.PULL_UP
    PULL_DOWN = Pin.PULL_DOWN
    def __init__(self, pin, mode=PULL_UP,
                 
                 target_widget=None, target_position=None):

        super().__init__(target_widget=target_widget,target_position=target_position)
        self.mode = mode # 开关的上拉下拉模式
        self.threshold = 0 if mode == self.PULL_UP else 1
        self.pin = Pin(pin, Pin.IN, mode)
        self.press_start_time = 0 # 按下的时间
        self.last_release_time = 0 # 上一次确认触摸释放的时间，用于检测双击
        # 触摸时间参数
        self.click_min_duration = 15    # 最小点击时间：15ms
        self.click_max_duration = 300   # 最大点击时间：300ms
        self.long_press_duration = 500  # 长按阈值：500ms
        # 双击时间间隔
        self.double_click_max_interval = 250  # 上一次释放和下一次开始。点击最大间隔：250ms


    def check_input(self):
        # 非阻塞的触摸状态机
        touch_value = self.pin.value()
        current_time = time.ticks_ms()

        if touch_value == self.threshold:# 触摸按下
            if self.state == self.IDLE:# 第一次检测到按下,将返回 PRESS event
                self.state = self.PRESS
                self.press_start_time = current_time
                return Event(self.PRESS, target_widget=self.target_widget,
                             target_position=self.target_position, timestamp=current_time)
            
            # 检查长按
            press_duration = time.ticks_diff(current_time,self.press_start_time)
            if press_duration >= self.long_press_duration:
                if self.state == self.PRESS:
                    self.state = self.LONG_PRESS
                    return Event(self.LONG_PRESS, target_widget=self.target_widget,
                                target_position=self.target_position, timestamp=current_time)
            
        else:# 触摸释放
            if self.state == self.IDLE:
                return None
            # 长按释放
            if self.state == self.LONG_PRESS:
                self.last_release_time = current_time
                self.state = self.IDLE
                return Event(self.LONG_PRESS_RELEASE, target_widget=self.target_widget,
                             target_position=self.target_position, timestamp=current_time)

            if self.state == self.PRESS:
                # 触摸持续时间
                press_duration = time.ticks_diff(current_time, self.press_start_time)
                # 触摸间隔
                click_interval = time.ticks_diff(self.press_start_time, self.last_release_time)
                # 有效单次点击检测
                if press_duration <= self.click_min_duration : # 持续时长 (不足短按)
                    return
                elif self.click_min_duration < press_duration < self.click_max_duration:
                    # 重置状态
                    self.last_release_time = current_time
                    self.state = self.IDLE
                    # 先判断是否为双击
                    if click_interval <= self.double_click_max_interval:# 是双击
                        return Event(self.DOUBLE_CLICK, target_widget=self.target_widget, 
                                     target_position=self.target_position, timestamp=current_time)
                    else:# 不是双击
                        return Event(self.CLICK, target_widget=self.target_widget, 
                                     target_position=self.target_position, timestamp=current_time)
                else:# 超过短按,不足长按
                    # 重置状态
                    self.last_release_time = current_time
                    self.state = self.IDLE
                    return Event(self.RELEASE, target_widget=self.target_widget, 
                                     target_position=self.target_position, timestamp=current_time)
