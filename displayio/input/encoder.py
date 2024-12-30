from machine import Pin # type: ignore
import time
from .base_input import Input
from ..core.event import Event

class RotaryEncoder(Input):
    __slots__ = ('pin_a', 'pin_b', 'strict', 'steps_per_click',
                 'code', 'position', 'tick_position', 'direction')

    def __init__(self, pin_a, pin_b, strict=False, steps_per_click=4, 
                 target_widget=None, target_position=None, event_map={}):
        """
        初始化旋转编码器
        Args:
            pin_a: A相引脚号
            pin_b: B相引脚号
            strict: 是否采用完整格雷码,完整的格雷编码可能会因为各种原因产生错步,有效转移能尽可能避免此错误
            steps_per_click: 一格clik有几步旋转
        """
        # 配置A相和B相引脚为上拉输入
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)

        self.strict = strict
        self.steps_per_click = steps_per_click
        
        # 调用父类初始化
        super().__init__(target_widget=target_widget, target_position=target_position, event_map=event_map)
        
        #顺时针旋转：状态可能按 00 -> 01 -> 11 -> 10 -> 00 的顺序变化。
        #逆时针旋转：状态可能按 00 -> 10 -> 11 -> 01 -> 00 的顺序变化。
        # 状态转移表 (Gray 编码)
        if strict:
            self.transition_table = {
                0b00: {0b00:  0, 0b01:  1, 0b10: -1, 0b11:  0}, # 完整的格雷编码
                0b01: {0b00: -1, 0b01:  0, 0b10:  0, 0b11:  1},
                0b10: {0b00:  1, 0b01:  0, 0b10:  0, 0b11: -1},
                0b11: {0b00:  0, 0b01: -1, 0b10:  1, 0b11:  0}}
        else:
            self.transition_table = {
                0b00: {0b01: 1, 0b10: -1}, # 只考虑有效转移
                0b01: {0b11: 1, 0b00: -1},
                0b11: {0b10: 1, 0b01: -1},
                0b10: {0b00: 1, 0b11: -1}}
        # 状态机的初始状态
        self.code = (self.pin_a.value() << 1) | self.pin_b.value()
        self.position = 0  # 位置计数器
        self.tick_position = 0 # tick的计数器
        self.direction = 0  # -1: 逆时针, 1: 顺时针, 0: 无变化
        
    def check_input(self):
        """
        检测旋转编码器状态
        
        :return: Event或None
        """
        current_time = time.ticks_ms()
        # 获取当前状态
        new_code = (self.pin_a.value() << 1) | self.pin_b.value()
        if self.code == new_code: # 位置未发生改变，直接返回None
            return None
        # 如果状态变化不在有效转移表中，忽略
        if new_code not in self.transition_table[self.code]:
            return None
        # 更新方向
        self.direction = self.transition_table[self.code][new_code]
        self.position += self.direction
        self.code = new_code  # 更新状态
        
        # 检测是否完成一个click
        if self.position % self.steps_per_click == 0:
            self.tick_position = self.position // self.steps_per_click
            return Event(self.event_map.get(self.ROTATE_TICK, self.ROTATE_TICK),
                         data={'rotate_direction': self.direction,
                               'rotate_tick_position': self.tick_position,
                               'rotate_position': self.position},
                         target_widget=self.target_widget, target_position=self.target_position, timestamp=current_time)

        # 如果有方向变化，则触发旋转事件
        if self.direction == -1:
            return Event(self.event_map.get(self.ROTATE_LEFT, self.ROTATE_LEFT),
                         data={'rotate_direction': self.direction,
                               'rotate_tick_position': self.tick_position,
                               'rotate_position': self.position},
                         target_widget=self.target_widget, target_position=self.target_position, timestamp=current_time)
        if self.direction == 1:
            return Event(self.event_map.get(self.ROTATE_RIGHT, self.ROTATE_RIGHT),
                         data={'rotate_direction': self.direction,
                               'rotate_tick_position': self.tick_position,
                               'rotate_position': self.position},
                         target_widget=self.target_widget, target_position=self.target_position, timestamp=current_time)
        else: # 这个分支大概率不会执行,因为之前如果状态未改变或无效转移,函数会提前返回None
            return None
