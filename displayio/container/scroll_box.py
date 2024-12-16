# ./container/free_box.py
from .container import Container
from ..core.bitmap import Bitmap
from ..core.event import EventType

import micropython # type: ignore

class ScrollBox(Container):
    """
    ScrollBox滚动容器类
    继承自Container
    """
    def __init__(self,                 
                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0,
                 width=None, height=None,
                 visibility=True, state=Container.STATE_DEFAULT,
                 background_color=Container.WHITE,
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
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         background_color = background_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        
        self.child = None
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
        self.event_listener = {EventType.SCROLL:[self.scroll],
                               EventType.ROTATE_TICK:[self.scroll],}

    def add(self, child) -> None:
        """向容器中添加元素"""
        self.children.append(child)
        self.child = child
        self.mark_dirty()
        self.register_dirty()
        self.register_layout_dirty()

    @micropython.native
    def update_layout(self) -> None:
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        if not self.children:
            return

        if len(self.children) != 1:
            raise ValueError("ScrollBox must have exactly one child and be a Container")

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

        actual_width = child_min_width if self.child.width_resizable else self.child.width
        actual_height = self.height if self.child.height_resizable else self.child.height
        # 根据滚动偏移量调整布局
        self.child.layout(dx=0 - self.scroll_offset_x, dy=0 - self.scroll_offset_y,
                          width=actual_width, height=actual_height)
                
    def scroll(self,event) -> None:
        """
        滚动方法, x和y为滚动的增量
        """
        print('hellp')
        if not self.children:
            raise ValueError("ScrollBox have no child")
        x = event.data.get('rotate_tick_position', 0)
        y = event.data.get('rotate_tick_position', 0)
        print(x,y)
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
                self._crop_bitmap() # 裁剪child的对应区域
                self._content_dirty = False
            return self._bitmap
        else:
            if self._empty_bitmap is None:
                self._empty_bitmap = Bitmap(self.width,self.height, transparent_color=self.transparent_color, format=self.color_format)
                self._empty_bitmap.fill_rect(0,0,self.width,self.height,self.background_color)
            return self._empty_bitmap
        
    @micropython.native
    def _crop_bitmap(self) -> None:
        """
        裁剪child的完整位图的对应区域
        """
        if self._bitmap is None:
            self._bitmap = Bitmap(self.width, self.height, transparent_color=self.transparent_color, format=self.color_format)
        if self.child._dirty:
            self._update_child_bitmap()
        self._bitmap.blit(self.child._bitmap, dx=(-1)*self.scroll_offset_x, dy=(-1)*self.scroll_offset_y)

    def _update_child_bitmap(self) -> None:
        """更新child的bitmap"""
        if self.child._bitmap is None:
            self.child._bitmap = Bitmap(self.child.width, self.child.height, transparent_color=self.transparent_color, format=self.color_format)
        self._render_child(self.child) # 获取到完整的child._bitmap

    def _render_child(self, widget):
        """绘制整个屏幕的buffer"""
        if widget._dirty:
            widget._dirty = False
            if hasattr(widget, 'get_bitmap'):
                bitmap = widget.get_bitmap()
                self.child._bitmap.blit(bitmap, dx=widget.dx, dy=widget.dy)
                return    
        for child in widget.children:
            self._render_child(child)


    def hide(self):
        """重写 隐藏部件方法"""
        self.visibility = False
        self.register_dirty()
    
    def unhide(self):
        self.visibility = True
        self.register_dirty()

    def bind(self, event_type, callback_func: function) -> None:
        """绑定事件处理器
        
        Args:
            event_type (_EventType_): 事件类型（EventType枚举值）
            callback_func (_function_, optional): 事件处理函数，接收Event对象作为参数. Defaults to None.
        """
        if event_type not in self.event_listener:
            self.event_listener[event_type] = []
        self.event_listener[event_type].append(callback_func)

    def unbind(self, event_type, callback_func: function=None) -> None:
        """解绑事件处理器
        
        Args:
            event_type (_EventType_): 事件类型（EventType枚举值）
            callback_func (_function_, optional): 事件处理函数，接收Event对象作为参数. Defaults to None.
        """
        if event_type in self.event_listener:
            if callback_func is None:
                self.event_listener[event_type] = []
            else:
                self.event_listener[event_type] = [
                    cb for cb in self.event_listener[event_type] 
                    if cb != callback_func
                ]