# ./core/container.py
from .widget import Widget

class Container(Widget):
    def __init__(self,
                 abs_x = 0,abs_y = 0,
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
    
