# ./display.py
from .core.bitmap import Bitmap
from .core.event import Event # type hint
from .core.logging import logger
from .core.dirty import DirtySystem
from .widget.widget import Widget
from .container.container import Container # type hint
from .input.base_input import Input # type hint

import time

class Display:
    __slots__ = ('width', 'height', 'root', 'output', 'inputs',
                 'soft_timer', 'fps', 'show_fps', 'partly_refresh', 'show_dirty_are',
                 'loop')

    def __init__(self, log_level = logger.INFO, config_file:str=None,
                 width:int=0, height:int=0, root:Container=None, show_dirty_are:bool=False,
                 output=None, inputs=[], fps:int=0, soft_timer:bool=True,
                 show_fps:bool=False, partly_refresh:bool=False):
        """显示器主程序

        Args:
            width (int): 显示器宽度
            height (int): 显示器高度
            root (_type_, optional): 元素树的根节点,通常为容器. Defaults to None.
            output (_type_, optional): 输出驱动程序接口,将调用output.refresh()刷新buffer. Defaults to None.
            inputs (list, optional): 输入设备,将调用input.check_input()检查输入设备状态. Defaults to [].
            fps (int, optional): 目标FPS大小,fps <=0 时,不限制刷新速度. Defaults to 0.
            soft_timer (bool, optional): 是否采用软件计时器调用输入设备检测. Defaults to True.
            show_fps (bool, optional): 是否print FPS 和 IPS(input per second). Defaults to False.
            partly_refresh (bool, optional): 是否开启局部刷新. Defaults to True.
            config_file (str, optional): display实例初始化配置json文件的目录. Defaults to None.
        """
        logger.setLevel(log_level)
        logger.debug("Initializing display...")
        # 屏幕尺寸和根节点
        self.width = width
        self.height = height
        self.root = root
        # 输入输出设备
        self.output = output
        self.inputs = inputs
        # 输入设备是否采用软件定时器
        self.soft_timer = soft_timer
        # 刷新频率和出否在命令行输出fps信息
        self.fps = fps # 默认0，不限制刷新频率
        self.show_fps = show_fps # 是否显示刷新率
        self.show_dirty_area = show_dirty_are
        # 局部刷新
        self.partly_refresh = partly_refresh
        # 设置文件
        if config_file is not None:
            import json
            f=open(config_file, 'r')
            config=json.load(f)
            for key, value in config.items():
                setattr(self, key, value)
            f.close()
        # 创建事件循环
        self.loop = MainLoop(self)
        logger.debug("Display initialized.")

    def set_root(self, widget:Container):
        """设置根组件"""
        widget.resize(width=self.width, height=self.height, force=True)
        widget.width_resizable, widget.height_resizable = False, False
        self.root = widget
        # 传递root的dirty_system到事件循环
        self.loop.dirty_system=widget.dirty_system
        # 将root的dirty_system设置为全局共享实例
        DirtySystem._instances['default'] = widget.dirty_system
        # 如果局部刷新,在root 部件创建一个全屏framebuff。
        if not self.partly_refresh:
            widget._bitmap = Bitmap(widget, transparent_color=widget.transparent_color)
            widget._bitmap.init(dx=0, dy=0)

    def add_event(self, event:Event):
        """添加事件到事件循环"""
        self.loop._post_event(event)

    def add_input_device(self,*device:Input):
        """添加输入设备"""
        self.inputs.extend(device)

    def run(self,func:function):
        """启动显示循环"""
        self.loop.run(func)

    def stop(self):
        """停止显示循环和线程"""
        # 停止事件循环
        self.loop.stop()


from collections import deque
from heapq import heappush, heappop  # 用于优先级队列管理任务
from machine import Timer # type: ignore
from .utils.decorator import timeit
import gc

