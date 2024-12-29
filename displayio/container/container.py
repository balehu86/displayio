# ./core/container.py
from ..core.base_widget import BaseWidget
from ..core.event import Event # type hint
from ..core.dirty import MergeRegionSystem # type hint
from ..core.event import EventType

from heapq import heappush

class Container(BaseWidget):
    """
    容器基类
    继承自BaseWidget
    """
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=BaseWidget.STATE_DEFAULT,
                 background_color=BaseWidget.DARK,
                 transparent_color=BaseWidget.PINK,
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
                         background_color = background_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        # 容器的子元素
        self.children = []
        
    def add(self, *childs: BaseWidget|'Container') -> None:
        """向容器中添加元素"""
        for child in childs:
            child.parent=self
            child.set_dirty_system(self.dirty_system)  # 设置相同的脏区域管理器
            heappush(self.children, child)

        self.mark_dirty()
        self.dirty_system.layout_dirty = True

    def remove(self, *childs: BaseWidget|'Container') -> None:
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

    def bind(self, event_type:EventType) -> None:
        """事件委托,接收事件并冒泡"""
        if event_type not in self.event_listener:
            self.event_listener[event_type] = [self.bubble]
        self.event_listener[event_type].append(self.bubble)

    def unbind(self, event_type:EventType) -> None:
        """事件委托"""
        if event_type in self.event_listener:
            self.event_listener.pop(event_type)

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

    def bubble(self, event:Event) -> None:
        """事件冒泡
        首先检查容器自己是否有对应的处理器，如果有则看自己是否处理，不处理则传递给子组件
        Args:
            event: Event类实例
        """
        # 尝试捕获
        # 如果事件未被捕获，传递给子组件
        if self.catch(event):
            self.handle(event)
        else:
            for child in self.children: # 传递
                if event.is_handled(): # 已被处理
                    break
                else: # 未处理
                    child.bubble(event)

    def set_dirty_system(self, dirty_system:MergeRegionSystem):
        """递归设置脏区域管理器"""
        self.dirty_system = dirty_system
        for child in self.children:
            child.set_dirty_system(dirty_system)

    def focus(self):
        """元素聚焦,会将元素内所有元素调暗0.1"""
        super().focus()
        for child in self.children:
            child.focus()
    
    def unfocus(self):
        """取消元素聚焦"""
        super().unfocus()
        for child in self.children:
            child.unfocus()