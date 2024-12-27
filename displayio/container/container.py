# ./core/container.py
from ..core.widget import Widget

# 类型提示
from ..core.event import Event

from heapq import heappush

class Container(Widget):
    """
    容器基类
    继承自Widget
    """
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=Widget.STATE_DEFAULT,
                 background_color=Widget.WHITE,
                 transparent_color=Widget.PINK,
                 color_format=Widget.RGB565):
        """
        初始化按钮控件
        
        继承Widget的所有参数,额外添加:
            pass
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         background_color = background_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        
    def add(self, *childs: Widget) -> None:
        """向容器中添加元素"""
        for child in childs:
            child.parent=self
            child.set_dirty_system(self.dirty_system)  # 设置相同的脏区域管理器
            heappush(self.children, child)

        self.mark_dirty()
        self.dirty_system.layout_dirty = True

    def remove(self, *childs: Widget) -> None:
        """从容器中移除元素"""
        for child in childs:
            if child in self.children:
                child.parent = None
                self.children.remove(child)
        self.mark_dirty()
        self.dirty_system.layout_dirty = True

    def clear(self) -> None:
        """清空容器中所有元素"""
        for child in self.children:
            child.parent = None
        self.children.clear()

        self.mark_dirty()
        self.dirty_system.layout_dirty = True

    def layout(self, dx=0, dy=0, width=None, height=None) -> None:
        """在这里重写布局方法,确保先更新自身位置和大小"""
        # 设置自己的布局
        super().layout(dx=dx, dy=dy, width=width, height=height)
        # 设置子元素的布局
        self.update_layout()

    def update_layout(self) -> None:
        """在子类型里会重写这个方法,这里只做声明"""
        pass

    def mark_dirty(self) -> None:
        """向末梢传递 脏"""
        self._dirty = True
        for child in self.children:
            child.mark_dirty()

    def bind(self,event_type, callback_func) -> None:
        """事件委托,由容器为每个子元素绑定事件监听

        Args:
            event_type (_EventType_): 事件类型（EventType枚举值）
            callback_func (_function_, optional): 事件处理函数，接收Event对象作为参数. Defaults to None.
        """
        for child in self.children:
            child.bind(event_type, callback_func)

    def unbind(self, event_type, callback_func=None) -> None:
        """事件委托,由容器为每个子元素解除绑定事件监听

        Args:
            event_type (_EventType_): 事件类型（EventType枚举值）
            callback_func (_function_, optional): 事件处理函数，接收Event对象作为参数. Defaults to None.
        """
        for child in self.children:
            child.unbind(event_type, callback_func)

    def hide(self) -> None:
        """隐藏容器"""
        self.visibility = False
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
        for child in self.children:
            child.hide()

    def unhide(self) -> None:
        """取消隐藏容器"""
        self.visibility = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
        for child in self.children:
            child.unhide()

    def event_handler(self, event: Event) -> None:
        """处理事件
        首先检查容器自己是否有对应的处理器，如果有则看自己是否处理，不处理则传递给子组件
        Args:
            event: Event类实例
        """
        resault = super().event_handler(event)
        # 如果事件未被处理，传递给子组件
        if not resault:
            for child in self.children: # 从上到下传递
                if event.is_handled(): # 未被处理
                    break
                else: # 已处理
                    child.event_handler(event)
