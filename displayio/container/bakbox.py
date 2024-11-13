from ..core.container import Container

class Box(Container):
    def __init__(self, direction='h', spacing=0, align='start',
                 x = 0, y = 0, width = None, height = None, hidden = False):
        """
        初始化Box容器
        :param direction: 布局方向，'h'为水平，'v'为垂直
        :param spacing: 子元素间距
        :param align: 对齐方式，'start'/'center'/'end'
        :param default_color: 默认填充颜色，用于隐藏元素的区域
        """
        super().__init__(x = x, y = y, width = width, height = height, hidden = hidden)
        self.direction = direction
        self.spacing = spacing
        self.align = align
        # 存储子元素的原始尺寸设置
        self.children_size = []

    def add(self, child):
        """
        添加子元素并更新布局
        :param child: 要添加的子元素(可以是容器或widget)
        """
        super().add(child)
        # 记录子元素的原始尺寸设置
        self.children_size.append([child.width, child.height,child.width_resizable, child.height_resizable])
        self.update_layout()
    def remove(self, child):
        """
        移除子元素并更新布局
        :param child: 要移除的子元素
        """
        # 获取子元素在children中的索引
        if child in self.children:
            index = self.children.index(child)
            # 同步删除children_size中对应的记录
            self.children_size.pop(index)
            super().remove(child)
            self.update_layout()

    def _calculate_flexible_size(self, total_size, fixed_size_sum, flexible_count):
        """
        计算可伸缩元素的尺寸
        :param total_size: 总可用空间
        :param fixed_size_sum: 固定尺寸之和
        :param flexible_count: 可伸缩元素数量
        :return: 每个可伸缩元素应得的尺寸
        """
        if flexible_count == 0:
            return 0
        # 计算剩余空间
        remaining = total_size - fixed_size_sum - self.spacing * (len(self.children) - 1)
        # 平均分配给每个可伸缩元素
        return max(0, remaining // flexible_count)

    def update_layout(self):
        """
        更新容器的布局
        根据方向调用相应的布局函数
        """
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
        max_height = 0
        fixed_width_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定宽度和可伸缩元素数量
        for i, child in enumerate(self.children):
            width, height, width_resizable, height_resizable = self.children_size[i]
            if width is not None:
                fixed_width_sum += width
            else:
                flexible_count += 1

        # 计算可伸缩元素的宽度
        flexible_width = self._calculate_flexible_size(
            self.width, fixed_width_sum, flexible_count)

        # 第二遍遍历：设置实际布局
        for i, child in enumerate(self.children):
            width, height, _, _= self.children_size[i]
            # 确定实际使用的宽度
            actual_width = flexible_width if width is None else width
            # 确定实际使用的高度
            actual_height = self.height if height is None else height

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
            max_height = max(max_height, actual_height)

    def _layout_vertical(self):
        """
        垂直方向的布局处理
        处理None值的情况，计算并分配空间
        """
        y = self.y
        max_width = 0
        fixed_height_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定高度和可伸缩元素数量
        for i, child in enumerate(self.children):
            width, height, width_resizable, height_resizable = self.children_size[i]
            if height is not None:
                fixed_height_sum += height
            else:
                flexible_count += 1

        # 计算可伸缩元素的高度
        flexible_height = self._calculate_flexible_size(
            self.height, fixed_height_sum, flexible_count)

        # 第二遍遍历：设置实际布局
        for i, child in enumerate(self.children):
            width, height, _, _ = self.children_size[i]
            # 确定实际使用的宽度
            actual_width = self.width if width is None else width
            # 确定实际使用的高度
            actual_height = flexible_height if height is None else height

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
            max_width = max(max_width, actual_width)