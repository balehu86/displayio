# ./core/container.py
from .widget import Widget

class Container(Widget):
    def __init__(self,
                 abs_x = None, abs_y = None,
                 rel_x = None, rel_y = None,
                 width = None, height = None,
                 visibility = True):
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility)
        
        # self.dirty_children = []

    def add(self, child):
        """
        向容器中添加元素
        """
        child.parent = self
        self.children.append(child)
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()
    def remove(self, child):
        """
        从容器中移除元素
        """
        child.parent = None
        if child in self.children:
            self.children.remove(child)
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()
    def layout(self,
               dx = 0, dy = 0,
               width = None, height = None):
        """
        重写布局方法，确保先更新自身位置和大小
        """
        # 设置自己的布局
        super().layout(dx = dx, dy = dy,
                       width = width, height = height)
        # 设置子元素的布局
        self.update_layout()
