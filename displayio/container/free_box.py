# ./container/free_box.py
from .container import Container

import micropython # type: ignore

class FreeBox(Container):
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=None, rel_y=None,
                 width=None, height=None,
                 visibility=True, enabled=True,
                 background_color=None,
                 transparent_color=None):
        """
        初始化FreeBox容器
        警告：不建议此容器初始化width和height
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility, enabled = enabled,
                         background_color = background_color,
                         transparent_color = transparent_color)

    @micropython.native
    def _get_min_size(self):
        """
        重写方法
        计算容器所需的最小尺寸
        返回: (min_width, min_height)
        """
        min_width = 0
        min_height = 0
        # 考虑自身的固定尺寸
        if not self.width_resizable:
            min_width = self.width
        if not self.height_resizable:
            min_height = self.height

        self_rel_x = self.rel_x if self.rel_x is not None else 0
        self_rel_y = self.rel_y if self.rel_y is not None else 0
        
        # 获取子元素的相对位置和固定尺寸
        for child in self.children:
            # 递归获取其最小尺寸
            child_min_width, child_min_height = child._get_min_size()
            
            min_width = max(min_width, child_min_width)
            min_height = max(min_height, child_min_height)

        return (min_width+self_rel_x, min_height+self_rel_y)
    
    @micropython.native
    def update_layout(self):
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        if not self.children:
            return
        
        # 获取自己的最小所需尺寸
        min_width, min_height = self._get_min_size()

        # 确保容器有足够的空间
        # 使用实际容器尺寸，而不是最小尺寸        
        if (min_width > self.width) or (min_height > self.height):
            raise ValueError(f'子元素尺寸大于容器尺寸，或有元素超出屏幕范围，请调整子元素的初始化参数。\n'
                            f'容器宽高{self.width} {self.height},组件所需尺寸{min_width} {min_height}')
         
        for child in self.children:
            # 应用布局,元素的layout()会将元素自己_layout_dirty = False
            actual_width, actual_height = child._get_min_size()
            if child.width_resizable:
                actual_width = self.width
            if child.height_resizable:
                actual_height = self.height
            child.layout(dx = self.dx, dy = self.dy, 
                    width = actual_width, height = actual_height)
    