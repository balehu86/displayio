# ./core/event.py
class EventType():
    """事件类型枚举"""
    TOUCH_START = 0       # 触摸开始
    TOUCH_MOVE = 1        # 触摸移动
    TOUCH_END = 2         # 触摸结束
    PRESS = 3             # 按下
    RELEASE = 4           # 释放
    CLICK = 5             # 点击
    LONG_PRESS = 6        # 长按
    DOUBLE_CLICK = 7      # 双击
    DRAG_START = 8        # 拖动开始
    DRAG_MOVE = 9         # 拖动中
    DRAG_END = 10         # 拖动结束
    FOCUS = 11            # 获得焦点
    BLUR = 12             # 失去焦点
    VALUE_CHANGE = 13     # 值改变
    SELECTION_CHANGE = 14 # 选择改变
    CUSTOM = 20           # 自定义事件

"""
[Initializing] -> [Pending] -> [Scheduled] -> [Processing] -> [Completed]
                                ↘ [Cancelled]
                                ↘ [Errored]
                                ↘ [Timed Out]

"""

class Event:
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
    def __init__(self, event_type: EventType, data=None, target_position=[0,0], event_queue=[]):
        self.type: EventType = event_type    # 事件类型
        # self.target = target                 # 事件目标对象
        self.target_position = target_position    # 事件目标位置
        self.data = data or {}              # 事件相关数据
        self.timestamp = 0                   # 事件发生时间戳
        self.event_queue = event_queue

        self.status_code = self.STANDY_BY
    def done(self):
        if self in self.event_queue:
            if self.status_code == self.Completed:
                self.event_queue.remove(self)



# event_manager.py
from collections import defaultdict
import _thread
import time

class EventManager:
    """事件管理器"""
    def __init__(self, threaded=False):
        self._listeners = defaultdict(list)  # 事件监听器字典
        self._event_queue = []  # 事件队列
        self._running = False   # 运行状态标志
        self.threaded = threaded
        self._event_lock = _thread.allocate_lock()
        
        if threaded:
            self._start_event_thread()
    
    def _start_event_thread(self):
        """启动事件处理线程"""
        self._running = True
        _thread.start_new_thread(self._event_loop, ())
    
    def _event_loop(self):
        """事件循环"""
        while self._running:
            if self._event_queue:
                with self._event_lock:
                    if self._event_queue:  # Double check after acquiring lock
                        event = self._event_queue.pop(0)
                        self._process_event(event)
            time.sleep(0.01)  # 避免过度占用CPU
    
    def add_event(self, event):
        """添加事件到队列"""
        if not self.threaded:
            self._process_event(event)
            return
            
        with self._event_lock:
            self._event_queue.append(event)
            event.status_code = Event.Scheduled
    
    def add_listener(self, event_type, listener):
        """添加事件监听器
        
        Args:
            event_type: 事件类型（EventType枚举值）
            listener: 监听器函数，接收Event对象作为参数
        """
        self._listeners[event_type].append(listener)
    
    def remove_listener(self, event_type, listener):
        """移除事件监听器"""
        if event_type in self._listeners:
            self._listeners[event_type] = [l for l in self._listeners[event_type] if l != listener]
    
    def _process_event(self, event):
        """处理单个事件"""
        event.status_code = Event.Processing
        
        # 获取该事件类型的所有监听器
        listeners = self._listeners.get(event.type, [])
        
        try:
            # 调用所有监听器
            for listener in listeners:
                try:
                    listener(event)
                except Exception as e:
                    print(f"Error in event listener: {e}")
            event.status_code = Event.Completed
            
        except Exception as e:
            event.status_code = Event.Errored
            print(f"Error processing event: {e}")
        
        finally:
            event.done()  # 清理事件
    
    def clear_events(self):
        """清空事件队列"""
        with self._event_lock:
            for event in self._event_queue:
                event.status_code = Event.Cancelled
            self._event_queue.clear()
    
    def stop(self):
        """停止事件管理器"""
        self._running = False
        self.clear_events()

class TouchEventManager(EventManager):
    """触摸事件管理器"""
    def __init__(self, display, threaded=False):
        super().__init__(threaded)
        self.display = display
        self.last_touch_time = 0
        self.last_touch_pos = None
        self.long_press_threshold = 1000  # 长按阈值（毫秒）
        self.double_click_threshold = 300  # 双击阈值（毫秒）
        
    def handle_touch(self, x, y, touch_type):
        """处理触摸事件
        
        Args:
            x, y: 触摸坐标
            touch_type: 触摸类型（按下/移动/释放）
        """
        current_time = time.ticks_ms()
        
        if touch_type == EventType.TOUCH_START:
            # 创建按下事件
            event = Event(EventType.TOUCH_START, 
                         data={'x': x, 'y': y, 'time': current_time},
                         target_position=[x, y])
            self.add_event(event)
            
            # 检查是否为双击
            if (self.last_touch_pos and 
                time.ticks_diff(current_time, self.last_touch_time) < self.double_click_threshold):
                double_click_event = Event(EventType.DOUBLE_CLICK,
                                         data={'x': x, 'y': y},
                                         target_position=[x, y])
                self.add_event(double_click_event)
            
            self.last_touch_time = current_time
            self.last_touch_pos = (x, y)
            
        elif touch_type == EventType.TOUCH_MOVE:
            # 创建移动事件
            event = Event(EventType.TOUCH_MOVE,
                         data={'x': x, 'y': y, 
                               'last_x': self.last_touch_pos[0] if self.last_touch_pos else x,
                               'last_y': self.last_touch_pos[1] if self.last_touch_pos else y},
                         target_position=[x, y])
            self.add_event(event)
            self.last_touch_pos = (x, y)
            
        elif touch_type == EventType.TOUCH_END:
            # 创建释放事件
            event = Event(EventType.TOUCH_END,
                         data={'x': x, 'y': y},
                         target_position=[x, y])
            self.add_event(event)
            
            # 检查是否为长按
            if (self.last_touch_pos and 
                time.ticks_diff(current_time, self.last_touch_time) >= self.long_press_threshold):
                long_press_event = Event(EventType.LONG_PRESS,
                                       data={'x': x, 'y': y},
                                       target_position=[x, y])
                self.add_event(long_press_event)
            
            # 普通点击事件
            elif self.last_touch_pos:
                click_event = Event(EventType.CLICK,
                                  data={'x': x, 'y': y},
                                  target_position=[x, y])
                self.add_event(click_event)
