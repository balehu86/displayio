# ./core/event.py
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set

class EventType(Enum):
    """事件类型枚举"""
    TOUCH_START = auto()      # 触摸开始
    TOUCH_MOVE = auto()       # 触摸移动
    TOUCH_END = auto()        # 触摸结束
    PRESS = auto()            # 按下
    RELEASE = auto()          # 释放
    CLICK = auto()            # 点击
    LONG_PRESS = auto()       # 长按
    DOUBLE_CLICK = auto()     # 双击
    DRAG_START = auto()       # 拖动开始
    DRAG_MOVE = auto()        # 拖动中
    DRAG_END = auto()         # 拖动结束
    FOCUS = auto()            # 获得焦点
    BLUR = auto()             # 失去焦点
    VALUE_CHANGE = auto()     # 值改变
    SELECTION_CHANGE = auto() # 选择改变
    CUSTOM = auto()           # 自定义事件

class Event:
    Initializing = -1 # 初始化中
    Pending = 0 # 准备中 
    Scheduled = 1 # 已调度
    Processing = 2 # 正在处理
    Completed = 10 # 已完成
    Errored = 99 # 出错
    Cancelled = 200 # 已取消
    Retrying = 201 # 重试中
    Blocked = 300 # 阻塞中

    Timed_Out = 999 # 超时
    """
    [Initializing] -> [Pending] -> [Scheduled] -> [Processing] -> [Completed]
                                  ↘ [Cancelled]
                                  ↘ [Errored]
                                  ↘ [Timed Out]

    """
    """事件基类"""
    def __init__(self, event_type: EventType, target=None, data=None):
        self.type: EventType = event_type    # 事件类型
        self.target = target                 # 事件目标对象
        self.target_position = [int,int]    # 事件目标位置
        self.current_target = target         # 当前处理事件的对象
        self.data = data or {}              # 事件相关数据
        self.timestamp = 0                   # 事件发生时间戳

        self.status_code = self.STANDY_BY

        self._propagation_stopped = False    # 是否停止传播
        self._immediate_propagation_stopped = False  # 是否立即停止传播
        self._default_prevented = False      # 是否阻止默认行为
        
    # def stop_propagation(self):
    #     """停止事件冒泡"""
    #     self._propagation_stopped = True
        
    # def stop_immediate_propagation(self):
    #     """立即停止事件传播"""
    #     self._immediate_propagation_stopped = True
        
    # def prevent_default(self):
    #     """阻止默认行为"""
    #     self._default_prevented = True

    def done(self):
        self.status_code = self.DONE