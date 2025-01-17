class GridSystem(DirtySystem):
    """
    网格型脏区域管理,采用网格划分算法
    适合大规模屏幕划分，逐块刷新。
    """
    _instances = {}  # 存储所有命名实例
    __slots__ = ('width', 'height', 'cell_size', 'cols', 'rows', 'grid',
                 '_dirty_rows', '_dirty_cols')
    
    def __init__(self, name='default', widget=None, width=128, height=64, cell_size=8):
        super().__init__(name, widget)
        # 屏幕尺寸
        self.width, self.height = width, height
        # 网格大小(建议是2的幂，便于除法运算)
        self.cell_size = cell_size
        # 计算网格行列数
        self.cols = (width + cell_size - 1) // cell_size
        self.rows = (height + cell_size - 1) // cell_size
        # 网格状态数组，True表示该网格包含脏区域
        self.grid = [[False] * self.cols for _ in range(self.rows)]
        
        # 用于优化clear操作的脏行列表
        self._dirty_rows = set()
        self._dirty_cols = set()

    @property
    def area(self):
        return [self._dirty_rows,self._dirty_cols]
    
    def add(self, x2, y2, width2, height2):
        """添加脏区域到网格"""
        # 提前检查无效区域，减少后续计算开销        
        width2 = width2 or 0
        height2 = height2 or 0
        if width2 <= 0 or height2 <= 0:
            return
        logger.debug(f'{self.__class__.__name__} add {x2}, {y2}, {width2}, {height2}')
        # 只标记网格
        start_row, start_col = y2 // self.cell_size, x2 // self.cell_size
        end_row, end_col = (y2 + height2 - 1) // self.cell_size, (x2 + width2 - 1) // self.cell_size
        
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                if not self.grid[row][col]:
                    self.grid[row][col] = True
                    # 记录脏行和列
                    self._dirty_rows.add(row)
                    self._dirty_cols.add(col)
        logger.debug(f'{self.__class__.__name__} after add {self.area}')
        self.dirty = True
        
        # 传递 dirty state to parent system
        if self.widget:
            parent_system = self.widget.dirty_system
            parent_system.add(self.widget.dx, self.widget.dy, self.widget.width, self.widget.height)

    def intersects(self, x, y, width, height):
        """判断是否与网格中的脏区域重叠"""
        width = width or 0
        height = height or 0
        start_row, start_col = y // self.cell_size, x // self.cell_size
        end_row, end_col = (y + height - 1) // self.cell_size, (x + width - 1) // self.cell_size
        for r in range(start_row, end_row + 1):
            for c in range(start_col, end_col + 1):
                if self.grid[r][c]:
                    return True
        return False

    def clear(self):
        """清空脏区域"""
        if self.name == "default":
            for name, system in self._instances.items():
                if name != 'default':
                    system.clear()

        if not self.dirty:  # 如果没有脏区域，直接退出
            return

        if len(self._dirty_rows) * len(self._dirty_cols) < (self.rows * self.cols) * 0.1:
            # 针对少量脏区域，仅清除脏单元格
            for row in self._dirty_rows:
                for col in self._dirty_cols:
                    self.grid[row][col] = False
        else:
            # 如果脏区域较多或覆盖大部分网格，直接重置整个网格
            self.grid = [[False] * self.cols for _ in range(self.rows)]
        
        # 重置状态
        self.dirty_widget.clear()
        self._dirty_rows.clear()
        self._dirty_cols.clear()
        self.dirty = False
