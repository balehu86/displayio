# ./container/free_box.py
from .container import Container

import micropython # type: ignore

class FreeBox(Container):
    """
    FreeBox滚动容器类
    继承自Container
    """
    __slots__ = ()
    
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=Container.STATE_DEFAULT,
                 background_color=Container.DARK,
                 transparent_color=Container.PINK,
                 color_format=Container.RGB565):
        """
        初始化FreeBox容器
        建议: 不建议此容器初始化width和height

        继承Container的所有参数,额外添加:
            pass
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         background_color = background_color,
                         transparent_color = transparent_color,
                         color_format = color_format)

    @micropython.native
    def _get_min_size(self) -> tuple[int, int]:
        """
        重写方法
        计算容器所需的最小尺寸
        返回: (min_width, min_height)
        """
        # 考虑自身的固定尺寸,如果固定尺寸则取self的尺寸，否则灵活尺寸取0
        min_width = self.width if not self.width_resizable else 0
        min_height = self.height if not self.height_resizable else 0

        # 获取子元素的相对位置和固定尺寸
        for child in self.children:
            # 递归获取其最小尺寸
            child_min_width, child_min_height = child._get_min_size()
            
            min_width = max(min_width, child_min_width)
            min_height = max(min_height, child_min_height)

        return min_width+self.rel_x, min_height+self.rel_y
    
    @micropython.native
    def update_layout(self) -> None:
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        if not self.children:
            return
        
        # 获取自己的最小所需尺寸
        min_width, min_height = self._get_min_size()
        # 确保容器有足够的空间,使用实际容器尺寸，而不是最小尺寸        
        if (min_width > self.width+self.rel_x) or (min_height > self.height+self.rel_y):
            raise ValueError(f'子元素尺寸大于free容器尺寸,或有元素超出屏幕范围,请调整子元素的初始化参数.\n    容器宽高{self.width} {self.height},组件所需尺寸{min_width} {min_height}')
         
        for child in self.children:
            child_min_width, child_min_height = child._get_min_size()
            # 确定实际使用的宽度,如果灵活尺寸则取灵活尺寸，否则取child_min_width固定尺寸
            actual_width = self.width if child.width_resizable else child_min_width
            # 确定实际使用的高度
            actual_height = self.height if child.height_resizable else child_min_height
            # 应用布局
            child.layout(dx=self.dx, dy=self.dy, width=actual_width, height=actual_height)
    