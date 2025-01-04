# ./core/event.py

class EventType:
    """事件类型枚举"""
    __slots__ = ()

    DEFAULT = 0           # No event
    IDLE = 0

    # 触摸相关事件
    TOUCH_START = 'TOUCH_START'  # 触摸开始
    TOUCH_MOVE = 'TOUCH_MOVE'    # 触摸移动
    TOUCH_END = 'TOUCH_END'      # 触摸结束
    # 按键相关事件
    PRESS = 'PRESS'       # 按下
    RELEASE = 'RELEASE'   # 释放
    LONG_PRESS_RELEASE = 'LONG_PRESS_RELEASE' # 长按释放
    CLICK = 'CLICK'       # 点击
    LONG_PRESS = 'LONG_PRESS'       # 长按
    DOUBLE_CLICK = 'DOUBLE_CLICK'   # 双击
    # 拖动相关事件
    DRAG_START = 10       # 拖动开始,检测逻辑类似长按
    DRAG_MOVE = 11        # 拖动中
    DRAG_END = 12         # 拖动结束
    # 焦点相关事件
    FOCUS = 'FOCUS'       # 获得焦点
    UNFOCUS = 'UNFOCUS'   # 失去焦点
    FOCUS_NEXT = 'FOCUS_NEXT' # 下一个焦点
    FOCUS_PREV = 'FOCUS_PREV' # 上一个焦点
    # 值和选择相关事件
    VALUE_CHANGE = 15     # 值改变
    SELECTION_CHANGE = 16 # 选择改变
    # 旋转编码器相关事件
    ROTATE = 'ROTATE'         # 旋转
    ROTATE_LEFT = 'ROTATE_LEFT'      # 左旋
    ROTATE_RIGHT = 'ROTATE_RIGHT'    # 右旋
    ROTATE_TICK = 'ROTATE_TICK'      # 一个tick
    ROTATE_TICK_LEFT = 'ROTATE_TICK_LEFT'  # 一个左旋tick
    ROTATE_TICK_RIGHT = 'ROTATE_TICK_RIGHT'# 一个右旋tick
    # 滚动
    SCROLL = 'SCROLL'           # 滚动
    SCROLL_UP = 'SCROLL_UP'     # 向上滚动
    SCROLL_DOWN = 'SCROLL_DOWN' # 向下滚动
    SCROLL_RIGHT = 'SCROLL_RIGHT' # 向右滚动
    SCROLL_LEFT = 'SCROLL_LEFT' # 向左滚动


    CUSTOM = 99           # 自定义事件
"""
[Initializing] -> [Pending] -> [Scheduled] -> [Processing] -> [Completed]
                                ↘ [Cancelled]
                                ↘ [Errored]
                                ↘ [Timed Out]
"""
class Event:
    __slots__ = ('type', 'target_widget', 'target_position', 'data',
                'timestamp', 'priority', 'status_code')
    
    Initializing = -1 # 初始化中
    Pending = 0       # 准备中 
    Scheduled = 1     # 已调度
    Processing = 2    # 正在处理
    Completed = 10    # 已完成
    Errored = 99      # 出错
    Cancelled = 200   # 已取消
    Retrying = 201    # 重试中
    Blocked = 300     # 阻塞中
    Timed_Out = 999   # 超时

    """事件基类"""
    def __init__(self, event_type: EventType, data=None, target_position=None, target_widget=None, timestamp=0):
        self.type: EventType = event_type    # 事件类型
        if target_position is None and target_widget is None:
            raise ValueError("事件必须指定目标位置或目标组件")
        self.target_widget = target_widget   # 事件目标对象
        self.target_position = target_position    # 事件目标位置
        self.data = data             # 事件相关数据
        self.timestamp = timestamp                   # 事件发生时间戳
        self.priority = 10  # 事件优先级
        self.status_code = self.Initializing

    def is_handled(self) -> bool:
        """ 返回event是否已被处理 """
        return self.status_code == self.Completed
        
    def is_catched(self) -> bool:
        """返回event是否被捕获"""
        return self.status_code == self.Processing
    
    def handle(self) -> None:
        """将事件标记为已完成"""
        self.status_code = self.Completed

    def catch(self) -> None:
        """将事件标记为已捕获"""
        self.status_code = self.Processing
    
    def __lt__(self, other):
        """比较任务，优先按时间排序；时间相同时按优先级排序。"""
        if self.timestamp == other.timestamp:
            return self.priority < other.priority
        return self.timestamp < other.timestamp

