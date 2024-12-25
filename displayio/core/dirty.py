class DirtySystem:
    """
    脏区域管理类
    采用单例模式,确保实例唯一
    """
    _default_instance = None  # 默认单例
    _instances = {}           # 多实例
    
    def __new__(cls, name=None):
        if name:  # 使用命名实例
            if name not in cls._instances:
                cls._instances[name] = super().__new__(cls)
            return cls._instances[name]
        # 默认单例
        if cls._default_instance is None:
            cls._default_instance = super().__new__(cls)
        return cls._default_instance
    
    def __init__(self, name=None):
        if not hasattr(self, 'initialized'):  # 检查是否已初始化
            # 绘制系统的脏标记区域,用来触发触发遍历组件树刷新。
            self.area = []
            # 布局系统脏标记，用来触发重新计算布局。布局系统的尺寸位置重分配总是从根节点开始。
            self.layout_dirty = True
            self.initialized = True  # 标记已初始化

    def add(self, x2_min, y2_min, width2, height2):
        width2 = width2 or 0
        height2 = height2 or 0
        if width2 <= 0 or height2 <= 0:  # 检查无效区域
            return  # 忽略无效输入
        x2_max = x2_min + width2 - 1  # widget的右边界
        y2_max = y2_min + height2 - 1 # widget的上边界
        merged = False # 标志位 merged，确保区域合并或追加一次
        for index, dirty_area in enumerate(self.area):
            if self._intersects(dirty_area, x2_min, y2_min, x2_max, y2_max):
                self.area[index] = self._union(dirty_area, x2_min, y2_min, x2_max, y2_max)
                merged = True
                break
        if not merged:
            self.area.append([x2_min, y2_min, x2_max, y2_max])

    def _intersects(self, area1, x2_min, y2_min, x2_max, y2_max) -> bool:
        """检查两个区域是否有重叠"""
        x1_min, y1_min, x1_max, y1_max = area1
        # 检查是否有交集
        if x1_min > x2_max or x2_min > x1_max:
            return False  # 在水平轴上没有交集
        if y1_min > y2_max or y2_min > y1_max:
            return False  # 在垂直轴上没有交集
        return True  # 存在交集

    def _union(self, area1, x2_min, y2_min, x2_max, y2_max) -> list:
        """合并脏区域"""
        x1_min, y1_min, x1_max, y1_max = area1
        return [min(x1_min, x2_min),
                min(y1_min, y2_min),
                max(x1_max, x2_max),
                max(y1_max, y2_max)]
    
    def clear(self):
        """重置脏区域"""
        self.area.clear()