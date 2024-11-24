# ./core/widget.py
from .event import Event

class Widget:
    RED   = 0xf800
    GREEN = 0x07e0
    BLUE  = 0x001f
    PINK  = 0xf81f

    def __init__(self,
                 abs_x = None, abs_y = None,
                 rel_x = None, rel_y = None,
                 width = None, height = None,
                 visibility = True,
                 background_color = None):
        # 初始化时坐标，分绝对坐标和相对坐标
        # 警告：若要将部件添加进flex_box，严禁初始化abs_x和abs_y
        self.abs_x = abs_x
        self.abs_y = abs_y
        self.rel_x = rel_x
        self.rel_y = rel_y
        # 目标位置，由布局系统确定
        self.dx = abs_x if abs_x is not None else 0
        self.dy = abs_y if abs_y is not None else 0
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
        self._layout_dirty = True
        # 部件继承关系
        self.parent = None
        self.children = []
        # 背景色
        self.background_color = background_color

        # event注册
        self.registed_event = []
            
            
    def layout(self,
               dx, dy,
               width = None, height = None):
        """
        布局函数,设置控件的位置和大小,由父容器调用
        此函数从root开始,一层层调用
        在容器中次函数会被容器重写,用来迭代布局容器中的子元素
        如果位置或大小发生变化，标记需要重绘

        Args:
            dx (int, optional): _description_. Defaults to 0.
            dy (int, optional): _description_. Defaults to 0.
            width (_type_, optional): _description_. Defaults to None.
            height (_type_, optional): _description_. Defaults to None.
        """
        rel_x = self.rel_x if self.rel_x is not None else 0
        rel_y = self.rel_y if self.rel_y is not None else 0
        
        # 处理绝对位置，它具有最高优先级
        if self.abs_x is not None:
            self.dx = self.abs_x
        else:
            # 没有绝对位置时，使用父容器位置加上相对偏移
            self.dx = dx + rel_x
            
        if self.abs_y is not None:
            self.dy = self.abs_y
        else:
            # 没有绝对位置时，使用父容器位置加上相对偏移
            self.dy = dy + rel_y

        # 处理尺寸
        if self.width_resizable:
            self.width = (width-rel_x) if width is not None else 0
        if self.height_resizable:
            self.height = (height-rel_y) if height is not None else 0

        self._dirty = True
        self._layout_dirty = False

    def move(self,abs_x = None, abs_y = None, rel_x=None, rel_y=None):
        """重新设置位置

        Args:
            abs_x (int, optional): _description_. Defaults to 0.
            abs_y (int, optional): _description_. Defaults to 0.
        """
        self.dx = abs_x if abs_x is not None else self.dx
        self.dy = abs_y if abs_y is not None else self.dy
        self.register_layout_dirty()

    def resize(self, width = None, height = None):
        """重新设置尺寸，会考虑部件是否可以被重新设置新的尺寸，这取决于部件初始化时是否设置有初始值

        Args:
            width (_type_, optional): _description_. Defaults to None.
            height (_type_, optional): _description_. Defaults to None.
        """
        self.width = width if self.width_resizable and self.width != width and width !=None else self.width
        self.height = height if self.height_resizable and self.height != height and height != None else self.height
        self.register_layout_dirty()

    def hide(self):
        """隐藏部件
        """
        self.visibility = False
        self.register_dirty()
        self._dirty = True
        for child in self.children:
            child.hide()
        
    def unhide(self):
        """取消隐藏部件
        """
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


    def register_dirty(self):
        """向上汇报 脏
        """
        self._dirty = True
        if self.parent:
            self.parent.register_dirty()

    def mark_dirty(self):
        """向下通知 脏
        """
        self._dirty = True
        for child in self.children:
            child.mark_dirty()

    def register_content_dirty(self):
        """向上汇报 内容脏
        """
        self._content_dirty = True
        if self.parent:
            self.parent.register_content_dirty()
    # def mark_content_dirty(self):
    #     self._content_dirty = True
    #     for child in self.children:
    #         child.mark_content_dirty()

    def register_layout_dirty(self):
        """向上汇报 布局脏
        """
        self._layout_dirty = True
        if self.parent:
            self.parent.register_layout_dirty()

    def event_handler(self, event: Event):
        """处理event,决定是自己处理还是向下传递. 然后向上汇报处理结果

        Args:
            event (_type_): _description_
        """
        if event.type in self.registed_event:
            # do something
            event.done()
            return
        else:
            for child in self.children:
                child.event_handler(event)
