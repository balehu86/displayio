# ./core/widget.py

class Widget:
    RED   = 0xf800
    GREEN = 0x07e0
    BLUE  = 0x001f
    PINK  = 0xf18f

    def __init__(self,x = 0, y = 0, width = None, height = None, visibility = True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # 若已初始化时定义宽或高，则layout布局系统无法自动设置widget的大小
        # 但是可以通过resize()手动调整大小，不受次项限制
        self.width_resizable = True if width is None else False
        self.height_resizable = True if height is None else False
        # 缓存的位图对象
        self._bitmap = None
        # 脏标记，Ture则重绘bitmap，并刷新
        self._dirty = True
        self.parent = None
        self.children = []
        # widget 是否可见
        self.visibility = visibility
        # 支持同一个widget对象同时显示到不同区域bytearray(x,y)
        self.area = [[x,y]]


    # 从子层，向上层一层层标脏
    def register_dirty(self):
        self._dirty = True
        if self.parent:
            self.parent.register_dirty()
    # 从父层，向下层一层层标脏
    def mark_dirty(self):
        for child in self.children:
            child.mark_dirty()
        self._dirty = True
   
            
    def layout(self, x = 0, y = 0, 
               width = None, height = None):
        """
        布局函数，设置控件的位置和大小
        如果位置或大小发生变化，标记需要重绘
        """
        self.x = x if self.x !=x else self.x
        self.y = y if self.y !=y else self.y

        self.width = width if self.width_resizable and self.width != width and width !=None else self.width
        self.height = height if self.height_resizable and self.height != height and height != None else self.height
        self.register_dirty()
    
    # 强制重新设置大小
    def resize(self,width=None,height=None):
        self.width = width if width !=None else self.width
        self.height = height if height != None else self.height

    def hide(self):
        def set_hide(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    set_hide(child)
            widget.visibility = False
        set_hide(self)
        self.register_dirty()
        self.mark_dirty()
        
    def unhide(self):
        def set_unhide(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    set_unhide(child)
            self.visibility = True
        set_unhide(self)
        self.register_dirty()
        self.mark_dirty()

    def _get_min_size(self):
        min_width = self.width if not self.width_resizable else 0
        min_height = self.height if not self.height_resizable else 0
        return (min_width, min_height)
