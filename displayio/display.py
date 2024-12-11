# ./display.py
from .core.loop import MainLoop
from .core.bitmap import Bitmap
import time

class Display:
    def __init__(self, width, height, root=None,
                 output=None, inputs=[], fps=0,
                 show_fps=False, partly_refresh=True, threaded=True):
        # 屏幕尺寸和根节点
        self.width = width
        self.height = height
        self.root = root
        # 输入输出设备
        self.output = output
        self.inputs = inputs
        # 刷新频率和出否在命令行输出fps信息
        self.fps = fps # 默认0，不限制刷新频率
        self.show_fps = show_fps # 是否显示刷新率
        # 局部刷新
        self.partly_refresh = partly_refresh
        # 脏区域列表,用来处理遮挡问题,每个列表为 [x, y, width, height]
        self.dirty_area_list = [[0,0,0,0]]
        # 创建事件循环
        self.loop = MainLoop(self)
        # 标志是否开启多线程
        self.threaded = threaded
        if threaded and output is not None:
            import _thread
            # 坐标和尺寸参数 x,y,width,height
            self.thread_dx = 0
            self.thread_dy = 0
            self.thread_width = self.width
            self.thread_height = self.height
            # 初始化一个bitmap，粉色背景
            init_buffer=bytes(width*height*2)
            # 锁和运行控制
            self.lock=_thread.allocate_lock()
            self.thread_running = True
            # 传递给线程的可变类型参数
            self.thread_args = {'bitmap_memview':memoryview(init_buffer),\
                                'thread_running':self.thread_running,
                                'dx':0, 'dy':0, 'width':self.width,\
                                'height':self.height}
            # 创建线程
            self.thread = _thread.start_new_thread(
                                                self.output._thread_refresh_wrapper,\
                                                (self.thread_args,self.lock))

    def set_root(self, widget):
        """设置根组件"""
        self.root = widget
        self.root.layout(dx=0, dy=0, width=self.width, height=self.height)
        self.root.width_resizable = False
        self.root.height_resizable = False
        # 如果局部刷新,在root 部件创建一个全屏framebuff。
        if not self.partly_refresh:
            self.root._bitmap = Bitmap(self.root.width,self.root.height,
                                       transparent_color=self.root.transparent_color,
                                       format=Bitmap.RGB565)
    
    def add_event(self, event):
        """添加事件到事件循环"""
        self.loop.post_event(event)

    def add_input_device(self,*device):
        self.inputs.extend(device)

    def run(self,func):
        """启动显示循环"""
        self.loop.start(func)
        
    def stop(self):
        """停止显示循环和线程"""
        # 停止事件循环
        self.loop.stop()
        # 停止线程
        if self.threaded:
            self.thread_running = False
            if hasattr(self, 'thread') and self.thread is not None:
                # 等待线程自然退出
                time.sleep_ms(50)
