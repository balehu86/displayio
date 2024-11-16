# ./display.py
from .core.bitmap import Bitmap

from .utils.decorator import timeit

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
        self.root.layout(x=0, y=0, width=self.width, height=self.height)
        self.root.width_resizable = False
        self.root.height_resizable = False
    
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
            
                for child in widget.children:
                    render_widget(child)  # 递归处理子组件
                    
            render_widget(self.root)
            
    def run(self):
        while True:
            self.check_dirty()