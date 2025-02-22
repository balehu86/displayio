# ./container/box.py
from .container import Container

import micropython # type: ignore

class FlexBox(Container):
    """
    FlexBox弹性容器类
    继承自Container
    """
    __slots__ = ('direction', 'spacing', 'align', 'reverse')

    def __init__(self,
                 direction=Container.HORIZONTAL, spacing=0, align=Container.ALIGN_START, reverse=False,

                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=Container.STATE_DEFAULT,
                 transparent_color=Container.PINK,
                 background=Container.DARK,
                 color_format=Container.RGB565):
        """
        初始化FlexBox容器

        继承Container的所有参数,额外添加:
            direction: 布局方向
            spacing: 子元素间距
            align: 对齐方式，'start'/'center'/'end'
            reverse: 元素排列顺序,False 为顺序排列,True为倒序
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         transparent_color = transparent_color,
                         background = background,
                         color_format = color_format)

        self.direction = direction
        self.spacing = spacing
        self.align = align
        self.reverse = reverse

    @micropython.native
    def _get_min_size(self) -> tuple[int, int]:
        """
        重写方法
        计算容器所需的最小尺寸
        返回: (min_width, min_height)
        """
        min_width = 0
        min_height = 0

        if self.direction == self.HORIZONTAL:
            # 水平布局
            for child in self.children:
                # 递归获取其最小尺寸
                child_min_width, child_min_height = child._get_min_size()
                # 宽度累加，高度取最大值
                min_width += child_min_width
                min_height = max(min_height, child_min_height)
            # 添加间距
            min_width += self.spacing * (len(self.children) - 1)

        else: # direction == self.VERTICAL
            # 垂直布局
            for child in self.children:
                # 递归获取其最小尺寸
                child_min_width, child_min_height = child._get_min_size()
                # 高度累加，宽度取最大值
                min_width = max(min_width, child_min_width)
                min_height += child_min_height
            # 添加间距
            min_height += self.spacing * (len(self.children) - 1)

        # 如果容器本身固定尺寸则使用较大的值，否则灵活尺寸不做修正
        if not self.width_resizable:
            min_width = max(min_width, self.width or 0)
        if not self.height_resizable:
            min_height = max(min_height, self.height or 0)

        return min_width+self.rel_x, min_height+self.rel_y

    @micropython.viper
    @staticmethod
    def _calculate_flexible_size(total_size: int, fixed_size_sum: int, flexible_count: int, spacing: int, children_num: int) -> int:
        """
        计算可伸缩元素的尺寸
        :param total_size: 总可用空间
        :param fixed_size_sum: 固定尺寸之和
        :param flexible_count: 可伸缩元素数量
        :return: 每个可伸缩元素应得的尺寸
        """
        # 计算剩余空间
        remaining = total_size - fixed_size_sum - spacing * (children_num - 1)
        if remaining < 0:
            raise ValueError(f'计算可伸缩元素尺寸时，剩余空间不够。\n    总可用{total_size},固定尺寸实际占用{fixed_size_sum}')
        # 平均分配给每个可伸缩元素
        if flexible_count == 0:
            return 0
        # resault = int(max(0, remaining // flexible_count))
        return int(max(0, remaining // flexible_count))

    def update_layout(self) -> None:
        """更新容器的布局,处理子元素的位置和大小
            到这一步,self的尺寸已经被上层设置完成
        """
        if not self.children:
            return
        # 获取容器的最小所需尺寸,,确保容器有足够的空间
        min_width, min_height = self._get_min_size()
        if (min_width > self.width+self.rel_x) or (min_height > self.height+self.rel_y):
            raise ValueError(f'子元素尺寸大于flex容器尺寸,请调整子元素的初始化参数.\n    容器宽高{self.width} {self.height},组件所需尺寸{min_width} {min_height}')    

        if self.direction == self.HORIZONTAL:
            self._layout_horizontal()
        else:
            self._layout_vertical()

    @micropython.native
    def _layout_horizontal(self) -> None:
        """
        水平方向的布局处理
        处理None值的情况,计算并分配空间
        """
        dx = self.dx if not self.reverse else (self.dx + self.width + self.spacing)
        fixed_width_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定宽度和可伸缩元素数量
        for child in self.children:
            child_min_width, _ = child._get_min_size()
            if child.width_resizable:
                flexible_count += 1
            else:
                fixed_width_sum += child_min_width

        # 计算可伸缩元素的宽度
        flexible_width = self._calculate_flexible_size(
            self.width, fixed_width_sum, flexible_count, self.spacing, len(self.children))

        # 第二遍遍历：设置实际布局
        for child in self.children:
            child_min_width, child_min_height = child._get_min_size()
            # 确定实际使用的宽度,灵活尺寸则取灵活尺寸，否则取child_min_width固定尺寸
            actual_width = flexible_width if child.width_resizable else child_min_width
            # 确定实际使用的高度
            actual_height = self.height if child.height_resizable else child_min_height

            # 根据对齐方式计算y坐标
            if self.align == self.ALIGN_START:
                dy = self.dy
            elif self.align == self.ALIGN_CENTER:
                dy = self.dy + (self.height - actual_height) // 2
            else:  # end
                dy = self.dy + self.height - actual_height

            if self.reverse:
                dx -= (actual_width + self.spacing)
            # 应用布局
            child.layout(dx = dx, dy = dy,
                         width = actual_width, height = actual_height)
            if not self.reverse:
                dx += actual_width + self.spacing

    @micropython.native
    def _layout_vertical(self) -> None:
        """
        垂直方向的布局处理
        处理None值的情况,计算并分配空间
        """
        dy = self.dy if not self.reverse else (self.dy + self.height + self.spacing)
        fixed_height_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定高度和可伸缩元素数量
        for child in self.children:
            _, child_min_width = child._get_min_size()
            if child.height_resizable:
                flexible_count += 1
            else:
                fixed_height_sum += child_min_width

        # 计算可伸缩元素的高度
        flexible_height = self._calculate_flexible_size(
            self.height, fixed_height_sum, flexible_count, self.spacing, len(self.children))

        # 第二遍遍历：设置实际布局
        for child in self.children:
            child_min_width, child_min_height = child._get_min_size()
            # 确定实际使用的宽度
            actual_width = self.width if child.width_resizable else  child_min_width
            # 确定实际使用的高度
            actual_height = flexible_height if child.height_resizable else child_min_height

            # 根据对齐方式计算x坐标
            if self.align ==self.ALIGN_START:
                dx = self.dx
            elif self.align == self.ALIGN_CENTER:
                dx = self.dx + (self.width - actual_width) // 2
            else:  # align_end
                dx = self.dx + self.width - actual_width

            if self.reverse:
                dy -= (actual_height + self.spacing)
            # 应用布局
            child.layout(dx=dx, dy=dy, width=actual_width, height=actual_height)
            if not self.reverse:
                dy += actual_height + self.spacing
