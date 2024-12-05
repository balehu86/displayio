# ./core/container.py
from ..core.widget import Widget

class Container(Widget):
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=None, rel_y=None,
                 width=None, height=None,
                 visibility=True,enabled=True,
                 background_color=None,
                 transparent_color=Widget.PINK):
        
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility, enabled = enabled,
                         background_color = background_color,
                         transparent_color = transparent_color)
        
        # self.dirty_children = []

    def add(self, *childs):
        """向容器中添加元素"""
        for child in childs:
            child.parent=self
        self.children.extend(childs)
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()

    def insert(self,index,child):
        self.children.insert(index,child)
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()

    def remove(self, *childs):
        """从容器中移除元素"""
        for child in childs:
            child.parent = None
            if child in self.children:
                self.children.remove(child)
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()

    def clear(self):
        self.children.clear()

    def layout(self, dx=0, dy=0, width=None, height=None):
        """重写布局方法，确保先更新自身位置和大小"""
        # 设置自己的布局
        super().layout(dx=dx, dy=dy, width=width, height=height)
        # 设置子元素的布局
        self.update_layout()

    def update_layout(self):
        pass

    def bind(self,event_type, handler):
        for child in self.children:
            child.bind(event_type, handler)

    def unbind(self, event_type, handler=None):
        for child in self.children:
            child.unbind(event_type, handler)