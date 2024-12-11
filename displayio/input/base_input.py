# ./input/base_input.py
from ..core.event import EventType

class Input:
    IDLE = EventType.NORMAL

    PRESS = EventType.PRESS               # 按下
    RELEASE = EventType.RELEASE           # 释放
    LONG_PRESS_RELEASE = EventType.LONG_PRESS_RELEASE # 长按释放

    CLICK = EventType.CLICK               # 点击
    LONG_PRESS = EventType.LONG_PRESS     # 长按
    DOUBLE_CLICK = EventType.DOUBLE_CLICK # 双击
    
    def __init__(self, device, target_widget=None, target_position=None):
        # 统一驱动读取输入为self.input.read()
        self.input = device
        # 目标管理
        if target_position is None and target_widget is None:
            raise ValueError("TouchPin必须指定作用的目标位置或目标组件")
        self.target_widget = target_widget
        self.target_position = target_position
        # 状态管理
        self.state = self.IDLE
        self.press_start_time = 0 # 按下的时间
        self.last_click_time = 0 # 上一次确认触摸的事间，一般用于检测双击
        # 触摸时间参数
        self.click_min_duration = 8     # 最小点击时间：8ms
        self.click_max_duration = 400   # 最大点击时间：400ms
        self.long_press_duration = 500  # 长按阈值：500ms
        # 双击时间间隔
        self.double_click_max_interval = 300  # 两次点击最大间隔：300ms
    def check_input(self):
        pass