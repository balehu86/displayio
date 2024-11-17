# ./container/free_box.py
from ..core.container import Container

class FreeBox(Container):
    def __init__(self,
                 x = 0, y = 0, width = None, height = None, visibility = True):
        """
        初始化Box容器
        """
        super().__init__(x = x, y = y, width = width, height = height, visibility = visibility)
    
    def add(self, child):
        """
        添加子元素并更新布局
        :param child: 要添加的子元素(可以是容器或widget)
        """
        super().add(child)
        self.update_layout()
    def remove(self, child):
        """
        移除子元素并更新布局
        :param child: 要移除的子元素
        """
        # 获取子元素在children中的索引
        if child in self.children:
            super().remove(child)
            self.update_layout()

    def layout(self, x, y, width, height):
        """
        重写布局方法，确保先更新自身位置和大小
        """
        super().layout(x, y, width, height)
        self.update_layout()

    def _get_min_size(self):
        """
        重写方法
        计算容器所需的最小尺寸
        返回: (min_width, min_height)
        """
        min_width = 0
        min_height = 0

        # 容器没有children，则返回（0，0）.
        # 普通widget没有children，则返回初始化时的值 或者强制resize()的值
        # if not self.children:
        #     min_width = self.width if self.width is not None else 0
        #     min_height = self.height if self.height is not None else 0
        #     return (min_width, min_height)
        
        
        # 获取子元素的相对位置和固定尺寸
        for i, child in enumerate(self.children):
            # 递归获取其最小尺寸
            child_min_width, child_min_height = child._get_min_size()
            
            min_width += child_min_width
            min_height = max(min_height, child_min_height)
            
            # 添加间距
            if i < len(self.children) - 1:
                min_width += self.spacing


        # 如果容器本身设置了固定的width或height，使用较大的值
        if self.width is not None and not self.width_resizable:
            min_width = max(min_width, self.width)
        if self.height is not None and not self.height_resizable:
            min_height = max(min_height, self.height)          
        
        return (min_width, min_height)
    
    def update_layout(self):
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        if not self.children:
            return
            
        # 获取容器的最小所需尺寸
        # 确保容器有足够的空间
        min_width, min_height = self._get_min_size()
        if (min_width > self.width) or (min_height > self.height):
            raise ValueError(f'子元素尺寸大于容器尺寸，请调整子元素的初始化参数。\n    容器宽高{self.width} {self.height},组件所需尺寸{min_width} {min_height}')    
        
        if self.direction == 'h':
            self._layout_horizontal()
        else:
            self._layout_vertical()