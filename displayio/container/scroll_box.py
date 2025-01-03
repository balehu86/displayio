# ./container/free_box.py
from .container import Container
from ..core.bitmap import Bitmap
from ..core.event import EventType
from ..core.dirty import MergeRegionSystem, BoundBoxSystem
from ..widget.widget import Widget # type hint

import micropython # type: ignore

class ScrollBox(Container):
    """
    ScrollBox滚动容器类
    继承自Container
    """
    __slots__ = ('scroll_dirty_system', 'child'
                 'scroll_offset_x', 'scroll_offset_y',
                 'is_scrollable_x', 'is_scrollable_y',
                 'scroll_range_x', 'scroll_range_y')

    def __init__(self,                 
                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=Container.STATE_DEFAULT,
                 default_color=Container.DARK,
                 transparent_color=Container.PINK,
                 color_format=Container.RGB565):
        """
        初始化ScrollBox容器, 此容器的children唯一, 且是一个其他类型的容器.
            self.child.children 中的元素只能是具有get_bitmap() 方法的 widget实例
        child的布局采用虚拟位置, 默认dx=0-scroll_offset_x; dy=0-scroll_offset_y
        滚动操作相当于self._bitmap.blit(self.child._bitmap, dx=0-scroll_offset_x, dy=0-scroll_offset_y),
            即, 在child._bitmap 截取当前width * height 的框。

        警告: 此容器接受的事件 必须包含data={'rx':None, 'ry':None, 'dx':None, 'dy':None}, 
            分别表示相对滚动距离和绝对滚动距离

        继承Container的所有参数,额外添加:
            pass
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         default_color = default_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        # 预创建bitmap对象
        self._bitmap = Bitmap(self, transparent_color=transparent_color)
        self._empty_bitmap = Bitmap(self, transparent_color=transparent_color)
        # 使用实例ID作为唯一标识
        self.child = None
        # 创建独立的脏区域管理器
        self.scroll_dirty_system = BoundBoxSystem(name=f'ScrollBox_{id(self)}',widget=self)
        # 滚动相关的属性
        # 记录滚动的当前偏移量
        self.scroll_offset_x = 0
        self.scroll_offset_y = 0
        # 是否可以在某个方向上滚动
        self.is_scrollable_x = False
        self.is_scrollable_y = False
        # 滚动范围
        self.scroll_range_x = 0
        self.scroll_range_y = 0
        # 事件监听器
        self.event_listener = {EventType.SCROLL_UP:[self.scroll],
                               EventType.SCROLL_DOWN:[self.scroll],
                               EventType.SCROLL_LEFT:[self.scroll],
                               EventType.SCROLL_RIGHT:[self.scroll]}

    def add(self, child:Container) -> None:
        """向滚动容器中添加元素"""
        assert self.child is None, "scroll must have one child"
        child.parent = self
        child._bitmap = Bitmap(child, transparent_color=self.transparent_color)
        # 递归设置独立的脏区域管理器
        child.set_dirty_system(self.scroll_dirty_system)
        child.set_default_color(self.default_color)
        self.child = child
        self.children.append(child) # 因为事件传递需要，所以保留此项
        self._dirty = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
        self.dirty_system.layout_dirty = True

    def remove(self, child:Container=None):
        """从滚动容器中移除元素"""
        if child == self.child or child == None:
            self.child._bitmap=None
            self.children.clear() # 因为事件传递需要，所以保留此项
            self.child.parent = None
            # 恢复默认的脏区域管理器
            self.child.set_dirty_system(MergeRegionSystem())
            self.child = None
        self.dirty_system.layout_dirty = True

    @micropython.native
    def update_layout(self) -> None:
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        # 获取子元素的最小尺寸
        child_min_width, child_min_height = self.child._get_min_size()

        # 确定水平滚动性
        self.is_scrollable_x = child_min_width > self.width
        if self.is_scrollable_x:
            self.scroll_range_x = child_min_width - self.width
        else:
            self.scroll_range_x = 0
            self.scroll_offset_x = 0
        # 确定垂直滚动性
        self.is_scrollable_y = child_min_height > self.height
        if self.is_scrollable_y:
            self.scroll_range_y = child_min_height - self.height
        else:
            self.scroll_range_y = 0
            self.scroll_offset_y = 0

        actual_width = self.width if self.child.width_resizable else self.child.width
        actual_height = self.height if self.child.height_resizable else self.child.height
        # 根据滚动偏移量调整布局
        self.child.layout(dx=0, dy=0, width=actual_width, height=actual_height)
                
    def scroll(self, widget, event) -> None:
        """
        滚动方法, x和y为滚动的增量
        """
        # 限制水平滚动和垂直滚动
        if event.type == EventType.SCROLL_UP:
            self.scroll_offset_x = max(0, min(self.scroll_range_x, self.scroll_offset_x + 5)) if self.is_scrollable_x else 0
        if event.type == EventType.SCROLL_DOWN:
            self.scroll_offset_x = max(0, min(self.scroll_range_x, self.scroll_offset_x - 5)) if self.is_scrollable_x else 0
        if event.type == EventType.SCROLL_RIGHT:
            self.scroll_offset_y = max(0, min(self.scroll_range_y, self.scroll_offset_y + 5)) if self.is_scrollable_y else 0
        if event.type == EventType.SCROLL_LEFT:
            self.scroll_offset_y = max(0, min(self.scroll_range_y, self.scroll_offset_y - 5)) if self.is_scrollable_y else 0
        
        self._dirty = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    @micropython.native
    def get_bitmap(self):
        """在这维护一个整体buffer。不再单独刷新此滚动容器的子元素,将子元素合并成整体刷新。"""
        if self.visibility:
            if self._dirty or self.scroll_dirty_system.dirty:
                self._crop_bitmap() # 裁剪child的对应区域
                self._dirty = False
            return self._bitmap
        else:
            self._empty_bitmap.init(color=0x0000)
            return self._empty_bitmap
        
    @micropython.native
    def _crop_bitmap(self) -> None:
        """裁剪child的完整位图的对应区域"""
        self._bitmap.init()
        self._update_child_bitmap()
        self._bitmap.blit(self.child._bitmap, dx=(-1)*self.scroll_offset_x, dy=(-1)*self.scroll_offset_y)

    def _update_child_bitmap(self) -> None:
        """更新child的bitmap"""
        if self.scroll_dirty_system.dirty:
            self.child._bitmap.init()
            self._render_child_tree(self.child) # 获取到完整的child._bitmap
            
            self._dirty = True
            self.dirty_system.add(self.dx, self.dy, self.width, self.height)
            
            self.scroll_dirty_system.clear()

    def _render_child_tree(self, widget:Widget):
        """绘制整个屏幕的buffer"""
        if widget.widget_in_dirty_area():
            if hasattr(widget, 'get_bitmap'):
                bitmap = widget.get_bitmap()
                self.child._bitmap.blit(bitmap, dx=widget.dx, dy=widget.dy)
            else:
                for child in widget.children:
                    self._render_child_tree(child)

    def hide(self):
        """重写 隐藏部件方法"""
        self.visibility = False
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
    
    def unhide(self):
        """重写 取消隐藏部件"""
        self.visibility = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    def set_dirty_system(self, dirty_system:MergeRegionSystem):
        """重写set_dirty_system,以适应scroll_box"""
        self.dirty_system = dirty_system
    
