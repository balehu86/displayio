# ./core/container.py
from .widget import Widget

class Container(Widget):
    def __init__(self,x = 0, y = 0, width = None, height = None, visibility = True):
        super().__init__(x = x, y = y, width = width, height = height, visibility = visibility)

        self.children = []
        # self.dirty_children = []

    def add(self, child):
        child.parent = self
        self.children.append(child)
        self.mark_dirty()
        self.register_dirty()
    def remove(self,child):
        child.parent = None
        self.children.remove(child)
        self.mark_dirty()
        self.register_dirty()