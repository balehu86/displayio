# ./core/widget.py
from .style import Color, Style
from .dirty import MergeRegionSystem
from .event import EventType
from .logging import logger

class BaseWidget(Color, Style):

    __slots__ = ('abs_x', 'abs_y', 'rel_x', 'rel_y', 'dx', 'dy', 'dz',
                 'width', 'height', 'width_resizable', 'height_resizable',
                 'state', 'visibility', 'color_format',
                 '_bitmap', 'dirty_system',
                 'parent', 'children', 'transparent_color', 'background', 'event_listener')
    
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
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=STATE_DEFAULT,
                 transparent_color=Color.PINK,
                 background=Color.DARK,
                 color_format=Style.RGB565):
        # 初始化时坐标，分绝对坐标和相对坐标
        # 警告：若要将部件添加进flex_box，严禁初始化abs_x和abs_y
        self.abs_x, self.abs_y = abs_x, abs_y
        self.rel_x, self.rel_y = rel_x, rel_y
        # 目标位置，由布局系统确定
        self.dx = abs_x if abs_x is not None else 0
        self.dy = abs_y if abs_y is not None else 0
        # 部件在z轴方向上的深度
        self.dz = dz
        # 部件的尺寸，分宽和高
        self.width, self.height = width, height
        # 若已初始化时定义宽或高，则layout布局系统无法自动设置widget的大小
        # 但是可以通过resize()手动调整大小，不受次项限制
        self.width_resizable = True if width is None else False
        self.height_resizable = True if height is None else False
        # widget 是否可交互，如果部件未启用，则不会处理事件
        self.state = state
        # widget 是否可见
        self.visibility = visibility
        # 位图的色彩格式
        self.color_format = color_format
        # 缓存的位图对象
        self._bitmap = None
        # 脏区域系统
        self.dirty_system = MergeRegionSystem()
        # 部件继承关系
        self.parent = None
        # 容器的子元素
        self.children = []
        # 透明色
        self.transparent_color = transparent_color
        # 背景
        self.background = Background(color=background)
        # event监听器注册
        self.event_listener = {EventType.FOCUS:[self.focus],
                               EventType.UNFOCUS:[self.unfocus]}  # 事件处理器字典
            
    def layout(self, dx, dy, width=None, height=None) -> None:
        """
        布局函数,设置控件的位置和大小,由父容器调用
        此函数从root开始,一层层调用
        在容器中次函数会被容器重写,用来迭代布局容器中的子元素
        如果位置或大小发生变化，标记需要重绘
        """
        # 将初始区域记录
        original_dx, original_dy = self.dx, self.dy
        original_width = self.width if self.width is not None else 0
        original_height = self.height if self.height is not None else 0
        # 标记布局是否发生改变
        changed = False
        rel_x, rel_y = self.rel_x, self.rel_y
        # 处理绝对位置，它具有最高优先级
        # 没有绝对位置时，使用父容器位置加上相对偏移
        actual_dx = self.abs_x or (dx + rel_x)
        actual_dy = self.abs_y or (dy + rel_y)
        if self.dx != actual_dx:
            self.dx = actual_dx
            changed = True
        if self.dy != actual_dy:
            self.dy = actual_dy
            changed = True
        
        # 处理尺寸
        actual_width = (width-rel_x) if width is not None else 0
        actual_height = (height-rel_y) if height is not None else 0
        if self.width != actual_width:
            self.width = actual_width
            changed = True
            self.dirty_system.add_widget(self)
        if self.height != actual_height:
            self.height = actual_height
            changed = True
            self.dirty_system.add_widget(self)

        if changed: # 如果发生改变，则将原始区域和重新布局后的区域标脏
            self.dirty_system.add(original_dx, original_dy, original_width, original_height)
            self.dirty_system.add(self.dx, self.dy, self.width, self.height)
    
    def resize(self, width=None, height=None, force=False):
        """重新设置尺寸，会考虑部件是否可以被重新设置新的尺寸，这取决于部件初始化时是否设置有初始值

        Args:
            width (_type_, optional): _description_. Defaults to None.
            height (_type_, optional): _description_. Defaults to None.
        """
        self.width = width if (force or self.width_resizable) and width != None else self.width
        self.height = height if (force or self.height_resizable) and height != None else self.height
        self.dirty_system.add_widget(self)
        self.dirty_system.layout_dirty = True
        original_width = self.width if self.width is not None else 0
        original_height = self.height if self.height is not None else 0
        self.dirty_system.add(self.dx, self.dy, original_width, original_height)
        self.dirty_system.add(self.dx, self.dy, self.width, self.height)

    def hide(self) -> None:
        """隐藏部件"""
        self.visibility = False
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
        for child in self.children:
            if child.visibility:
                child.hide()

    def unhide(self) -> None:
        """取消隐藏部件"""
        self.visibility = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
        for child in self.children:
            if not child.visibility:
                child.unhide()

    def _get_min_size(self) -> tuple[int, int]:
        """
        计算元素尺寸用。
        容器会重写这个方法，用来迭代嵌套子元素的尺寸
        """
        # 考虑自身的固定尺寸,如果固定尺寸则取self的尺寸，否则取0
        width = self.width if not self.width_resizable else 0
        height = self.height if not self.height_resizable else 0

        return width+self.rel_x, height+self.rel_y

    def mark_dirty(self) -> None:
        """向末梢传递 脏"""
        self._dirty = True
        self.dirty_system.add_widget(self)
        for child in self.children:
            if not child._dirty: # 先做个判断，减少重复修改
            if child not in self.dirty_system.dirty_widget: # 先做个判断，减少重复修改
                child.mark_dirty()

    def set_dirty_system(self, dirty_system) -> None:
        """设置脏区域管理器"""
        self.dirty_system = dirty_system
        for child in self.children:
            if child.dirty_system is not dirty_system:
                child.set_dirty_system(dirty_system)

    def set_default_color(self, color) -> None:
    def set_background(self, color=None, pic=None) -> None:
        """设置背景"""
        self.background=Background(color=color, pic=pic)
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    def bubble(self, event) -> None:
        """事件冒泡
        首先检查容器自己是否有对应的处理器，如果有则看自己是否处理，不处理则传递给子组件
        Args:
            event: Event类实例
        """
        # 尝试捕获
        # 如果事件未被捕获，传递给子组件
        logger.debug(f'bubble {event.type}')
        if self.catch(event):
            if not self.handle(event):
                for child in self.children: # 传递
                    child.bubble(event)

    def catch(self, event) -> bool:
        """捕获事件
        首先检查自己是否有对应的处理器,然后返回是否被捕获
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
        return True

    def handle(self, event) -> None:
        """处理事件"""
        if event.type in self.event_listener:
            for callback_func in self.event_listener[event.type]:
                callback_func(widget=self,event=event)
                event.handle()
            return True
    
    def bind(self, event_type, callback_func: function) -> None:
        """绑定事件处理器"""
        if event_type not in self.event_listener:
            self.event_listener[event_type] = []
        self.event_listener[event_type].append(callback_func)

    def unbind(self, event_type, callback_func: function=None) -> None:
        """解绑事件处理器"""
        if event_type in self.event_listener:
            if callback_func is None:
                self.event_listener[event_type].clear()
            elif callback_func in self.event_listener[event_type]:
                self.event_listener[event_type].remove(callback_func)

    def index(self) -> int:
        """返回部件在父容器中的位置,从0开始"""
        if self.parent is not None:
            return self.parent.index(self)

    def widget_in_dirty_area(self):
        """检查widget是否和脏区域有交集"""
        return self.dirty_system.intersects(self.dx,self.dy,self.width,self.height)
    
    def focus(self, widget, event):
        """元素聚焦,会将元素内所有元素调暗0.1"""
        if hasattr(self, 'background_color') and self.state != self.STATE_DISABLED:
            self.background_color_cache = self.background_color
            self.background_color= self._darken_color(self.background_color,0.9)
        self._dirty = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
        for child in self.children:
            child.focus(widget, event)

    def unfocus(self, widget, event):
        """取消元素聚焦"""
        if hasattr(self, 'background_color') and self.state != self.STATE_DISABLED:
            if self.background_color_cache is not None:
                self.background_color = self.background_color_cache
                self.background_color_cache = None
        self._dirty = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
        for child in self.children:
            child.unfocus(widget, event)

    def _darken_color(self, color, factor):
        """将16位RGB颜色调暗
        参数:
            color: 原始颜色(16位RGB)
            factor: 暗化因子(0-1)
        """
        # 提取RGB分量
        r = (color >> 11) & 0x1F
        g = (color >> 5) & 0x3F
        b = color & 0x1F
        # 调整亮度
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        # 重新组装颜色
        return (r << 11) | (g << 5) | b
    
    def __lt__(self, other):
        """比较图层，按优先级排序。"""
        return self.dz < other.dz
    
    def __repr__(self):
    # def __repr__(self):
    #     return f'<{self.__class__.__name__} object> \n\tdx: {self.dx}, dy: {self.dx}, dz: {self.dz}, \n\twidth: {self.width}, height: {self.height}, \n\tvisibility: {self.visibility}, state: {self.state}'
