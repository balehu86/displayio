# ./display.py
from .core.bitmap import Bitmap
from .core.event import EventType, Event
from .utils.decorator import fps, timeit
import uasyncio # type: ignore
from collections import deque
import time

class Display:
    def __init__(self, width, height, driver=None, fps=1, threaded=True):
        self.width = width
        self.height = height
        self.root = None
        self.driver = driver
        self.fps = fps
        self.event_loop = MainLoop(self, fps)

        self.threaded = threaded

        if threaded and driver is not None:
            import _thread
            # 坐标和尺寸参数 x,y,width,height
            self.thread_dx = 0
            self.thread_dy = 0
            self.thread_width = self.width
            self.thread_height = self.height
            bitmap=Bitmap(self.width,self.height)
            bitmap.fill_rect(0,0,self.width,self.height,0xf81f)
            self.thread_bitmap_memview =memoryview(bitmap.buffer)

            self.lock=_thread.allocate_lock()

            self.thread_running = True
            self.thread_dirty = True
            self.thread = _thread.start_new_thread(self.driver._thread_refresh_wrapper,(self,))

    def set_root(self, widget):
        """设置根组件"""
        self.root = widget
        self.root.layout(dx=0, dy=0, width=self.width, height=self.height)
        self.root.width_resizable = False
        self.root.height_resizable = False
    
    def add_event(self, event):
        """添加事件到事件循环"""
        self.event_loop.post_event(event)

    def run(self,func):
        """启动显示循环"""
        self.event_loop.start(func)
        
    def run_as_async(self):
        self.event_loop.async_start()
        
    def stop(self):
        """停止显示循环和线程"""
        # 停止事件循环
        self.event_loop.stop()
        # 停止线程
        if self.threaded:
            self.thread_running = False
            if hasattr(self, 'thread') and self.thread is not None:
                # 等待线程自然退出
                time.sleep_ms(50)


class MainLoop:
    """事件循环类，管理布局、渲染和事件处理"""
    def __init__(self, display, fps):
        self.display = display
        self.running = False
        self.event_queue = deque([],10)
        self.frame_interval = 1/fps  # default 1 FPS 
        self.last_frame_time = 0
        
    def start(self,func):
        """启动事件循环"""
        self.running = True
        self._run(func)

    def async_start(self):
        """启动异步事件循环"""
        self.running = True
        uasyncio.run(self._async_run())
    
    def stop(self):
        """停止事件循环"""
        self.running = False
        
    def post_event(self, event):
        """添加事件到队列"""
        self.event_queue.append(event)
      
    def _process_events(self):
        """处理所有待处理事件"""
        while self.event_queue and self.running:
            event = self.event_queue.popleft()
            if self.display.root:
                self.display.root.event_handler(event)

    async def _async_process_events(self):
        """异步处理所有待处理事件"""
        while self.event_queue and self.running:
            event = self.event_queue.popleft()
            if self.display.root:
                await self.display.root.async_event_handler(event)
                
    def _update_layout(self):
        """更新布局"""
        if self.display.root and self.display.root._layout_dirty:
            self.display.root.layout(dx=0, dy=0, width=self.display.width, height=self.display.height)
    
    async def _async_update_layout(self):
        """异步更新布局"""
        if self.display.root and self.display.root._layout_dirty:
            await self.display.root.async_layout(dx=0, dy=0, width=self.display.width, height=self.display.height)

    @timeit
    def _update_display(self):
        """更新显示"""
        if self.display.root and self.display.root._dirty:
            self._render_widget(self.display.root)

    async def _async_update_display(self):
        """异步更新显示"""
        if self.display.root and self.display.root._dirty:
            await self._async_render_widget(self.display.root)

    def _render_widget(self, widget):
        """递归渲染widget及其子组件"""
        if widget._dirty:
            if hasattr(widget, 'get_bitmap'):
                bitmap = widget.get_bitmap()
                mem_view = memoryview(bitmap.buffer)
                if self.display.threaded:
                    with self.display.lock:
                        self.display.thread_bitmap_memview = mem_view
                        self.display.thread_dx = widget.dx
                        self.display.thread_dy = widget.dy
                        self.display.thread_width = widget.width
                        self.display.thread_height = widget.height    
                else:
                    self.display.driver.refresh(
                        mem_view, dx=widget.dx, dy=widget.dy, 
                        width=widget.width, height=widget.height)
                    
        for child in widget.children:
            self._render_widget(child)

    async def _async_render_widget(self, widget):
        """递归异步渲染widget及其子组件"""
        if widget._dirty:
            if hasattr(widget, 'get_bitmap'):
                bitmap = await widget.async_get_bitmap() if hasattr(widget, 'async_get_bitmap') else widget.get_bitmap()
                
                if self.display.threaded:
                    with self.display.bitmap_lock:
                        self.display.tem_bitmap = bitmap
                        self.display.tem_dx = widget.dx
                        self.display.tem_dy = widget.dy
                        self.display.tem_width = widget.width
                        self.display.tem_height = widget.height
                else:
                    self.display.driver.refresh(
                        memoryview(bitmap.buffer),
                        dx=widget.dx,
                        dy=widget.dy, 
                        width=widget.width,
                        height=widget.height)
        
        for child in widget.children:
            await self._async_render_widget(child)
    
    def _should_update_frame(self):
        """检查是否应该更新帧"""
        current_time = time.time()
        if current_time - self.last_frame_time >= self.frame_interval:
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
            # 避免过度占用CPU
            time.sleep_ms(1)

    async def _async_run(self):
        """异步运行事件循环"""
        while self.running:
            # 处理事件
            await self._async_process_events()
            
            # 检查是否需要更新帧
            if self._should_update_frame():
                # 异步更新布局
                await self._async_update_layout()
                # 异步更新显示
                await self._async_update_display()
            # 避免过度占用CPU
            await uasyncio.sleep_ms(1)