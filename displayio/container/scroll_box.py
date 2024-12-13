# ./container/free_box.py
from .container import Container
from ..core.bitmap import Bitmap
from ..core.event import EventType, Event

import micropython # type: ignore

class ScrollBox(Container):
    def __init__(self, 
                 scroll_offset_x=0,
                 scroll_offset_y=0,
                 
                 abs_x=None, abs_y=None,
                 rel_x=None, rel_y=None,
                 width=None, height=None,
                 visibility=True, state=Container.STATE_DEFAULT,
                 background_color=None,
                 transparent_color=None):
        """
        初始化ScrollBox容器, 此容器的children唯一, 且是一个其他类型的容器.
            self.child.children 中的元素只能是具有get_bitmap() 方法的 widget实例
        child的布局采用虚拟位置, 默认dx=0-scroll_offset_x; dy=0-scroll_offset_y
        滚动操作相当于self._bitmap.blit(self.child._bitmap, dx=0-scroll_offset_x, dy=0-scroll_offset_y),
            即, 在child._bitmap 截取当前width * height 的框。

        警告: 此容器接受的事件 必须包含data={'rx':None, 'ry':None, 'dx':None, 'dy':None}, 
            分别表示相对滚动距离和绝对滚动距离
        """
        self.child = None
        # 滚动相关的属性
        # 记录滚动的当前偏移量
        self.scroll_offset_x = scroll_offset_x
        self.scroll_offset_y = scroll_offset_y
        # 是否可以在某个方向上滚动
        self.is_scrollable_x = False
        self.is_scrollable_y = False
        # 滚动范围
        self.scroll_range_x = 0
        self.scroll_range_y = 0
        # 事件监听器
        self.event_listener = {EventType.DRAG_MOVE:[]}

        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         background_color = background_color,
                         transparent_color = transparent_color)

    def add(self, child):
        """向容器中添加元素"""
        self.children.append(child)
        self.child = child
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()

    @micropython.native
    def _get_min_size(self):
        """
        重写方法
        计算容器所需的最小尺寸
        返回: (min_width, min_height)
        """
        # 确保只有一个子元素
        if len(self.children) != 1:
            raise ValueError("ScrollBox must have exactly one child")
        
        # 考虑自身的固定尺寸,如果固定尺寸则取self的尺寸，否则灵活尺寸取0
        min_width = self.width if not self.width_resizable else 0
        min_height = self.height if not self.height_resizable else 0
        
        child_min_width, child_min_height = self.child._get_min_size()

        min_width = max(min_width, child_min_width)
        min_height = max(min_height, child_min_height)
        # 如果rel_value为None则取0, 否则取rel_value
        return (min_width+(self.rel_x or 0), min_height+(self.rel_y or 0))
    
    @micropython.native
    def update_layout(self):
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        if not self.children:
            return

        if len(self.children) != 1:
            raise ValueError("ScrollBox must have exactly one child and be a Container")

        # 获取自己的最小所需尺寸
        min_width, min_height = self._get_min_size()
        # 确保容器有足够的空间,使用实际容器尺寸，而不是最小尺寸        
        if (min_width > self.width) or (min_height > self.height):
            raise ValueError(f'子元素尺寸大于容器尺寸，或有元素超出屏幕范围，请调整子元素的初始化参数。\n',
                            f'容器宽高{self.width} {self.height},组件所需尺寸{min_width} {min_height}')

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

        actual_width = max(self.width, child_min_width) if self.child.width_resizable else self.child.height
        actual_height = max(self.height, child_min_height) if self.child.height_resizable else self.child.width
        # 根据滚动偏移量调整布局
        self.child.layout(dx=0 - self.scroll_offset_x, dy=0 - self.scroll_offset_y,
                          width=actual_width, height=actual_height)
                
    def scroll(self, event: Event):
        """
        滚动方法，x和y为滚动的增量
        """
        if not self.children:
            raise ValueError("ScrollBox have no child")
        rx, ry=event.data['rx'], event.data['ry']
        dx, dy=event.data['dx'], event.data['dy']
        if rx or ry:
            x, y = rx, ry
        if dx or dy:
            x, y = dx, dy
        if (x is None) or (y is None):
            raise ValueError("scroll event data value error, all are None")
        x = x or 0
        y = y or 0
        # 限制水平滚动
        if self.is_scrollable_x:
            self.scroll_offset_x = max(0, min(self.scroll_range_x, self.scroll_offset_x + x))
        # 限制垂直滚动
        if self.is_scrollable_y:
            self.scroll_offset_y = max(0, min(self.scroll_range_y, self.scroll_offset_y + y))
        
        self._content_dirty = True
        self.register_dirty()

    @micropython.native
    def get_bitmap(self):
        """在这维护一个整体buffer。不再单独刷新此滚动容器的子元素,将子元素合并成整体刷新。"""
        if self.visibility:
            if self._content_dirty:
                self._crop_bitmap()
                self._content_dirty = False
            return self._bitmap
        else:
            if self._empty_bitmap is None:
                self._empty_bitmap = Bitmap(self.width,self.height,
                                            transparent_color=self.transparent_color,
                                            format=Bitmap.RGB565)
                self._empty_bitmap.fill_rect(0,0,self.width,self.height,self.background_color)
            return self._empty_bitmap
        
    @micropython.native
    def _crop_bitmap(self):
        """
        创建child的完整位图
        """
        if self._bitmap is None:
            self._bitmap = Bitmap(self.width, self.height, transparent_color=self.transparent_color, format=Bitmap.RGB565)
        
        if self.child._dirty or self.widget_in_dirty_area(self.child):
            self._update_child_bitmap()
            self._bitmap.blit(self.child._bitmap, dx=(-1)*self.scroll_offset_x, dy=(-1)*self.scroll_offset_y)
        if self.child._content_dirty:
            self._update_child_bitmap()
            self.child._content_dirty = False
        self._bitmap.blit(self.child._bitmap, dx=(-1)*self.scroll_offset_x, dy=(-1)*self.scroll_offset_y)


    def _update_child_bitmap(self):
        """全屏刷新"""
        if self.child._dirty:
            self._render_child(self.child) # 获取到完整的child._bitmap        

    def _render_child(self, widget):
        """绘制整个屏幕的buffer"""
        if widget._dirty or self.widget_in_dirty_area(widget):
            if hasattr(widget, 'get_bitmap'):
                bitmap = widget.get_bitmap()
                self.child._bitmap.blit(bitmap, dx=widget.dx, dy=widget.dy)
            widget._dirty = False
        for child in widget.children:
            self._render_child(child)
    
    def widget_in_dirty_area(self, widget):
        pass

    def hide(self):
        """重写 隐藏部件方法"""
        self.visibility = False
        self.register_dirty()
    
    def unhide(self):
        self.visibility = True
        self.register_dirty()
