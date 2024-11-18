# ./core/widget.py

class Widget:
    RED   = 0xf800
    GREEN = 0x07e0
    BLUE  = 0x001f
    PINK  = 0xf81f

    def __init__(self,
                 abs_x = 0, abs_y = 0,
                 rel_x = None, rel_y = None,
                 width = None, height = None,
                 visibility = True,
                 background_color = None):
        # 初始化时坐标，分绝对坐标和相对坐标
        self.abs_x = abs_x
        self.abs_y = abs_y
        self.rel_x = rel_x
        self.rel_y = rel_y
        # 目标位置，由布局系统确定
        self.dx = abs_x
        self.dy = abs_y
        # widget 是否可见
        self.visibility = visibility
        self.width = width
        self.height = height
        # 若已初始化时定义宽或高，则layout布局系统无法自动设置widget的大小
        # 但是可以通过resize()手动调整大小，不受次项限制
        self.width_resizable = True if width is None else False
        self.height_resizable = True if height is None else False
        # 缓存的位图对象
        self._bitmap = None
        self._text_bitmap = None
        # 绘制系统脏标记,分别用来触发刷新和重绘
        self._dirty = True
        self._content_dirty = True
        # 布局系统脏标记，用来触发重新计算布局。
        # self._position_dirty = True
        # self._size_dirty = True
        self._layout_dirty = True

        self.parent = None
        self.children = []
        # 背景色
        self.background_color = background_color
            
            
    def layout(self,
               dx = 0, dy = 0,
               width = None, height = None):
        """
        布局函数,设置控件的位置和大小,由父容器调用
        此函数从root开始,一层层调用
        在容器中次函数会被容器重写,用来迭代布局容器中的子元素
        如果位置或大小发生变化，标记需要重绘
        """
        self.dx = dx if self.dx !=dx else self.dx
        self.dy = dy if self.dy !=dy else self.dy
        self.width = width if self.width_resizable and self.width != width and width !=None else self.width
        self.height = height if self.height_resizable and self.height != height and height != None else self.height
        self._dirty = True
        self._layout_dirty = False
    
    def move_to(self,abs_x = 0, abs_y = 0):
        self.dx = abs_x if self.dx !=abs_x else self.dx
        self.dy = abs_y if self.dy !=abs_y else self.dy
        self.register_layout_dirty()

    # 强制重新设置大小
    def resize(self, width = None, height = None):
        self.width = width if self.width_resizable and self.width != width and width !=None else self.width
        self.height = height if self.height_resizable and self.height != height and height != None else self.height
        self.register_layout_dirty()

    def hide(self):
        # 隐藏不算内容发生改变
        self.visibility = False
        self.register_dirty()
        self._dirty = True
        for child in self.children:
            child.hide()
        
    def unhide(self):
        self.visibility = True
        self.register_dirty()
        for child in self.children:
            child.unhide()
        

    def _get_min_size(self):
        """
        计算元素尺寸用。
        容器会重写这个方法，用来迭代嵌套子元素的尺寸
        """
        width = self.width if not self.width_resizable else 0
        height = self.height if not self.height_resizable else 0
        rel_x = self.rel_x if self.rel_x is not None else 0
        rel_y = self.rel_y if self.rel_y is not None else 0
        
        min_width = width + rel_x
        min_height = height + rel_y
        return (min_width, min_height)
    
    def update_layout(self):
        """
        统计子元素的尺寸,并按照容器类型调用layout()布局设置
        次函数每种容器实现方式不同，所以需要容器自己重写次函数

        """
        pass


    # 从子层，向上层一层层标脏
    def register_dirty(self):
        self._dirty = True
        if self.parent:
            self.parent.register_dirty()
    # 从父层，向下层一层层标脏
    def mark_dirty(self):
        self._dirty = True
        for child in self.children:
            child.mark_dirty()

    # def register_position_dirty(self):
    #     self._position_dirty = True
    #     if self.parent:
    #         self.parent.register_position_dirty()
    # def mark_position_dirty(self):
    #     self._position_dirty = True
    #     for child in self.children:
    #         child.mark_position_dirty()

    # def register_size_dirty(self):
    #     self._size_dirty = True
    #     if self.parent:
    #         self.parent.register_size_dirty()
    # def mark_size_dirty(self):
    #     self._size_dirty = True
    #     for child in self.children:
    #         child.mark_size_dirty()

    def register_content_dirty(self):
        self._content_dirty = True
        if self.parent:
            self.parent.register_content_dirty()
    # def mark_content_dirty(self):
    #     self._content_dirty = True
    #     for child in self.children:
    #         child.mark_content_dirty()


    def register_layout_dirty(self):
        self._layout_dirty = True
        if self.parent:
            self.parent.register_layout_dirty()
