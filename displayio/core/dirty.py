from .logging import logger

class DirtySystem:
    """
    脏区域管理基类类,采用单例模式,确保实例唯一
    只有widget需要额外创建一张屏幕外的bitmap时,才需要创建一个独立的dirty_system
        命名为 {容器类名}_{容器实例id}  ,且需要传入widget参数
    """
    _instances = {}  # 存储所有命名实例
    __slots__ = ('name', 'dirty_widget', 'widget', '_layout_dirty', 'initialized')
    
    def __new__(cls, name='default', *args,**kwargs):
        # 确保每个名称只创建一个实例
        if name not in cls._instances:
            cls._instances[name] = object.__new__(cls)
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
        # 引用Widget(那些维护自己独立的bitmap(同时也会使用独立的脏系统)的widget,例如scroll_box)
        self.widget=widget if name != 'default' else None
        # 布局系统脏标记，用来触发重新计算布局。布局系统的尺寸位置重分配总是从根节点开始。
        self._layout_dirty = True
        # 需要重新绘制的widget
        self.dirty_widget = set()
        # 标记默认的管理器已初始化,防止重复实例
        self.initialized = True
    
    @property
    def dirty(self):
        """绘制系统的脏标记,用来出发遍历组件树刷新
        脏区域基类的dirty属性:
        - 默认实例(name='default'): 检查自身和所有其他实例的脏状态
        - 其他实例: 只检查自己的脏状态
        """
        if self.name == 'default':
            # 默认实例需要检查所有其他实例
            for dirty_system in self._instances.values():
                if dirty_system is self:
                    continue
                if dirty_system.dirty:  # 这里的递归是安全的,因为其他实例只检查自己
                    return True
            # 如果其他实例都不脏,才检查自己
            return self._check_self_dirty()
        else:
            # 非默认实例只检查自己
            return self._check_self_dirty()

    def _check_self_dirty(self):
        """检查自身的脏状态"""
        raise NotImplementedError('脏区域基类未实现 _check_self_dirty 方法')
    
    def add_widget(self, widget):
        self.dirty_widget.add(widget)

    def clear_widget(self):
        self.dirty_widget.clear()

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
        raise NotImplementedError('脏区域基类未实现 clear 方法')

    def __repr__(self):
        return f'{self.__class__.__name__} \n\tname: {self.name}, area: {self.area}\n\tdirty_widget: {self.dirty_widget}'
    
class MergeRegionSystem(DirtySystem):
    """
    脏区域管理类,采用区域合并算法
    精细化管理,当脏区域数量变多,性能下降明显
    """
    __slots__ = ('area',)
    
    def __init__(self, name='default', widget=None):
        # 绘制系统的脏区域,用来触发组件刷新
        super().__init__(name, widget)
        # 绘制系统的脏区域,用来触发组件刷新
        self.area = []

    def _check_self_dirty(self):
        return len(self.area) != 0

    def add(self, x2, y2, width2, height2):
        """添加脏区域"""
        # 提前检查无效区域，减少后续计算开销
        logger.debug(f'{self.__class__.__name__} add {x2}, {y2}, {width2}, {height2}')
        width2 = width2 or 0
        height2 = height2 or 0
        if width2 <= 0 or height2 <= 0:  # 检查无效区域
            return  # 忽略无效输入
        
        x2_max = x2 + width2 - 1  # widget的右边界
        y2_max = y2 + height2 - 1 # widget的上边界
        new_region = [x2, y2, x2_max, y2_max]  # 新区域

        # 查找所有与新区域相交的区域
        # 从后向前遍历以安全地进行列表修改
        for i in range(len(self.area) - 1, -1, -1):
            if self._intersects(self.area[i], x2, y2, x2_max, y2_max):
                area1 = self.area.pop(i)
                new_region = self._union(area1, *new_region)

        # 将合并后的区域加入结果列表
        self.area.append(new_region)

        logger.debug(f'{self.__class__.__name__} after add {self.area}')
        # 如果这个dirty_system不是默认实例,则需要将self.widget.dirty_system为脏
        # 这是因为需要传递脏信息,否则会导致dirty_system的脏区域只作用于局部,不会影响到默认dirty_system
        if self.widget:
            parent_system = self.widget.dirty_system
            parent_system.add(self.widget.dx, self.widget.dy, self.widget.width, self.widget.height)

    def _intersects(self, area1, x2_min, y2_min, x2_max, y2_max) -> bool:
        """检查两个区域是否有重叠"""
        x1_min, y1_min, x1_max, y1_max = area1
        # 检查是否有交集
        margin = 0  # 设置允许合并的最大边距
        return not (x1_min > x2_max + margin or x2_min > x1_max + margin or 
                    y1_min > y2_max + margin or y2_min > y1_max + margin)

    def _union(self, area1, x2_min, y2_min, x2_max, y2_max) -> list:
        """合并脏区域"""
        x1_min, y1_min, x1_max, y1_max = area1
        return [min(x1_min, x2_min), min(y1_min, y2_min),
                max(x1_max, x2_max), max(y1_max, y2_max)]

    def clear(self):
        """重置脏区域"""
        self.area.clear()

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
        self._area = [[0,0,0,0]]

    def _check_self_dirty(self):
        return self.max_x - self.min_x > 0 or self.max_y - self.min_y > 0
    
    @property
    def area(self):
        if self.max_x-self.min_x > 0 or self.max_y-self.min_y > 0:
            self._area[0][0], self._area[0][1], self._area[0][2], self._area[0][3] = self.min_x, self.min_y, self.max_x, self.max_y
        return self._area

    def add(self, x2, y2, width2, height2):
        """添加边界框"""
        # 提前检查无效区域，减少后续计算开销
        width2 = width2 or 0
        height2 = height2 or 0
        if width2 <= 0 or height2 <= 0:
            return
        logger.debug(f'{self.__class__.__name__} add {x2}, {y2}, {width2}, {height2}')
        self.min_x = min(self.min_x, x2)
        self.min_y = min(self.min_y, y2)
        self.max_x = max(self.max_x, x2 + width2 - 1)
        self.max_y = max(self.max_y, y2 + height2 - 1)
        logger.debug(f'{self.__class__.__name__} after add {self.area}')

        # 传递 dirty state to parent system
        if self.widget:
            parent_system = self.widget.dirty_system
            parent_system.add(self.widget.dx, self.widget.dy, self.widget.width, self.widget.height)

    def clear(self):
        """重置边界框"""
        self.min_x, self.min_y = 0, 0
        self.max_x, self.max_y = 0, 0
        self._area[0][0], self._area[0][1], self._area[0][2], self._area[0][3] = 0,0,0,0

