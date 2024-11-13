from ..core.container import Container

class Box(Container):
    def __init__(self, direction='h', spacing=0, align='start',
                 x=0, y=0, width=None, height=None, hidden=False):
        """
        初始化Box容器
        :param direction: 布局方向，'h'为水平，'v'为垂直
        :param spacing: 子元素间距
        :param align: 对齐方式，'start'/'center'/'end'
        """
        super().__init__(x=x, y=y, width=width, height=height, hidden=hidden)
        self.direction = direction
        self.spacing = spacing
        self.align = align

    def _get_min_size(self):
        """
        计算容器所需的最小尺寸
        返回: (min_width, min_height)
        """
        min_width = 0
        min_height = 0
        
        if not self.children:
            return (0, 0)
            
        if self.direction == 'h':
            # 水平布局：宽度累加，高度取最大值
            for i, child in enumerate(self.children):
                child_width = child.width if child.width is not None else 0
                child_height = child.height if child.height is not None else 0
                
                # 如果是容器，递归获取其最小尺寸
                if isinstance(child, Container):
                    child_min_width, child_min_height = child._get_min_size()
                    child_width = max(child_width, child_min_width)
                    child_height = max(child_height, child_min_height)
                
                min_width += child_width
                min_height = max(min_height, child_height)
                
                # 添加间距
                if i < len(self.children) - 1:
                    min_width += self.spacing
        else:
            # 垂直布局：高度累加，宽度取最大值
            for i, child in enumerate(self.children):
                child_width = child.width if child.width is not None else 0
                child_height = child.height if child.height is not None else 0
                
                # 如果是容器，递归获取其最小尺寸
                if isinstance(child, Container):
                    child_min_width, child_min_height = child._get_min_size()
                    child_width = max(child_width, child_min_width)
                    child_height = max(child_height, child_min_height)
                
                min_width = max(min_width, child_width)
                min_height += child_height
                
                # 添加间距
                if i < len(self.children) - 1:
                    min_height += self.spacing
                    
        return (min_width, min_height)

    def _distribute_space(self, available_space, min_sizes, resizable_count):
        """
        分配可用空间给子元素
        :param available_space: 可用总空间
        :param min_sizes: 子元素最小尺寸列表
        :param resizable_count: 可调整大小的元素数量
        返回: 分配给每个元素的尺寸列表
        """
        if resizable_count == 0:
            return min_sizes
            
        total_min_size = sum(min_sizes)
        spacing_size = self.spacing * (len(min_sizes) - 1)
        extra_space = max(0, available_space - total_min_size - spacing_size)
        
        # 计算每个可调整大小的元素可以得到的额外空间
        extra_per_resizable = extra_space // resizable_count
        
        # 分配空间
        distributed_sizes = []
        for i, min_size in enumerate(min_sizes):
            if i < len(self.children) and (
                (self.direction == 'h' and self.children[i].width_resizable) or
                (self.direction == 'v' and self.children[i].height_resizable)
            ):
                distributed_sizes.append(min_size + extra_per_resizable)
            else:
                distributed_sizes.append(min_size)
                
        return distributed_sizes

    def layout(self, x, y, width, height):
        """
        重写布局方法，确保先更新自身位置和大小
        """
        super().layout(x, y, width, height)
        self.update_layout()
        
    def update_layout(self):
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        if not self.children:
            return
            
        # 获取容器的最小所需尺寸
        min_width, min_height = self._get_min_size()
        
        # 确保容器有足够的空间
        self.width = max(min_width, self.width if self.width is not None else min_width)
        self.height = max(min_height, self.height if self.height is not None else min_height)
        
        if self.direction == 'h':
            self._layout_horizontal()
        else:
            self._layout_vertical()

    def _layout_horizontal(self):
        """
        水平方向的布局处理
        """
        # 收集子元素的最小宽度和可调整性
        min_widths = []
        resizable_count = 0
        
        for child in self.children:
            if isinstance(child, Container):
                min_width, _ = child._get_min_size()
            else:
                min_width = child.width if child.width is not None else 0
            min_widths.append(min_width)
            if child.width_resizable:
                resizable_count += 1
                
        # 分配水平空间
        widths = self._distribute_space(self.width, min_widths, resizable_count)
        
        # 布局每个子元素
        current_x = self.x
        for i, child in enumerate(self.children):
            width = widths[i]
            
            # 计算高度和垂直位置
            if child.height is None or child.height_resizable:
                height = self.height
            else:
                height = child.height
                
            # 计算垂直对齐位置
            if self.align == 'start':
                y = self.y
            elif self.align == 'center':
                y = self.y + (self.height - height) // 2
            else:  # end
                y = self.y + self.height - height
                
            # 更新子元素布局
            child.layout(current_x, y, width, height)
            current_x += width + self.spacing

    def _layout_vertical(self):
        """
        垂直方向的布局处理
        """
        # 收集子元素的最小高度和可调整性
        min_heights = []
        resizable_count = 0
        
        for child in self.children:
            if isinstance(child, Container):
                _, min_height = child._get_min_size()
            else:
                min_height = child.height if child.height is not None else 0
            min_heights.append(min_height)
            if child.height_resizable:
                resizable_count += 1
                
        # 分配垂直空间
        heights = self._distribute_space(self.height, min_heights, resizable_count)
        
        # 布局每个子元素
        current_y = self.y
        for i, child in enumerate(self.children):
            height = heights[i]
            
            # 计算宽度和水平位置
            if child.width is None or child.width_resizable:
                width = self.width
            else:
                width = child.width
                
            # 计算水平对齐位置
            if self.align == 'start':
                x = self.x
            elif self.align == 'center':
                x = self.x + (self.width - width) // 2
            else:  # end
                x = self.x + self.width - width
                
            # 更新子元素布局
            child.layout(x, current_y, width, height)
            current_y += height + self.spacing

    def add(self, child):
        """
        添加子元素并更新布局
        """
        super().add(child)
        self.update_layout()

    def remove(self, child):
        """
        移除子元素并更新布局
        """
        super().remove(child)
        self.update_layout()