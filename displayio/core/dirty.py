class DirtySystem:
    """
    脏区域管理基类类,
    采用单例模式,确保实例唯一
    """
    _instances = {}  # 存储所有命名实例
    __slots__ = ('name', 'dirty', 'widget', '_layout_dirty', 'initialized')
    
    def __new__(cls, name='default', **kwargs):
        # 确保每个名称只创建一个实例
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(self, name='default', widget=None):
        if hasattr(self, 'initialized'):  # 检查是否已初始化,避免覆盖参数
            return
        if name != 'default' and widget is None:
            raise ValueError('dirty_system初始化错误,\n\t非默认dirty_system缺少关键字参数: widget')
        if name == 'default' and widget is not None:
            raise ValueError('dirty_system初始化错误,\n\t默认dirty_system禁止关键字参数: widget')
        # 管理器的名称,默认为default
        self.name = name
        # 绘制系统的脏标记,用来出发遍历组件树刷新
        self.dirty = False
        # 引用Widget(那些维护自己独立的bitmap(同时也会使用独立的脏系统)的widget,例如scroll_box)
        self.widget=widget if name != 'default' else None
        # 布局系统脏标记，用来触发重新计算布局。布局系统的尺寸位置重分配总是从根节点开始。
        self._layout_dirty = True
        # 标记默认的管理器已初始化,防止重复实例
        self.initialized = True

    @property
    def layout_dirty(self):
        return self._layout_dirty

    @layout_dirty.setter
    def layout_dirty(self, value):
        """设置 layout_dirty 属性，并同步到默认实例"""
        self._layout_dirty = value
        # 如果当前实例不是默认实例且被赋值为True，则更新默认实例
        if value and self.widget:
            parent_system = self.widget.dirty_system
            parent_system.layout_dirty = True

    def clear(self):
        """重置脏区域"""
        if self.name == "default":
            for name, system in self._instances.items():
                if name != 'default':
                    system.clear()
        
        self.dirty = False

class MergeRegionSystem(DirtySystem):
    """
    脏区域管理类,采用区域合并算法
    精细化管理,当脏区域数量变多,性能下降明显
    """
    __slots__ = ('_area',)
    
    def __init__(self, name='default', widget=None):
        # 绘制系统的脏区域,用来触发组件刷新
        super().__init__(name, widget)
        # 绘制系统的脏区域,用来触发组件刷新
        self._area = []

    @property
    def area(self):
        """返回脏区域"""
        return self._area

    def add(self, x2_min, y2_min, width2, height2):
        """添加脏区域"""
        # 提前检查无效区域，减少后续计算开销        
        width2 = width2 or 0
        height2 = height2 or 0
        if width2 <= 0 or height2 <= 0:  # 检查无效区域
            return  # 忽略无效输入
        
        x2_max = x2_min + width2 - 1  # widget的右边界
        y2_max = y2_min + height2 - 1 # widget的上边界

        for i, area1 in enumerate(self._area): # 如果发现交集，则合并
            if self._intersects(area1, x2_min, y2_min, x2_max, y2_max):
                self._area[i] = self._union(area1, x2_min, y2_min, x2_max, y2_max)
                break
        else: # 如果没有交集，则直接追加
            self._area.append([x2_min, y2_min, x2_max, y2_max])

        # 如果这个dirty_system不是默认实例,则需要将self.widget.dirty_system为脏
        # 这是因为需要传递脏信息,否则会导致dirty_system的脏区域只作用于局部,不会影响到默认dirty_system
        self.dirty = True
        if self.widget:
            parent_system = self.widget.dirty_system
            parent_system.add(self.widget.dx, self.widget.dy, self.widget.width, self.widget.height)

    def _intersects(self, area1, x2_min, y2_min, x2_max, y2_max) -> bool:
        """检查两个区域是否有重叠"""
        x1_min, y1_min, x1_max, y1_max = area1
        # 检查是否有交集
        # 扩展1个像素的判断范围,允许相邻合并
        return not (x1_min > x2_max + 1 or x2_min > x1_max + 1 or 
                    y1_min > y2_max + 1 or y2_min > y1_max + 1)

    def _union(self, area1, x2_min, y2_min, x2_max, y2_max) -> list:
        """合并脏区域"""
        x1_min, y1_min, x1_max, y1_max = area1
        return [min(x1_min, x2_min), min(y1_min, y2_min),
                max(x1_max, x2_max), max(y1_max, y2_max)]

    def intersects(self, x, y, width, height):
        """判断widget是否与脏区域重叠"""
        width = width or 0
        height = height or 0
        x_max, y_max = x + width - 1, y + height - 1
        for area in self._area:
            if self._intersects(area, x, y, x_max, y_max):
                return True
        return False
    
    def clear(self):
        """重置脏区域"""
        if self.name == "default":
            for name, system in self._instances.items():
                if name != 'default':
                    system.clear()

        if not self.dirty:  # 如果没有脏区域，直接退出
            return
        
        self._area.clear()
        self.dirty = False

class BoundBoxSystem(DirtySystem):
    """
    边界框脏区域管理,采用包围盒算法
    适合处理单一矩形区域的大规模刷新。
    """
    __slots__ = ('min_x', 'min_y', 'max_x', 'max_y')
    
    def __init__(self, name='default', widget=None):
        super().__init__(name, widget)
        self.min_x, self.min_y = 0, 0
        self.max_x, self.max_y = 0, 0

    @property
    def area(self):
        return [self.min_x, self.min_y, self.max_x, self.max_y]

    def add(self, x2, y2, width2, height2):
        """添加边界框"""
        # 提前检查无效区域，减少后续计算开销        
        width2 = width2 or 0
        height2 = height2 or 0
        if width2 <= 0 or height2 <= 0:
            return

        self.min_x = min(self.min_x, x2)
        self.min_y = min(self.min_y, y2)
        self.max_x = max(self.max_x, x2 + width2 - 1)
        self.max_y = max(self.max_y, y2 + height2 - 1)

        self.dirty = True

        # 传递 dirty state to parent system
        if self.widget:
            parent_system = self.widget.dirty_system
            parent_system.add(self.widget.dx, self.widget.dy, self.widget.width, self.widget.height)
    
    def intersects(self, x, y, width, height):
        """判断是否与边界框重叠"""
        width = width or 0
        height = height or 0
        x_max, y_max = x + width - 1, y + height - 1
        return not (x > self.max_x or x_max < self.min_x or y > self.max_y or y_max < self.min_y)

    def clear(self):
        """重置边界框"""
        if self.name == "default":
            for name, system in self._instances.items():
                if name != 'default':
                    system.clear()

        if not self.dirty:  # 如果没有脏区域，直接退出
            return
        
        self.min_x, self.min_y = 0, 0
        self.max_x, self.max_y = 0, 0
        self.dirty = False

class GridSystem(DirtySystem):
    """
    网格型脏区域管理,采用网格划分算法
    适合大规模屏幕划分，逐块刷新。
    """
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
        self._dirty_rows.clear()
        self._dirty_cols.clear()
        self.dirty = False
