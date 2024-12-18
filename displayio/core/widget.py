# ./core/widget.py
from .style import Color, Style

class Widget(Color, Style):
    # widget状态枚举
    STATE_DEFAULT = 0   # 正常、释放状态
    STATE_CHECKED = 1   # 切换或选中状态
    STATE_FOCUSED = 2   # 通过键盘或编码器聚焦或通过触摸板/鼠标点击
    STATE_FOCUS_KEY = 3 # 通过键盘或编码器聚焦，但不通过触摸板/鼠标聚焦
    STATE_EDITED = 4    # 通过编码器编辑
    STATE_HOVERED = 5   # 鼠标悬停
    STATE_PRESSED = 6   # 受到压力
    STATE_SCROLLED = 7  # 正在滚动
    STATE_DISABLED = 8  # 已禁用

    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0,
                 width=None, height=None,
                 visibility=True, state=STATE_DEFAULT,
                 background_color=Color.WHITE, # 默认白色
                 transparent_color=Color.PINK,
                 color_format = Style.RGB565):
        # 初始化时坐标，分绝对坐标和相对坐标
        # 警告：若要将部件添加进flex_box，严禁初始化abs_x和abs_y
        self.abs_x, self.abs_y = abs_x, abs_y
        self.rel_x, self.rel_y = rel_x, rel_y
        # 目标位置，由布局系统确定
        self.dx = abs_x if abs_x is not None else 0
        self.dy = abs_y if abs_y is not None else 0
        # widget 是否可见
        self.visibility = visibility
        self.width, self.height = width, height
        # widget 是否可交互，如果部件未启用，则不会处理事件
        self.state = state
        # 若已初始化时定义宽或高，则layout布局系统无法自动设置widget的大小
        # 但是可以通过resize()手动调整大小，不受次项限制
        self.width_resizable = True if width is None else False
        self.height_resizable = True if height is None else False
        # 位图的色彩格式
        self.color_format = color_format
        # 缓存的位图对象
        self._bitmap = None
        self._empty_bitmap = None
        """脏标记解释：    警告:任何具有get_bitmap的组件将被视为组件树的末端
        _dirty: 部件是否需要重绘,只用于发起重绘,
            是否重绘缓存的bitmap取决于_content_dirty.
            在调用Widget的部分设置函数时标记,并向根部传递,
            在Display的事件循环render_widget()中调用get_bitmap()后取消标记。
        _content_dirty: 部件的内容是否需要重绘,用于重绘部件实例缓存的bitmap,
            在调用Widget的部分设置函数时标记,  不会传递！！！
            在Display的事件循环render_widget()中调用get_bitmap()后取消标记。
        _layout_dirty: 部件的布局是否需要重新计算,并重新布局,
            在调用widget的部分设置和container的布局树结构发生改变时标记,并向根部传递,
            在Widget的layout()中,重新布局后取消。
        """
        # 绘制系统的脏标记
        self._dirty = True # 触发刷新检查
        self._content_dirty = True # 触发重绘
        # 布局系统脏标记，用来触发重新计算布局。布局系统的尺寸位置重分配总是从根节点开始。
        self._layout_dirty = True
        # 部件继承关系
        self.parent = None
        # 容器的子元素
        self.children = []
        # 背景色
        self.background_color = background_color
        # 透明色
        self.transparent_color = transparent_color
        # event监听器注册
        self.event_listener = {}  # 事件处理器字典
            
    def layout(self, dx, dy, width=None, height=None) -> None:
        """
        布局函数,设置控件的位置和大小,由父容器调用
        此函数从root开始,一层层调用
        在容器中次函数会被容器重写,用来迭代布局容器中的子元素
        如果位置或大小发生变化，标记需要重绘
        """
        rel_x = self.rel_x
        rel_y = self.rel_y
        # 处理绝对位置，它具有最高优先级
        # 没有绝对位置时，使用父容器位置加上相对偏移
        actual_dx = self.abs_x or (dx + rel_x)
        if self.dx != actual_dx:
            self.dx = actual_dx
            self.register_dirty()

        actual_dy = self.abs_y or (dy + rel_y)
        if self.dy != actual_dy:
            self.dy = actual_dy
            self.register_dirty()

        # 处理尺寸
        actual_width = (width-rel_x) if width is not None else 0
        if self.width != actual_width:
            self.width = actual_width
            self._content_dirty = True

        actual_height = (height-rel_y) if height is not None else 0
        if self.height != actual_height:
            self.height = actual_height
            self._content_dirty = True
        # 重新layout结束,重置layout脏标记
        self._layout_dirty = False
    
    def resize(self, width = None, height = None):
        """重新设置尺寸，会考虑部件是否可以被重新设置新的尺寸，这取决于部件初始化时是否设置有初始值

        Args:
            width (_type_, optional): _description_. Defaults to None.
            height (_type_, optional): _description_. Defaults to None.
        """
        self.width = width if self.width_resizable and self.width != width and width !=None else self.width
        self.height = height if self.height_resizable and self.height != height and height != None else self.height
        self._content_dirty = True
        self.register_layout_dirty()

    def hide(self) -> None:
        """隐藏部件"""
        self.visibility = False
        self.register_dirty()
        
    def unhide(self) -> None:
        """取消隐藏部件"""
        self.visibility = True
        self.register_dirty()
        
    def _get_min_size(self) -> tuple[int, int]:
        """
        计算元素尺寸用。
        容器会重写这个方法，用来迭代嵌套子元素的尺寸
        """
        # 考虑自身的固定尺寸,如果固定尺寸则取self的尺寸，否则取0
        width = self.width if not self.width_resizable else 0
        height = self.height if not self.height_resizable else 0

        return width+self.rel_x, height+self.rel_y
    
    def register_dirty(self) -> None:
        """向根方向汇报 脏"""
        if not self._dirty:  # 只有在未被标记为脏时，才向上传递
            self._dirty = True
            if self.parent:
                self.parent.register_dirty()

    def register_layout_dirty(self) -> None:
        """向根方向传递 布局脏"""
        if not self._layout_dirty:  # 只有在未被标记为布局脏时，才向上传递
            self._layout_dirty = True
            if self.parent:
                self.parent.register_layout_dirty()

    def mark_dirty(self) -> None:
        self._dirty = True
    
    def mark_content_dirty(self) -> None:
        self._content_dirty = True

    def event_handler(self, event) -> bool:
        """处理事件
        
        首先检查自己是否有对应的处理器,然后决定是否处理

        Args:
            event: Event类型实例
        """
        # 如果部件未启用，则不会处理事件
        if self.state == self.STATE_DISABLED:
            return False

        # 当 target_widget 不为 None 时，仅检查其是否为 self
        if event.target_widget is not None:
            if event.target_widget is not self:
                return False
        # 当 target_widget 为 None 且 target_position 不为 None 时，根据位置判断
        elif event.target_position is not None:
            x, y = event.target_position
            if not (self.dx <= x < self.dx + self.width and 
                    self.dy <= y < self.dy + self.height):
                return False
    
        # 处理事件
        if event.type in self.event_listener:
            for callback_func in self.event_listener[event.type]:
                callback_func(event)
                event.done()
        return event.is_handled()

    def bind(self, event_type, callback_func: function) -> None:
        """绑定事件处理器
        
        Args:
            event_type (_EventType_): 事件类型（EventType枚举值）
            callback_func (_function_, optional): 事件处理函数，接收Event对象作为参数. Defaults to None.
        """
        if event_type not in self.event_listener:
            self.event_listener[event_type] = []
        self.event_listener[event_type].append(callback_func)

    def unbind(self, event_type, callback_func: function=None) -> None:
        """解绑事件处理器
        
        Args:
            event_type (_EventType_): 事件类型（EventType枚举值）
            callback_func (_function_, optional): 事件处理函数，接收Event对象作为参数. Defaults to None.
        """
        if event_type in self.event_listener:
            if callback_func is None:
                self.event_listener[event_type] = []
            else:
                self.event_listener[event_type] = [
                    cb for cb in self.event_listener[event_type] 
                    if cb != callback_func
                ]

    def index(self) -> int:
        """返回部件在父容器中的位置,从0开始"""
        if self.parent is not None:
            return self.parent.index(self)

    def __del__(self):
        """析构函数,在部件被销毁时被调用"""
        if self.parent is not None:
            self.parent.children.remove(self)