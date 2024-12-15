# ./core/loop.py
from collections import deque
import time
from machine import Timer # type: ignore
# from ..utils.decorator import fps, timeit, measure_iterations

class MainLoop:
    """事件循环类，管理布局、渲染和事件处理"""
    def __init__(self, display):
        self.display = display
        # 标记是否运行
        self.running = False
        # 事件队列，最多存10个事件
        self.event_queue = deque([],10,1)
        # 检查是否到刷新屏幕的时间。
        if self.display.fps > 0 :
            self.frame_interval = 1/self.display.fps
        else :
            self.frame_interval = 0.001  # 1000 FPS
        # 记录上次刷新屏幕的时间
        self.last_frame_time = 0
        self.frame_count = 0  # 新增：帧计数器
        self.last_fps_time = time.ticks_ms()  # 新增：上次计算FPS的时间
        # 检查输入的定时器
        self.input_timer = Timer(0)
        # 确认 局部刷新还是全局刷新
        if self.display.partly_refresh:
            self.update_display = self._update_display
        else:
            self.update_display = self._update_display_fully
        
    def start(self,func):
        """启动事件循环"""
        self.running = True
        # 初始化输入检测定时器
        self.input_timer.init(mode=Timer.PERIODIC,freq=500, callback=self._check_input)
        try:
            self._run(func)
        except KeyboardInterrupt:
            print("捕获到键盘中断，正在退出...")
            self.stop()
            print("已退出。")
    
    def stop(self):
        """停止事件循环"""
        self.running = False
        self.input_timer.deinit()
        
    def post_event(self, event):
        """添加事件到队列"""
        self.event_queue.append(event)

    def _process_events(self):
        """处理所有待处理事件"""
        while self.event_queue:
            event = self.event_queue.popleft()
            if self.display.root:
                self.display.root.event_handler(event)

    def _check_input(self,timer_object):
        for device in self.display.inputs:
            event = device.check_input()
            if event is not None:
                self.post_event(event)

    def _update_layout(self):
        """更新布局"""
        if self.display.root._layout_dirty:
            self.display.root.layout(dx=0, dy=0, width=self.display.width, height=self.display.height)

    def _update_display(self):
        """更新显示"""
        if self.display.root._dirty:
            self._render_widget(self.display.root)

    def _render_widget(self, widget):
        """递归渲染widget及其子组件
                任何具有get_bitmap的组件将被视为组件树的末端
        """
        if widget._dirty:
            widget._dirty = False
            if hasattr(widget, 'get_bitmap'):
                bitmap = widget.get_bitmap()
                mem_view = memoryview(bitmap.buffer)
                if self.display.threaded:
                    with self.display.lock:
                        self.display.thread_args['bitmap_memview'] = mem_view
                        self.display.thread_args['dx'] = widget.dx
                        self.display.thread_args['dy'] = widget.dy
                        self.display.thread_args['width'] = widget.width
                        self.display.thread_args['height'] = widget.height   
                else:
                    self.display.output.refresh(mem_view, dx=widget.dx, dy=widget.dy, width=widget.width, height=widget.height)
                return # 任何具有get_bitmap的组件将被视为组件树的末端

        for child in widget.children:
            self._render_widget(child)
    
    def _update_display_fully(self):
        """全屏刷新"""
        if self.display.root._dirty:
            self._render_widget_fully(self.display.root)
        mem_view = memoryview(self.display.root._bitmap.buffer)
        self.display.output.refresh(mem_view, dx=0, dy=0, width=self.display.width, height=self.display.height)

    def _render_widget_fully(self, widget):
        """绘制整个屏幕的buffer"""
        if widget._dirty or self.widget_in_dirty_area(widget):
            widget._dirty = False
            if hasattr(widget, 'get_bitmap'):
                bitmap = widget.get_bitmap()
                self.display.root._bitmap.blit(bitmap, dx=widget.dx, dy=widget.dy)
                return
        for child in widget.children:
            self._render_widget_fully(child)

    def _should_update_frame(self):
        """检查是否应该更新帧"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_frame_time) >= self.frame_interval*1000:
            self.last_frame_time = current_time
            return True
        return False
        
    def _run(self,func):        
        """运行事件循环"""
        func()
        show_fps = self.display.show_fps
        while self.running:
            # 处理事件
            self._process_events()
            # 检查是否需要更新帧
            if self._should_update_frame():
                # 更新布局
                self._update_layout()
                # 更新显示
                self.update_display()
                # 新增：帧数计数和FPS计算
                if show_fps:
                    self.frame_count += 1
                    self._calculate_fps()

    def _calculate_fps(self):
        """计算并打印每秒帧数"""
        current_time = time.ticks_ms()
        elapsed_time = time.ticks_diff(current_time, self.last_fps_time)

        if elapsed_time >= 1000:  # 每秒计算一次
            fps = 1000 * self.frame_count / elapsed_time
            print(f"FPS: {fps:.2f}")
            # 重置计数器
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def widget_in_dirty_area(self, widget):
        """
        判断widget是否和dirty_area有重叠。
        """
        # 获取widget的边界
        x2_min, y2_min, width2, height2 = widget.dx, widget.dy, widget.width, widget.height

        for dirty_area in widget.parent.dirty_area_list:
            # 获取dirty_area的边界
            x1_min, y1_min, width1, height1 = dirty_area

            x1_max = x1_min + width1 - 1  # 脏区域的右边界
            y1_max = y1_min + height1 - 1 # 脏区域的上边界

            x2_max = x2_min + width2 - 1  # widget的右边界
            y2_max = y2_min + height2 - 1 # widget的上边界

            # 检查是否有交集
            if x1_min > x2_max or x2_min > x1_max:
                return False  # 在水平轴上没有交集
            if y1_min > y2_max or y2_min > y1_max:
                return False  # 在垂直轴上没有交集

            return True  # 存在交集