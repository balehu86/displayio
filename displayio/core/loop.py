# ./core/loop.py
from collections import deque
import time
from ..utils.decorator import fps, timeit, measure_iterations

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

    def start_with_fps(self,func):
        self.running = True
        self._run_with_fps(func)

    # def async_start(self,func):
    #     """启动异步事件循环"""
    #     self.running = True
    #     loop = uasyncio.new_loop()
    #     loop.run_until_complete(self._async_run(func))
    
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

    # async def _async_process_events(self):
    #     """异步处理所有待处理事件"""
    #     while self.running:
    #         while self.event_queue:
    #             event = self.event_queue.popleft()
    #             if self.display.root:
    #                 await self.display.root.async_event_handler(event)
    #             await uasyncio.sleep_ms(1)
    #         await uasyncio.sleep_ms(1)

    def _check_input(self):
        for device in self.display.inputs:
            event = device.check_input()
            if event is not None:
                self.post_event(event)

    def _update_layout(self):
        """更新布局"""
        if self.display.root and self.display.root._layout_dirty:
            self.display.root.layout(dx=0, dy=0, width=self.display.width, height=self.display.height)
    
    # async def _async_update_layout(self):
    #     """异步更新布局"""
    #     while self.running:
    #         if self.display.root and self.display.root._layout_dirty:
    #             await self.display.root.async_layout(dx=0, dy=0, width=self.display.width, height=self.display.height)
    #         uasyncio.sleep_ms(1)
    def _update_display(self):
        """更新显示"""
        if self.display.root and self.display.root._dirty:
            self._render_widget(self.display.root)

    # async def _async_update_display(self):
    #     """异步更新显示"""
    #     while self.running:
    #         if self.display.root and self.display.root._dirty:
    #             await self._async_render_widget(self.display.root)

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

    # async def _async_render_widget(self, widget):
    #     """递归异步渲染widget及其子组件"""
    #     if widget._dirty:
    #         if hasattr(widget, 'get_bitmap'):
    #             bitmap = await widget.async_get_bitmap() if hasattr(widget, 'async_get_bitmap') else widget.get_bitmap()
                
    #             if self.display.threaded:
    #                 with self.display.bitmap_lock:
    #                     self.display.tem_bitmap = bitmap
    #                     self.display.tem_dx = widget.dx
    #                     self.display.tem_dy = widget.dy
    #                     self.display.tem_width = widget.width
    #                     self.display.tem_height = widget.height
    #             else:
    #                 self.display.output.refresh(
    #                     memoryview(bitmap.buffer),
    #                     dx=widget.dx,
    #                     dy=widget.dy, 
    #                     width=widget.width,
    #                     height=widget.height)
        
    #     for child in widget.children:
    #         await self._async_render_widget(child)
    
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
            self._check_input()
            self._process_events()
            # 检查是否需要更新帧
            if self._should_update_frame():
                # 更新布局
                self._check_input()
                self._process_events()
                self._update_layout()
                # 更新显示
                self._check_input()
                self._process_events()
                self._update_display()
            # # 避免过度占用CPU
            time.sleep_ms(10)

    # async def _async_run(self, func=None):
    #     try:
    #         while self.running:
    #             # Execute custom function if provided
    #             if func:
    #                 await self._safe_async_exec(func)
                
    #             # Process all pending events
    #             await self._async_process_events()
                
    #             # Check if it's time to update the frame based on FPS
    #             if self._should_update_frame():
    #                 # Perform layout update if needed
    #                 if self.display.root and self.display.root._layout_dirty:
    #                     await self._async_update_layout()
                    
    #                 # Process any events that might have been generated during layout update
    #                 await self._async_process_events()
                    
    #                 # Update display rendering
    #                 await self._async_update_display()
                    
    #                 # Process any events that might have been generated during rendering
    #                 await self._async_process_events()
                
    #             # Yield control to prevent blocking and allow other coroutines
    #             await uasyncio.sleep_ms(1)
        
    #     except Exception as e:
    #         print(f"Error in async event loop: {e}")
    #         self.running = False
    #     finally:
    #         self.running = False
    @measure_iterations  
    def _run_with_fps(self,func):
        func()
        # 处理事件
        self._check_input()
        self._process_events()
        # 检查是否需要更新帧
        # 更新布局
        self._check_input()
        self._process_events()
        self._update_layout()
        self._process_events()
        # 更新显示
        self._check_input()
        self._process_events()
        self._update_display()
        self._process_events()
    
    # async def _safe_async_exec(self, func):
    #     try:
    #         if hasattr(func(), '__await__'):
    #             await func()
    #         else:
    #             func()
    #     except Exception as e:
    #         print(f"Error executing user function: {e}")