class MainLoop:
    __slots__ = ('display', 'dirty_system', 'dirty_bitmap', 'running', 'event_queue', 'task_queue',
                 'frame_interval', 'last_frame_time', 'frame_count', 'last_fps_time'
                 'input_count', 'last_input_time', 'input_timer')

    """事件循环类，管理布局、渲染和事件处理"""
    def __init__(self, display:Display):
        self.display = display
        # 脏区域全局共享实例
        self.dirty_system:DirtySystem = None
        self.dirty_bitmap = Bitmap()
        # 标记是否运行
        self.running = False
        # 事件队列，最多存10个事件
        self.event_queue = deque([],10,1)
        # 优先级队列存储任务
        self.task_queue = []

        #FPS相关计算移到独立方法
        self._init_fps_settings()
        # 输入检测相关初始化移到独立方法
        self._init_input_settings()

    def _init_fps_settings(self):
        """初始化FPS相关设置"""
        self.frame_interval = 1000 // self.display.fps if self.display.fps > 0 else 1
        self.last_frame_time = time.ticks_ms()
        self.frame_count = 0
        self.last_fps_time = time.ticks_ms()

    def _init_input_settings(self):
        """初始化输入检测相关设置"""
        self.input_count = 0
        self.last_input_time = time.ticks_ms()
        if not self.display.soft_timer:
            self.input_timer = Timer(0)

    def stop(self):
        """停止事件循环"""
        self.running = False
        if not self.display.soft_timer:
            self.input_timer.deinit()

    def _post_event(self, event:Event=None):
        """添加事件到队列"""
        if event is not None:
            self.event_queue.append(event)

        # 新增：输入计数和IPS计算
        if self.display.show_fps:
            self._calculate_ips()

    def process_event(self):
        """处理待处理事件"""
        while self.event_queue:
            event = self.event_queue.popleft()
            logger.debug(f"Processing event: {event.type}")
            if event.target_widget: # 有目标widget,则在目标widget开始冒泡
                self.add_task(event.target_widget.bubble,one_shot=True,args=(event,))
            else:
                self.add_task(self.display.root.bubble,one_shot=True,args=(event,))

    def _hardware_check_input(self, *args):
        # 如果采用硬件定时器,此函数需要接受一个timer的实例作为参数,如果采用软件定时器,则不需要.
        for device in self.display.inputs:
            event = device.check_input()
            self._post_event(event)

    def _calculate_ips(self):
        """计算并打印每秒检查输入轮次数"""
        self.input_count += 1
        current_time = time.ticks_ms()
        elapsed_time = time.ticks_diff(current_time, self.last_input_time)
        if elapsed_time >= 1000:  # 每秒计算一次
            ips = 1000 * self.input_count / elapsed_time / len(self.display.inputs)
            logger.info(f"IPS: {ips:.1f}")
            # 重置计数器
            self.input_count = 0
            self.last_input_time = current_time

    def update_layout(self):
        """更新布局.在这一步,Widget会被添加进脏系统的dirty_widget"""
        for system in self.dirty_system._instances.values():
            if system.layout_dirty:
                logger.debug(f"Updating {system.name} layout...")
                if system.name == 'default':
                    self.display.root.layout(dx=0, dy=0, width=self.display.width, height=self.display.height)
                else:
                    widget = system.widget
                    widget.layout(dx=widget.dx, dy=widget.dy, width=widget.width, height=widget.height)
                system.layout_dirty = False

    def _render_widget(self, widget:Container|Widget, area):
        """ 递归渲染widget及其子组件,任何具有get_bitmap的组件将被视为组件树的末端"""
        if widget.widget_in_dirty_area(area):
            if hasattr(widget, 'get_bitmap'): # 叶子widget
                bitmap = widget.get_bitmap()
                self.dirty_bitmap.blit(bitmap, dx=bitmap.dx-area[0], dy=bitmap.dy-area[1])
            else: # 容器节点
                if widget.background.color is not None:
                    self.dirty_bitmap.fill(widget.background.color)
                else:
                    self.dirty_bitmap.blit(bitmap, dx=bitmap.dx, dy=bitmap.dy)
                    raise ValueError
                for child in widget.children:
                    self._render_widget(child, area)

    def update_display(self):
        """更新显示
        绘制系统解释：
            每个独立绘制系统(update_display类似方法)只绘制自己的脏系统的dirty_widget,
                需要保留独立绘制系统的(例如scroll_box)需要实现自己的绘制方法(scroll_box.update_child_bitamp).
                同时,独立的绘制系统也只处理自己独立的脏系统的dirty_widget绘制
        """
        if self.dirty_system.dirty: # 如果有脏区域则出发刷新
            # 先重绘 脏widget的bitmap
            for dirty_widget in self.dirty_system.dirty_widget:
                if hasattr(dirty_widget, 'draw'):
                    dirty_widget.draw()
            self.dirty_system.clear_widget()

            # 如果显示脏区域
            if self.display.show_dirty_area:
                for dirty_area in self.dirty_system.area:
                    dx, dy = dirty_area[0], dirty_area[1]
                    width, height = dirty_area[2]-dx+1, dirty_area[3]-dy+1
                    if self.display.partly_refresh: # 如果局部刷新
                        self.display.output.fill_rect(dx,dy,width,height,0xf81f)
                    else: # 如果全局刷新
                        self.display.root._bitmap.fill_rect(dx,dy,width,height,0xf81f)
                if not self.display.partly_refresh: # 全局刷新
                    self.display.output.refresh(self.display.root._bitmap.buffer, dx=0, dy=0, width=self.display.width, height=self.display.height)
                time.sleep_ms(500)

            # 绘制和刷新
            for dirty_area in self.dirty_system.area:
                # 先初始化dirty_bitmap
                dx, dy = dirty_area[0], dirty_area[1]
                width, height = dirty_area[2]-dx+1, dirty_area[3]-dy+1
                self.dirty_bitmap.init(dx=dx, dy=dy, width=width, height=height)
                self._render_widget(self.display.root, dirty_area)
                if self.display.partly_refresh: # 如果局部刷新
                    self.display.output.refresh(self.dirty_bitmap.buffer, dx=dx, dy=dy, width=width, height=height)
                else:
                    self.display.root._bitmap.blit(self.dirty_bitmap, dx=self.dirty_bitmap.dx, dy=self.dirty_bitmap.dy)
            if not self.display.partly_refresh: # 如果全局刷新
                self.display.output.refresh(self.display.root._bitmap.buffer, dx=0, dy=0, width=self.display.width, height=self.display.height)

            # 绘制刷新完后，清除脏区域
            self.dirty_system.clear()

        # 帧数计数和FPS计算
        if self.display.show_fps:
            self._calculate_fps()

    def _calculate_fps(self):
        """计算并打印每秒帧数"""
        self.frame_count += 1
        current_time = time.ticks_ms()
        elapsed_time = time.ticks_diff(current_time, self.last_fps_time)

        if elapsed_time >= 1000:  # 每秒计算一次
            fps = 1000 * self.frame_count / elapsed_time
            logger.info(f"FPS: {fps:.1f}")
            # 重置计数器
            self.frame_count = 0
            self.last_fps_time = current_time

    def add_task(self, callback, period=0, priority=10, one_shot=False, on_complete=None, args=(), kwargs={}):
        """添加一个新任务"""
        task = Task(callback, period, priority, one_shot, on_complete, args, kwargs)
        heappush(self.task_queue, task)

    def run(self,func:function):
        """运行调度器"""
        try:
            self.running = True
            if not self.display.soft_timer:
                # 初始化输入检测定时器
                self.input_timer.init(mode=Timer.PERIODIC,freq=550, callback=self._hardware_check_input)
            self._init_tasks(func) # 添加初始函数
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("捕获到键盘中断，正在退出...")
            self.stop()
        except Exception as e:
            logger.exception("发生异常，正在退出...", exc=e)
            self.stop()

    def _init_tasks(self, func:function):
        """初始化所有任务"""
        # 添加初始函数
        self.add_task(func, one_shot=True)
        # 添加垃圾收集任务
        self.add_task(gc.collect, period=10000)
        # 添加输入检测任务
        if self.display.soft_timer:
            for device in self.display.inputs:
                self.add_task(device.check_input, period=2, priority=1, on_complete=self._post_event)

        # 添加核心任务
        # 添加事件冒泡 
        self.add_task(self.process_event, period=10)
        # 添加布局系统
        self.add_task(self.update_layout, period=self.frame_interval, priority=9)
        # 添加刷新系统
        self.add_task(self.update_display, period=self.frame_interval, priority=10)

    def _main_loop(self):
        """主循环实现"""
        while self.running:
            current_time = time.ticks_ms() # 获取当前时间
            task = self.task_queue[0] # 查看队列中的最高优先级任务
            time_to_next_run = time.ticks_diff(task.next_run, current_time) # 计算距离下次运行的时间
            if time_to_next_run > 0:
                # 距离下一次运行还有时间，动态休眠
                time.sleep_ms(min(time_to_next_run, 1)) # 最多休眠1ms
                continue
            # 移除任务并执行
            heappop(self.task_queue)
            if task.execute():  # 执行任务,任务完成返回False，未完成返回True
                # 考虑任务执行时间，避免任务堆积
                execution_time = time.ticks_diff(time.ticks_ms(), current_time)
                # 更新下次运行时间
                task.next_run = time.ticks_add(current_time, max(task.period, execution_time))
                heappush(self.task_queue, task)  # 重新放入队列

