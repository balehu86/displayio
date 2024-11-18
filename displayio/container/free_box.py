# ./container/free_box.py
from ..core.container import Container

class FreeBox(Container):
    def __init__(self,
                 abs_x = 0,abs_y = 0,
                 rel_x = None, rel_y = None,
                 width = None, height = None,
                 visibility = True):
        """
        初始化Box容器
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility)
    

    def layout(self,
               dx = 0, dy = 0,
               width = None, height = None):
        """
        重写布局方法，确保先更新自身位置和大小
        """
        super().layout(dx = dx, dy = dy,
                       width = width, height = height)
        self.update_layout()

    def _get_min_size(self):
        """
        重写方法
        计算容器所需的最小尺寸
        返回: (min_width, min_height)
        """
        min_width = 0
        min_height = 0
    
        # 获取子元素的相对位置和固定尺寸
        for child in self.children:
            # 递归获取其最小尺寸
            child_min_width, child_min_height = child._get_min_size()
            
            min_width += child_min_width + child.rel_x
            min_height += child_min_height + child.rel_y
            

        # 如果容器本身设置了固定的width或height，使用较大的值
        if not self.width_resizable:
            min_width = max(min_width, self.width)
        if not self.height_resizable:
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
            raise ValueError(f'子元素尺寸大于容器尺寸，或有元素超出屏幕范围，请调整子元素的初始化参数。\n    容器宽高{self.width} {self.height},组件所需尺寸{min_width} {min_height}')    
        

        for child in self.children:
            dx = child.abs_x if child.rel_x is None else (self.dx + child.rel_x)
            dy = child.abs_y if child.rel_y is None else (self.dy + child.rel_y)
            child.layout(dx = dx, dy = dy)