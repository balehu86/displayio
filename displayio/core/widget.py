# core/widget.py
class Widget:
    def __init__(self,x = 0, y = 0, 
                 width = None, height = None, hidden = False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # 若已定义宽或高，则布局系统无法设置widget的大小
        self.width_resizable = True if width is None else False
        self.height_resizable = True if height is None else False
        # 缓存的位图对象
        self._bitmap = None
        # 脏标记，Ture则重绘bitmap，并刷新
        self._dirty = True
        self.parent = None
        self.children = []
        # widget 是否可见,_hidden是widget自己hide，hidden是parent让隐藏的
        self._hidden = hidden


    # 从子层，向上层一层层标脏
    def register_dirty(self):
        self._dirty = True
        if self.parent:
            self.parent.register_dirty()
    # 从父层，向下层一层层标脏
    def mark_dirty(self):
        def render_dirty(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    render_dirty(child)
            widget._dirty = True
        render_dirty(self)
        
     
            
    def layout(self, x = 0, y = 0, 
               width = None, height = None):
        """
        布局函数，设置控件的位置和大小
        如果位置或大小发生变化，标记需要重绘
        """
        self.x = x if self.x !=x else self.x
        self.y = y if self.y !=y else self.y
        self.width = width if self.width_resizable and self.width != width else self.width
        self.height = height if self.height_resizable and self.height != height else self.height
        self.register_dirty()

    def hide(self):
        def set_hide(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    set_hide(child)
            widget._hidden = True
        set_hide(self)
        self.register_dirty()
        self.mark_dirty()
        
    def unhide(self):
        def set_unhide(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    set_unhide(child)
            self._hidden = False
        set_unhide(self)
        self.register_dirty()
        self.mark_dirty()

    def move_to(self, x = 0, y = 0):
        self.x = x if self.x !=x else self.x
        self.y = y if self.y !=y else self.y
        self.register_dirty()
