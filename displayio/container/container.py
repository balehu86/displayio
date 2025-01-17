# ./core/container.py
from ..core.base_widget import BaseWidget
from ..core.dirty import DirtySystem # type hint
from ..core.event import EventType # type hint

from heapq import heappush

class Container(BaseWidget):
    """
    容器基类
    继承自BaseWidget
    """
    __slots__ = ()
    
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=BaseWidget.STATE_DEFAULT,
                 transparent_color=BaseWidget.PINK,
                 background=BaseWidget.DARK,
                 color_format=BaseWidget.RGB565):
        """
        初始化按钮控件
        
        继承BaseWidget的所有参数,额外添加:
            pass
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         transparent_color = transparent_color,
                         background = background,
                         color_format = color_format)
        
    def add(self, *childs: BaseWidget|'Container') -> None:
        """向容器中添加元素"""
        for child in childs:
            child.parent=self
            child.set_dirty_system(self.dirty_system)  # 设置相同的脏区域管理器
            heappush(self.children, child)

        self.dirty_system.layout_dirty = True

    def remove(self, *childs: BaseWidget|'Container') -> None:
        """从容器中移除元素"""
        for child in childs:
            if child in self.children:
                child.parent = None
                child.set_dirty_system(DirtySystem(name='default'))
                self.children.remove(child)

        self.dirty_system.layout_dirty = True

    def clear(self) -> None:
        """清空容器中所有元素"""
        for child in self.children:
            child.parent = None
            child.set_dirty_system(DirtySystem(name='default'))
        self.children.clear()

        self.dirty_system.layout_dirty = True

    def layout(self, dx=0, dy=0, width=None, height=None) -> None:
        """在这里重写布局方法,确保先更新自身位置和大小"""
        # 设置自己的布局
        super().layout(dx=dx, dy=dy, width=width, height=height)
        # 设置子元素的布局
        self.update_layout()

    def update_layout(self) -> None:
        """在子类型里会重写这个方法,这里只做声明"""
        raise NotImplementedError("update_layout() must be implemented in subclass")

    def bind(self, event_type:EventType) -> None:
        """事件委托,接收事件并冒泡"""
        if event_type not in self.event_listener:
            self.event_listener[event_type] = [self.bubble]

    def unbind(self, event_type:EventType) -> None:
        """事件委托"""
        if event_type in self.event_listener:
            self.event_listener.pop(event_type, None)
