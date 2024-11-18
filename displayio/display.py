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
            self.tem_dx = 0
            self.tem_dy = 0
            self.tem_width = self.width
            self.tem_height = self.height
            self.tem_bitmap=Bitmap(self.width,self.height)
            self.tem_bitmap.fill_rect(0,0,self.width,self.height,0xf81f)
            self.bitmap_lock=_thread.allocate_lock()
            self.thread = _thread.start_new_thread(driver.thread_refresh,(self.tem_bitmap,
                                                                          self.tem_dx, self.tem_dy,
                                                                          self.tem_width, self.tem_height,
                                                                          self.bitmap_lock))
        
    def set_root(self, widget):
        self.root = widget
        self.root.layout(dx=0, dy=0, width=self.width, height=self.height)
        self.root.width_resizable = False
        self.root.height_resizable = False
    
    @timeit
    def check_dirty(self):
        if self.root._dirty:

            def render_widget(widget):
                if widget._dirty:  # 只有脏组件才需要重新绘制
                    # 只有实际的widget才有get_bitmap生成bitamp，容器没有此函数
                    if hasattr(widget, 'get_bitmap'):
                        if self.threaded:
                            self.bitmap_lock.acquire()
                            try:
                                self.tem_bitmap = widget.get_bitmap()
                                self.tem_dx= widget.dx
                                self.tem_dy= widget.dy
                                self.tem_width= widget.width
                                self.tem_height= widget.height
                            finally:self.bitmap_lock.release()
                        else:
                            bitmap = widget.get_bitmap()
                            self.driver.refresh(bitmap,dx=widget.dx,dy=widget.dy)
                          
                for child in widget.children:
                    render_widget(child)  # 递归处理子组件
                
            render_widget(self.root)
    

    @timeit
    def check_layout_dirty(self):
        if self.root._layout_dirty:
            self.root.layout(dx=0, dy=0,width=self.width, height=self.height)

    def run(self):
        while True:
            self.check_layout_dirty()
            self.check_dirty()