class Task:
    """表示一个任务"""
    __slots__ = ('generator', 'callback', 'period', 'priority', 'one_shot', 'on_complete', 'args', 'kwargs', 'next_run')

    def __init__(self, callback,
                 period=0, priority=10,
                 one_shot=False, on_complete=None,
                 args=(), kwargs={}):
        """
        Args:
            callback (function): 任务回调
            period (int, optional): 任务调用间隔,单位ms. Defaults to 0.
            priority (int, optional): 任务优先级. Defaults to 10.
            one_shot (bool, optional): 标记任务是否为单次任务. Defaults to False.
            on_complete (_type_, optional): 任务回调执行完毕执行的回调,接受一个任务返回值的参数. Defaults to None.
            args (tuple, optional): 任务启动时的参数. Defaults to None.
            kwargs (dict, optional): 任务启动时的关键字参数. Defaults to None.
        """
        if callback.__class__.__name__ == 'generator':
            self.generator = callback(*args,**kwargs)  # 如果是生成器，保存生成器对象
            self.callback = None
        else:
            self.generator = None
            self.callback = callback   # 普通函数回调

        self.period = period           # 任务的执行间隔（ms）
        self.priority = priority       # 优先级，数值越小优先级越高
        self.one_shot = one_shot       # 是否是单次任务
        self.on_complete = on_complete # 任务完成执行的回调函数
        self.args = args               # 任务启动时的参数
        self.kwargs = kwargs           # 任务启动时的关键字参数
        self.next_run = time.ticks_add(time.ticks_ms(), period)   # 下次运行时间

    def __lt__(self, other):
        """比较任务，优先按时间排序；时间相同时按优先级排序。"""
        if self.next_run == other.next_run:
            return self.priority < other.priority
        return self.next_run < other.next_run

    def execute(self) -> bool:
        """执行任务,任务是否需要继续执行。True表示继续,False表示结束"""
        if self.generator:
            try:
                next(self.generator)  # 执行生成器的下一步
                return True  # 生成器未完成，标记任务继续
            except StopIteration as e:
                result = e.value # 获取生成器的返回值
                if self.on_complete: # 任务完成后执行回调
                    self.on_complete(result)
                return not self.one_shot  # 对于单次任务，标记结束；多次任务则标记继续
        else: # 执行普通回调
            result = self.callback(*self.args,**self.kwargs)
            if self.on_complete:  # 单次任务完成后执行回调
                self.on_complete(result)
            return not self.one_shot  # 对于单次任务；标记结束；多次任务则标记继续
