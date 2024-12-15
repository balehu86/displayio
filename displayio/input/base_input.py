# ./input/base_input.py
from ..core.event import EventType

class Input(EventType):
    """
    输入设备基类
    """
    def __init__(self, device, target_widget=None, target_position=None):
        # 统一驱动读取输入为self.input.read()
        self.input = device
        # 目标管理
        self.target_widget = target_widget
        self.target_position = target_position
        # 状态管理
        self.state = self.IDLE
        
    def check_input(self):
        """返回值event说明:
            data字段(字典):
                key: {input_type}_{input类的参数名}
                value: value
            例如：
                data={'rotate_position': self.position}
        """
        pass
    
    def set_target_position(self, dx=-1, dy=-1):
        self.target_position = [dx, dy]

    def set_target_widget(self,widget):
        self.target_widget = widget

