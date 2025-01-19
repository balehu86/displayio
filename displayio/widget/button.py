# ./widget/button.py
from .label import Label
from ..core.event import EventType

import micropython # type: ignore

class Button(Label):
    """
    按钮控件类
    继承自Label,添加了状态和交互功能
    """
    __slots__ = ()

    def __init__(self,
                 
                 text="",
                 font=None,
                 font_scale=1,
                 text_color=Label.WHITE, # 文字颜色默认白色
                 align=Label.ALIGN_CENTER,  # 按钮文字默认居中
                 padding=(5, 3, 5, 3),  # 按钮默认较大内边距
                 
                 abs_x=None, abs_y=None,
                 rel_x=0,rel_y=0, dz=0,
                 width=None,height=None,
                 visibility=True, state=Label.STATE_DEFAULT,
                 transparent_color=Label.PINK,
                 background=Label.Button_BLUE, # 背景颜色默认蓝色
                 color_format = Label.RGB565): 
        """
        初始化按钮控件
        
        继承Label的所有参数,额外添加:
            pass
        """
        super().__init__(text = text,
                         font = font,
                         font_scale = font_scale,
                         text_color = text_color,
                         align = align,
                         padding = padding,

                         abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         transparent_color = transparent_color,
                         background = background,
                         color_format = color_format)
        
        self.event_listener = {EventType.CLICK:[self.release],
                               EventType.PRESS:[self.press],
                               EventType.RELEASE:[self.release],
                            #    EventType.LONG_PRESS:[self.press],
                               EventType.LONG_PRESS_RELEASE:[self.long_press_release],
                               EventType.DOUBLE_CLICK:[self.release],
                               }
        
    @micropython.native
    def draw(self) -> None:
        """
        创建按钮位图
        添加边框和状态效果
        """
        # 创建和填充新的位图
        self._bitmap.init(dx=self.dx,dy=self.dy,color=self.get_background_color)
        # 绘制文本部分,创建文本位图
        if self._text_dirty:
            self._draw_text_bitmap()
        # 计算文本位置（从Label类复用此逻辑）
        text_x, text_y = self._calculate_text_position()
        
        # 将文本bitmap绘制到背景
        self._bitmap.blit(self._text_bitmap, dx=text_x, dy=text_y)

    def set_state(self, state) -> None:
        if self.state != state:
            self.state = state
            self.dirty_system.add_widget(self)
            self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    def press(self,widget,event) -> None:
        """按钮按下,状态为STATE_PRESSED"""
        self.set_state(self.STATE_PRESSED)

    def release(self,widget,event) -> None:
        self.set_state(self.STATE_DEFAULT)
    
    def long_press_release(self,widget,event) -> None:
        self.set_state(self.STATE_DEFAULT)

    @property    
    def get_background_color(self):
        if self.state == self.STATE_FOCUSED:
            return self._darken_color(self.background.color, 0.9)
        if self.state == self.STATE_PRESSED:
            return self._darken_color(self.background.color, 0.7)
        if self.state == self.STATE_DISABLED:
            return Label.GREY
        return self.background.color
