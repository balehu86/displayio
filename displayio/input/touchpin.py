from machine import TouchPad,Pin # type: ignore
import time
from .base_input import Input
from ..core.event import Event

class TouchPin(Input):
    def __init__(self, pin, touch_threshold=100000,
                 
                 target_widget=None, target_position=None):

        super().__init__(target_widget=target_widget,target_position=target_position)
        self.touch_pin = TouchPad(Pin(pin))
        self.press_start_time = 0 # 按下的时间
        self.last_release_time = 0 # 上一次确认触摸释放的时间，用于检测双击
        # 触摸时间参数
        self.click_min_duration = 15    # 最小点击时间：15ms
        self.click_max_duration = 300   # 最大点击时间：300ms
        self.long_press_duration = 500  # 长按阈值：500ms
        # 双击时间间隔
        self.double_click_max_interval = 250  # 上一次释放和下一次开始。点击最大间隔：250ms
        # 触摸数据阈值
        self.touch_threshold = touch_threshold

    def check_input(self):
        # 非阻塞的触摸状态机
        touch_value = self.touch_pin.read()
        current_time = time.ticks_ms()

        if touch_value > self.touch_threshold:# 触摸按下
            if self.state == self.IDLE:# 第一次检测到按下,将返回 PRESS event
                self.state = self.PRESS
                self.press_start_time = current_time
                return Event(self.PRESS, target_widget=self.target_widget,
                             target_position=self.target_position)
            
            # 检查长按
            press_duration = time.ticks_diff(current_time,self.press_start_time)
            if press_duration >= self.long_press_duration:
                if self.state != self.LONG_PRESS:
                    self.state = self.LONG_PRESS
                    return Event(self.LONG_PRESS, target_widget=self.target_widget,
                                target_position=self.target_position)
            
        else:# 触摸释放
            if self.state == self.IDLE:
                return None
            # 长按释放
            if self.state == self.LONG_PRESS:
                self.last_release_time = current_time
                self.state = self.IDLE
                return Event(self.LONG_PRESS_RELEASE, target_widget=self.target_widget,
                             target_position=self.target_position)

            if self.state == self.PRESS:
                # 触摸持续时间
                press_duration = time.ticks_diff(current_time, self.press_start_time)
                # 触摸间隔
                click_interval = time.ticks_diff(self.press_start_time, self.last_release_time)
                # 重置状态
                self.last_release_time = current_time
                self.state = self.IDLE
                # 有效单次点击检测
                if self.click_min_duration < press_duration < self.click_max_duration:
                    # 先判断是否为双击
                    if click_interval <= self.double_click_max_interval:# 是双击
                        return Event(self.DOUBLE_CLICK, target_widget=self.target_widget, 
                                     target_position=self.target_position)
                    else:# 不是双击
                        return Event(self.CLICK, target_widget=self.target_widget, 
                                     target_position=self.target_position)
                else: # 持续时长 (超过短按,不足长按) 或 (不足短按)
                    return Event(self.RELEASE, target_widget=self.target_widget, 
                                     target_position=self.target_position)
