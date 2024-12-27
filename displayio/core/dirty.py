class DirtySystem:
    """
    脏区域管理类
    采用单例模式,确保实例唯一
    """
    _instances = {}  # 存储所有命名实例
    
    def __new__(cls, name='default',**kwargs):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(self, name='default',widget=None):
        if not hasattr(self, 'initialized'):  # 检查是否已初始化
            # 绘制系统的脏标记区域,用来触发触发遍历组件树刷新。
            self.name = name
            self.area = []
            self.dirty = False
            self.widget=widget
            # 布局系统脏标记，用来触发重新计算布局。布局系统的尺寸位置重分配总是从根节点开始。
            self._layout_dirty = True
            self.initialized = True  # 标记已初始化

    def add(self, x2_min, y2_min, width2, height2):
        """添加脏区域"""
        # 提前检查无效区域，减少后续计算开销        
        width2 = width2 or 0
        height2 = height2 or 0
        if width2 <= 0 or height2 <= 0:  # 检查无效区域
            return  # 忽略无效输入
        x2_max = x2_min + width2 - 1  # widget的右边界
        y2_max = y2_min + height2 - 1 # widget的上边界
        merged = False # 标志位 merged，确保区域合并或追加一次
        for index, dirty_area in enumerate(self.area):
            # 如果发现交集，则合并
            if self._intersects(dirty_area, x2_min, y2_min, x2_max, y2_max):
                self.area[index] = self._union(dirty_area, x2_min, y2_min, x2_max, y2_max)
                merged = True
                break
        # 如果没有交集，则直接追加
        if not merged:
            self.area.append([x2_min, y2_min, x2_max, y2_max])

        # 如果这个dirty_system不是默认实例,则需要将self.widget.dirty_system为脏
        # 这是因为需要传递脏信息,否则会导致dirty_system的脏区域只作用于局部,不会影响到默认dirty_system
        self.dirty = True
        if self.widget:
            print(self.widget.child.children)
            self.widget.dirty_system.dirty = True
            self.widget.dirty_system.add(self.widget.dx, self.widget.dy, self.widget.width, self.widget.height)

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
        return [min(x1_min, x2_min),
                min(y1_min, y2_min),
                max(x1_max, x2_max),
                max(y1_max, y2_max)]
    
    def clear(self):
        """重置脏区域"""
        self.area.clear()
        self.dirty = False

    @property
    def layout_dirty(self):
        """获取 layout_dirty 属性"""
        return self._layout_dirty

    @layout_dirty.setter
    def layout_dirty(self, value):
        """设置 layout_dirty 属性，并同步到默认实例"""
        self._layout_dirty = value
        # 如果当前实例不是默认实例且被赋值为True，则更新默认实例
        if value and self.name != 'default':
            default_instance = DirtySystem._instances.get('default')
            if default_instance:
                default_instance._layout_dirty = True

class QuadTreeNode:
    """四叉树节点"""
    MAX_OBJECTS = 4  # 每个节点最大存储对象数量
    MAX_LEVELS = 5   # 最大深度

    def __init__(self, level, bounds):
        self.level = level  # 当前深度
        self.bounds = bounds  # 节点边界 [x_min, y_min, x_max, y_max]
        self.objects = []  # 存储对象
        self.nodes = []  # 子节点

    def clear(self):
        """清除节点和子节点"""
        self.objects.clear()
        for node in self.nodes:
            node.clear()
        self.nodes = []

    def split(self):
        """分裂成四个象限"""
        x_min, y_min, x_max, y_max = self.bounds
        mid_x = (x_min + x_max) // 2
        mid_y = (y_min + y_max) // 2

        self.nodes = [
            QuadTreeNode(self.level + 1, [x_min, y_min, mid_x, mid_y]),  # 左上
            QuadTreeNode(self.level + 1, [mid_x + 1, y_min, x_max, mid_y]),  # 右上
            QuadTreeNode(self.level + 1, [x_min, mid_y + 1, mid_x, y_max]),  # 左下
            QuadTreeNode(self.level + 1, [mid_x + 1, mid_y + 1, x_max, y_max])  # 右下
        ]

    def get_index(self, area):
        """判断区域属于哪个象限"""
        x_min, y_min, x_max, y_max = area
        mid_x = (self.bounds[0] + self.bounds[2]) // 2
        mid_y = (self.bounds[1] + self.bounds[3]) // 2

        top = y_max <= mid_y
        bottom = y_min > mid_y
        left = x_max <= mid_x
        right = x_min > mid_x

        if top and left:
            return 0
        elif top and right:
            return 1
        elif bottom and left:
            return 2
        elif bottom and right:
            return 3
        return -1  # 不属于子节点

    def insert(self, area):
        """插入区域"""
        # 若已分裂，则递归插入子节点
        if self.nodes:
            index = self.get_index(area)
            if index != -1:
                self.nodes[index].insert(area)
                return

        # 添加当前区域
        self.objects.append(area)

        # 判断是否需要分裂
        if len(self.objects) > self.MAX_OBJECTS and self.level < self.MAX_LEVELS:
            if not self.nodes:
                self.split()
            for obj in self.objects[:]:
                index = self.get_index(obj)
                if index != -1:
                    self.nodes[index].insert(obj)
                    self.objects.remove(obj)

    def retrieve(self, area):
        """检索可能有交集的区域"""
        result = []
        index = self.get_index(area)
        if index != -1 and self.nodes:
            result += self.nodes[index].retrieve(area)
        result += self.objects
        return result