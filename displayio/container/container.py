# ./core/container.py
from ..core.widget import Widget

class Container(Widget):
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=None, rel_y=None,
                 width=None, height=None,
                 visibility=True, state=Widget.STATE_DEFAULT,
                 background_color=None,
                 transparent_color=Widget.PINK):
        
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         background_color = background_color,
                         transparent_color = transparent_color)
        
        # 脏区域列表,用来处理遮挡问题,每个列表为 [x, y, width, height]
        self.dirty_area_list = [[0,0,0,0]]
        

    def add(self, *childs):
        """向容器中添加元素"""
        for child in childs:
            child.parent=self
        self.children.extend(childs)
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()

    def insert(self,index,child):
        """在指定位置插入元素"""
        self.children.insert(index,child)
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()

    def replace(self,old_child,new_child):
        """将 old_child 替换换为 new_child"""
        self.children=list(map(lambda child: new_child if child==old_child else child, self.children))
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
        """清空容器中所有元素"""
        self.mark_dirty()
        self.children.clear()
        self.register_dirty()
        self.register_layout_dirty()

    def layout(self, dx=0, dy=0, width=None, height=None):
        """在这里重写布局方法,确保先更新自身位置和大小"""
        # 设置自己的布局
        super().layout(dx=dx, dy=dy, width=width, height=height)
        # 设置子元素的布局
        self.update_layout()

    def update_layout(self):
        """在子类型里会重写这个方法,这里只做声明"""
        pass

    def bind(self,event_type, handler):
        """事件委托,由容器为每个子元素绑定事件监听"""
        for child in self.children:
            child.bind(event_type, handler)

    def unbind(self, event_type, handler=None):
        for child in self.children:
            child.unbind(event_type, handler)

    def hide(self):
        """隐藏容器"""
        self.visibility = False
        self.register_dirty()
        for child in self.children:
            child.hide()

    def unhide(self):
        """取消隐藏容器"""
        self.visibility = True
        self.register_dirty()
        for child in self.children:
            child.hide().unhide()

    def mark_dirty(self):
        """向下通知 脏"""
        self._dirty = True
        for child in self.children:
            child.mark_dirty()

    def event_handler(self, event):
        """处理事件
        首先检查容器自己是否有对应的处理器，如果有则看自己是否处理，不处理则传递给子组件
        """
        resault = super().event_handler(event)
        # 如果事件未被处理，传递给子组件
        if not resault:
            for child in reversed(self.children): # 从上到下传递
                if event.is_handled(): # 未被处理
                    break
                else: # 已处理
                    child.event_handler(event)