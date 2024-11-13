from ..core.container import Container

class ScrollBox(Container):
    def __init__(self, direction='v', spacing=0, align='start'):
        """
        初始化可滚动容器
        :param direction: 滚动方向，'v'为垂直滚动，'h'为水平滚动
        :param spacing: 子元素间距
        :param align: 对齐方式，'start'/'center'/'end'
        """
        super().__init__()
        self.direction = direction
        self.spacing = spacing
        self.align = align
        # 存储子元素的原始尺寸设置
        self.children_size = []
        
        # 滚动相关属性
        self.scroll_position = 0  # 当前滚动位置
        self.content_size = 0     # 内容总大小
        self.viewport_size = 0    # 可视区域大小
        self.min_scroll = 0       # 最小滚动位置
        self.max_scroll = 0       # 最大滚动位置

    def add(self, child):
        """
        添加子元素并更新布局
        :param child: 要添加的子元素
        """
        super().add(child)
        self.children_size.append([child.width, child.height])
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
    def scroll_to(self, position):
        """
        滚动到指定位置
        :param position: 目标滚动位置
        """
        # 确保滚动位置在有效范围内
        self.scroll_position = max(self.min_scroll, min(position, self.max_scroll))
        self.update_layout()

    def scroll_by(self, delta):
        """
        相对滚动
        :param delta: 滚动距离
        """
        self.scroll_to(self.scroll_position + delta)

    def _calculate_content_size(self):
        """
        计算内容总大小
        :return: 内容在滚动方向上的总大小
        """
        if not self.children:
            return 0

        total_spacing = self.spacing * (len(self.children) - 1)
        total_size = 0

        for i, child in enumerate(self.children):
            width, height = self.children_size[i]
            if self.direction == 'v':
                size = height if height is not None else self.height
            else:
                size = width if width is not None else self.width
            total_size += size

        return total_size + total_spacing

    def _layout_vertical(self):
        """
        垂直方向的滚动布局
        """
        # 计算内容总高度和可视区域高度
        self.content_size = self._calculate_content_size()
        self.viewport_size = self.height
        
        # 更新最大滚动范围
        self.max_scroll = max(0, self.content_size - self.viewport_size)
        
        # 确保滚动位置有效
        self.scroll_position = max(self.min_scroll, min(self.scroll_position, self.max_scroll))
        
        # 开始布局
        y = self.y - self.scroll_position
        
        for i, child in enumerate(self.children):
            width, height = self.children_size[i]
            actual_width = self.width if width is None else width
            actual_height = child.height if height is not None else child.minimum_height
            
            # 判断是否在可视区域内
            if y + actual_height >= self.y and y <= self.y + self.height:
                # 根据对齐方式计算x坐标
                if self.align == 'start':
                    x = self.x
                elif self.align == 'center':
                    x = self.x + (self.width - actual_width) // 2
                else:  # end
                    x = self.x + self.width - actual_width
                
                # 应用布局
                child.layout(x, y, actual_width, actual_height)
            else:
                # 不在可视区域内的元素可以设置为不可见或最小化
                child.layout(self.x, y, actual_width, actual_height)
            
            y += actual_height + self.spacing

    def _layout_horizontal(self):
        """
        水平方向的滚动布局
        """
        # 计算内容总宽度和可视区域宽度
        self.content_size = self._calculate_content_size()
        self.viewport_size = self.width
        
        # 更新最大滚动范围
        self.max_scroll = max(0, self.content_size - self.viewport_size)
        
        # 确保滚动位置有效
        self.scroll_position = max(self.min_scroll, min(self.scroll_position, self.max_scroll))
        
        # 开始布局
        x = self.x - self.scroll_position
        
        for i, child in enumerate(self.children):
            width, height = self.children_size[i]
            actual_width = child.width if width is not None else child.minimum_width
            actual_height = self.height if height is None else height
            
            # 判断是否在可视区域内
            if x + actual_width >= self.x and x <= self.x + self.width:
                # 根据对齐方式计算y坐标
                if self.align == 'start':
                    y = self.y
                elif self.align == 'center':
                    y = self.y + (self.height - actual_height) // 2
                else:  # end
                    y = self.y + self.height - actual_height
                
                # 应用布局
                child.layout(x, y, actual_width, actual_height)
            else:
                # 不在可视区域内的元素可以设置为不可见或最小化
                child.layout(x, y, actual_width, actual_height)
            
            x += actual_width + self.spacing

    def update_layout(self):
        """
        更新容器的布局
        根据方向调用相应的布局函数
        """
        if self.direction == 'v':
            self._layout_vertical()
        else:
            self._layout_horizontal()

    def handle_scroll(self, event):
        """
        处理滚动事件
        :param event: 滚动事件，包含delta属性表示滚动距离
        """
        self.scroll_by(event.delta)