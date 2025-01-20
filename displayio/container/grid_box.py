# ./container/free_box.py
from ..core.base_widget import BaseWidget
from .container import Container

import micropython # type: ignore

class GridBox(Container):
    """
    GridBox表格容器类
    继承自Container
    """
    __slots__ = ('rows', 'cols', 'row_spacing', 'col_spacing',
                 'cells','allow_overlap', 'merged_cells', 'child_posi')

    def __init__(self,
                 rows, cols, row_spacing=0, col_spacing=0,
                 allow_overlap:bool=True,

                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=Container.STATE_DEFAULT,
                 transparent_color=Container.PINK,
                 background=Container.DARK,
                 color_format=Container.RGB565):
        """
        初始化GridBox容器

        继承Container的所有参数,额外添加:
            row: 行数
            column: 列数
            row_gap: 行间距
            column: 列间距
            allow_overlap: 是否允许重叠
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         transparent_color = transparent_color,
                         background = background,
                         color_format = color_format)

        # 格子布局的行列数
        self.rows = rows
        self.cols = cols
        self.row_spacing = row_spacing
        self.col_spacing = col_spacing
        # 是否允许重叠
        self.allow_overlap = allow_overlap
        # 初始化表格
        self.cells = self.cells = [[None for _ in range(cols)] for _ in range(rows)]
        # 存储合并信息 {start_pos: (row_span, col_span)}
        self.merged_cells = {}
        # 储存widget的位置信息 {widget: (row, col)}
        self.child_posi = {}

    def add(self, widget: BaseWidget|Container, row, col, row_span=1, col_span=1):
        """添加子部件,可选span参数"""
        # 如果需要合并单元格，先合并
        if row_span > 1 or col_span > 1:
            self.merge_cells(row, col, row_span, col_span)

        # 将widget添加到指定位置
        if self.allow_overlap: # 如果允许重叠,则直接覆盖区域
            for r in range(row, row + row_span):
                for c in range(col, col + col_span):
                    self.cells[r][c] = widget
        else: # 如果不允许重叠,则先检查区域是否为空,如果为空则添加,如果不为空,则raise error
            empty_area = True # 检查区域是否为空
            for r in range(row, row + row_span):
                for c in range(col, col + col_span):
                    if self.cells[r][c] is not None:
                        empty_area = False
                        break
                else:
                    continue
                break
            if empty_area: # 如果区域为空,则在区域添加
                for r in range(row, row + row_span):
                    for c in range(col, col + col_span):
                        self.cells[r][c] = widget
            else:
                raise ValueError('此网格容器不允许重叠,目标区域已存在其它widget')

        # 将widget添加到指定位置
        # 覆盖顺序可以用widget.dz属性确定
        self.child_posi[widget] = (row, col)
        super().add(widget)

    def remove(self, widget: BaseWidget|Container) -> None:
        """移除子部件"""
        # 不再子元素列表则直接返回
        if widget not in self.children:
            return
        row, col = self.child_posi[widget]
        row_span, col_span = self.merged_cells.pop((row, col), (1, 1))
        # 遍历widget所在区域,置位
        for r in range(row, row + row_span):
                for c in range(col, col + col_span):
                    if self.cells[r][c] == widget:
                        self.cells[r][c] = None

        self.child_posi.pop(widget, None)
        super().remove(widget)

    def clear(self) -> None:
        """清空容器中所有元素"""
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c] = None

        self.child_posi.clear()
        super().clear()

    def merge_cells(self, row, col, row_span=1, col_span=1):
        """合并网格单元"""
        if row < 0 or col < 0 or row + row_span > self.rows or col + col_span > self.cols:
            raise ValueError("指定的网格位置或范围越界")

        # 检查合并区域是否冲突
        if self.allow_overlap:
            for r in range(row, row + row_span):
                for c in range(col, col + col_span):
                    if self.cells[r][c] is not None:
                        raise ValueError(f"单元格({r}, {c})已被占用")

        # 标记合并信息
        self.merged_cells[(row, col)] = (row_span, col_span)

    @micropython.native
    def update_layout(self):
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        if not self.children:
            return

        cell_width = (self.width - (self.cols - 1) * self.col_spacing) // self.cols
        cell_height = (self.height - (self.rows - 1) * self.row_spacing) // self.rows
        for child in self.children:
            child_min_width, child_min_height = child._get_min_size()

            row, col = self.child_posi[child]
            row_span, col_span = self.merged_cells.get((row, col), (1, 1))

            actual_width = cell_width * col_span + self.col_spacing * (col_span - 1) if child.width_resizable else  child_min_width
            actual_height = cell_height * row_span + self.row_spacing * (row_span - 1) if child.height_resizable else child_min_height

            # 更新子部件位置和大小
            dx = self.dx + col * (cell_width + self.col_spacing)
            dy = self.dy + row * (cell_height + self.row_spacing)
            child.layout(dx=dx, dy=dy, width=actual_width, height=actual_height)
