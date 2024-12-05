# ./core/loop.py
from collections import deque
import time
from machine import Timer # type: ignore
from ..utils.decorator import fps, timeit, measure_iterations

class MainLoop:
    """事件循环类，管理布局、渲染和事件处理"""
    def __init__(self, display, fps):
        self.display = display
        self.running = False
        self.event_queue = deque([],10)
        self.frame_interval = 1/fps  # default 5 FPS 
        self.last_frame_time = 0
        self.timer = Timer(0)
        
    def start(self,func):
        """启动事件循环"""
        self.running = True
        self.timer.init(mode=Timer.PERIODIC,freq=500, callback=self._check_input)
        try:
            if self.display.show_fps:
                self._run_with_fps(func)
            else:
                self._run(func)
        except KeyboardInterrupt:
            print("捕获到键盘中断，正在退出...")
            self.stop()
        except Exception as e:
            print(e)
    
    def stop(self):
        """停止事件循环"""
        self.running = False
        self.timer.deinit()
        
    def post_event(self, event):
        """添加事件到队列"""
        self.event_queue.append(event)

    def _process_events(self):
        """处理所有待处理事件"""
        while self.event_queue:
            event = self.event_queue.popleft()
            if self.display.root:
                self.display.root.event_handler(event)

    def _check_input(self,timer):
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
        """递归渲染widget及其子组件"""
        if widget._dirty:
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
                    self.display.output.refresh(
                        mem_view, dx=widget.dx, dy=widget.dy, 
                        width=widget.width, height=widget.height)
            widget._dirty = False            
        for child in widget.children:
            self._render_widget(child)
    
    def _should_update_frame(self):
        """检查是否应该更新帧"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_frame_time) >= self.frame_interval*1000:
            self.last_frame_time = current_time
            return True
        return False
        
    def _run(self,func):        
        """运行事件循环"""
        self._update_layout()
        while self.running:
            func()
            # 处理事件
            self._process_events()
            # 检查是否需要更新帧
            if self._should_update_frame():
                # 更新布局
                self._update_layout()
                # 更新显示
                self._update_display()
            # # 避免过度占用CPU
            time.sleep_ms(1)

    @measure_iterations  
    def _run_with_fps(self,func):
        func()
        # 处理事件
        self._process_events()
        # 更新布局
        self._update_layout()
        # 更新显示
        self._update_display()

    