# ./container/free_box.py
from ..core.base_widget import BaseWidget
from .container import Container

import micropython # type: ignore

class GridBox(Container):
    """
    GridBox表格容器类
    继承自Container
    """
    def __init__(self,
                 rows, cols, row_spacing=0, col_spacing=0,

                 abs_x=None, abs_y=None,
                 rel_x=0, rel_y=0, dz=0,
                 width=None, height=None,
                 visibility=True, state=Container.STATE_DEFAULT,
                 background_color=Container.DARK,
                 transparent_color=Container.PINK,
                 color_format=Container.RGB565):
        """
        初始化GridBox容器

        继承Container的所有参数,额外添加:
            row: 行数
            column: 列数
            row_gap: 行间距
            column: 列间距
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         background_color = background_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        
        # 格子布局的行列数
        self.rows = rows
        self.cols = cols
        self.row_spacing = row_spacing
        self.col_spacing = col_spacing
        # 存储合并信息 {start_pos: (row_span, col_span)}
        self.merged_cells = {}
        # 储存widget的位置信息 {widget: (row, col)}
        self.child_posi = {}

    def merge_cells(self, row, col, row_span=1, col_span=1):
        """合并网格单元"""
        if row < 0 or col < 0 or row + row_span > self.rows or col + col_span > self.cols:
            raise ValueError("指定的网格位置或范围越界")

        # # 检查合并区域是否冲突
        # for r in range(row, row + row_span):
        #     for c in range(col, col + col_span):
        #         if self.cells[r][c] is not None:
        #             raise ValueError(f"单元格({r}, {c})已被占用")

        # 标记合并信息
        self.merged_cells[(row, col)] = (row_span, col_span)

    def add(self, widget: BaseWidget, row, col, row_span=1, col_span=1):
        """添加子部件,可选span参数"""
        # 如果需要合并单元格，先合并
        if row_span > 1 or col_span > 1:
            self.merge_cells(row, col, row_span, col_span)

        # 将widget添加到指定位置
        # 在这里不检查cell是否已有widget,cell可以重复添加widget
        # 在已经span占用的单元格中同样不做检查,默认覆盖操作
        # 覆盖顺序可以用widget.dz属性确定
        self.child_posi[widget] = (row, col)

        # 添加到子元素
        super().add(widget)
    
    @micropython.native
    def update_layout(self):
        """
        更新容器的布局
        处理子元素的位置和大小
        """
        cell_width = (self.width - (self.cols - 1) * self.col_spacing) // self.cols
        cell_height = (self.height - (self.rows - 1) * self.row_spacing) // self.rows
        for child in self.children:
            child_min_width, child_min_height = child._get_min_size()
            row, col = self.child_posi[child]
            if (row, col) in self.merged_cells:
                row_span, col_span = self.merged_cells[(row, col)]
                actual_width = cell_width * col_span + self.col_spacing * (col_span - 1) if child.width_resizable else  child_min_width
                actual_height = cell_height * row_span + self.row_spacing * (row_span - 1) if child.height_resizable else child_min_height
            else:
                actual_width = cell_width if child.width_resizable else  child_min_width
                actual_height = cell_height if child.height_resizable else child_min_height
            
            # 更新子部件位置和大小
            x = self.dx + col * (cell_width + self.col_spacing)
            y = self.dy + row * (cell_height + self.row_spacing)
            child.layout(dx=x, dy=y, width=actual_width, height=actual_height)
