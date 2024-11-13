# core/display.py
from .core.bitmap import Bitmap
import time

def timeit(func):
    def new_func(*args, **kwargs):
        t = time.ticks_ms()
        result = func(*args, **kwargs)
        diff=time.ticks_diff(time.ticks_ms(), t)
        print("\033[32m"+func.__name__+"\033[0m"+" "*(20-len(func.__name__))+" executed in"+" "*(10-len(str(diff)))+"\033[31m"+str(diff)+" ms"+"\033[0m")
        return result
    return new_func

class Display:
    def __init__(self, width, height, driver=None,threaded=True):
        self.width = width
        self.height = height
        self.root = None
        self.driver = driver
        self.threaded = threaded
        if threaded and driver is not None:
            import _thread
            self.dx = 0
            self.dy = 0
            self.bitmap = Bitmap(0,0)
            self.bitmap_lock=_thread.allocate_lock()
            self.thread = _thread.start_new_thread(lambda: driver.thread_refresh(bitmap=self.bitmap,
                                                                          x=self.dx, y=self.dy,
                                                                          lock=self.bitmap_lock),())
        
    def set_root(self, widget):
        self.root = widget
        self.root.layout(0, 0, self.width, self.height)
    
    @timeit
    def check_dirty(self):
        if self.root:

            def render_widget(widget):
                if widget._dirty:  # 只有脏组件才需要重新绘制
                    if hasattr(widget, 'get_bitmap'):
                        # self._bitmap.fill_rect(widget.x,widget.y,widget.width,widget.height,color=0xffff)
                        # self._bitmap.blit(bitmap, dx=widget.x, dy=widget.y)
                        if self.threaded:
                            self.bitmap_lock.acquire()
                            try:
                                bitmap = widget.get_bitmap()
                                self.dx= widget.x
                                self.dy= widget.y
                            finally:self.bitmap_lock.release()
                        else:
                            bitmap = widget.get_bitmap()
                            self.driver.refresh(bitmap,x=widget.x,y=widget.y)
                    widget._dirty = False  # 绘制完成后清除脏标记

                for child in widget.children:
                    render_widget(child)  # 递归处理子组件
                    
            render_widget(self.root)
            
            # Here you would add display hardware update logic
            # self.driver.refresh(self._bitmap)
    def run(self):
        while True:
            self.check_dirty()