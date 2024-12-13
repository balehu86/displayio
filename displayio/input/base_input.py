# ./input/base_input.py
from ..core.event import EventType

class Input:
    IDLE = EventType.DEFAULT

    PRESS = EventType.PRESS               # 按下
    LONG_PRESS = EventType.LONG_PRESS     # 长按
    
    RELEASE = EventType.RELEASE           # 释放
    LONG_PRESS_RELEASE = EventType.LONG_PRESS_RELEASE # 长按释放
    CLICK = EventType.CLICK               # 点击
    DOUBLE_CLICK = EventType.DOUBLE_CLICK # 双击
    
    def __init__(self, device, target_widget=None, target_position=None):
        # 统一驱动读取输入为self.input.read()
        self.input = device
        # 目标管理
        self.target_widget = target_widget
        self.target_position = target_position
        # 状态管理
        self.state = self.IDLE
        self.press_start_time = 0 # 按下的时间
        self.last_release_time = 0 # 上一次确认触摸释放的时间，用于检测双击
        # 触摸时间参数
        self.click_min_duration = 15    # 最小点击时间：15ms
        self.click_max_duration = 300   # 最大点击时间：300ms
        self.long_press_duration = 500  # 长按阈值：500ms
        # 双击时间间隔
        self.double_click_max_interval = 250  # 上一次释放和下一次开始。点击最大间隔：250ms

    def check_input(self):
        pass
    
    def set_target_position(self, dx=-1, dy=-1):
        self.target_position = [dx, dy]

    def set_target_widget(self,widget):
        self.target_widget = widget

