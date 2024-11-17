# ./container/box.py
from ..core.container import Container

class Box(Container):
    def __init__(self, direction='h', spacing=0, align='start', flex = 0,
                 abs_x=0,abs_y=0,x = 0, y = 0, width = None, height = None, visibility = True):
        """
        初始化Box容器
        :param direction: 布局方向，'h'为水平，'v'为垂直
        :param spacing: 子元素间距
        :param align: 对齐方式，'start'/'center'/'end'
        :param flex: 分配空间的比例
        """
        super().__init__(abs_x=abs_x,abs_y=abs_y,x = x, y = y, width = width, height = height, visibility = visibility)

        self.direction = direction
        self.spacing = spacing
        self.align = align
        self.flex = flex

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
        
        if self.direction == 'h':
            # 水平布局：宽度累加，高度取最大值
            for i, child in enumerate(self.children):
                # 递归获取其最小尺寸
                child_min_width, child_min_height = child._get_min_size()
                
                min_width += child_min_width
                min_height = max(min_height, child_min_height)
                
                # 添加间距
                if i < len(self.children) - 1:
                    min_width += self.spacing
        else: # direction == 'v'
            # 垂直布局：高度累加，宽度取最大值
            for i, child in enumerate(self.children):
                # 递归获取其最小尺寸
                child_min_width, child_min_height = child._get_min_size()
                
                min_width = max(min_width, child_min_width)
                min_height += child_min_height
                
                # 添加间距
                if i < len(self.children) - 1:
                    min_height += self.spacing

        # 如果容器本身设置了固定的width或height，使用较大的值
        if self.width is not None and not self.width_resizable:
            min_width = max(min_width, self.width)
        if self.height is not None and not self.height_resizable:
            min_height = max(min_height, self.height)          
        
        return (min_width, min_height)

    def _calculate_flexible_size(self, total_size, fixed_size_sum, flexible_count):
        """
        计算可伸缩元素的尺寸
        :param total_size: 总可用空间
        :param fixed_size_sum: 固定尺寸之和
        :param flexible_count: 可伸缩元素数量
        :return: 每个可伸缩元素应得的尺寸
        """

        # 计算剩余空间
        remaining = total_size - fixed_size_sum - self.spacing * (len(self.children) - 1)

        if remaining < 0:
            raise ValueError(f'计算可伸缩元素尺寸时，剩余空间不够。\n    总可用{total_size},固定尺寸实际占用{fixed_size_sum}')
        
        # 平均分配给每个可伸缩元素
        if flexible_count == 0:
            return 0
        return max(0, remaining // flexible_count)

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

    def _layout_horizontal(self):
        """
        水平方向的布局处理
        处理None值的情况，计算并分配空间
        """
        x = self.x
        fixed_width_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定宽度和可伸缩元素数量
        for child in self.children:
            width = child.width
            width_resizable = child.width_resizable
            if width_resizable:
                flexible_count += 1
            else:
                fixed_width_sum += width

        # 计算可伸缩元素的宽度
        flexible_width = self._calculate_flexible_size(
            self.width, fixed_width_sum, flexible_count)

        # 第二遍遍历：设置实际布局
        for child in self.children:
            width=child.width
            height=child.height
            width_resizable=child.width_resizable
            height_resizable=child.height_resizable
            # 确定实际使用的宽度
            actual_width = flexible_width if width_resizable else width
            # 确定实际使用的高度
            actual_height = self.height if height_resizable else height

            # 根据对齐方式计算y坐标
            if self.align == 'start':
                y = self.y
            elif self.align == 'center':
                y = self.y + (self.height - actual_height) // 2
            else:  # end
                y = self.y + self.height - actual_height

            # 应用布局
            child.layout(x, y, actual_width, actual_height)
            x += actual_width + self.spacing

    def _layout_vertical(self):
        """
        垂直方向的布局处理
        处理None值的情况，计算并分配空间
        """
        y = self.y
        fixed_height_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定高度和可伸缩元素数量
        for child in self.children:
            height = child.height
            height_resizable = child.height_resizable
            if height_resizable:
                flexible_count += 1
            else:
                fixed_height_sum += height

        # 计算可伸缩元素的高度
        flexible_height = self._calculate_flexible_size(
            self.height, fixed_height_sum, flexible_count)

        # 第二遍遍历：设置实际布局
        for child in self.children:
            width=child.width
            height=child.height
            width_resizable=child.width_resizable
            height_resizable=child.height_resizable
            # 确定实际使用的宽度
            actual_width = self.width if width_resizable else width
            # 确定实际使用的高度
            actual_height = flexible_height if height_resizable else height

            # 根据对齐方式计算x坐标
            if self.align == 'start':
                x = self.x
            elif self.align == 'center':
                x = self.x + (self.width - actual_width) // 2
            else:  # end
                x = self.x + self.width - actual_width

            # 应用布局
            child.layout(x, y, actual_width, actual_height)
            y += actual_height + self.spacing