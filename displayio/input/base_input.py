# ./input/base_input.py
from ..core.event import EventType

class Input(EventType):
    """
    输入设备基类
    """
    __slots__ = ('target_widget', 'target_position', 'state', 'event_map')
    
    def __init__(self,target_widget=None, target_position=None, event_map={}):
        # 目标管理
        self.target_widget = target_widget
        self.target_position = target_position
        # 状态管理
        self.state = self.IDLE
        # 硬件设备事件到系统事件映射,默认直接输出硬件设备状态
        self.event_map = event_map

    def check_input(self):
        """返回值event说明:
            data字段(字典):
                key: {input_type}_{input类的参数名}
                value: value
            例如：
                data={'rotate_position': self.position}
        """
        raise NotImplementedError("Input子类必须实现check_input方法")
    
    def set_target_position(self, dx=-1, dy=-1):
        """设置目标位置"""
        self.target_position = [dx, dy]

    def set_target_widget(self,widget):
        """设置目标widget"""
        self.target_widget = widget

    def set_event_mapping(self, source_type, target_type):
        """动态设置事件类型"""
        self.event_map.setdefault(source_type, target_type)

