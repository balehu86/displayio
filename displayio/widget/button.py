# ./widget/button.py
from .label import Label
from ..core.bitmap import Bitmap
from ..core.event import EventType
import micropython # type: ignore

@micropython.native
def _darken_color(color, factor):
    """
    将16位RGB颜色调暗
    
    参数:
        color: 原始颜色（16位RGB）
        factor: 暗化因子（0-1）
    """
    # 提取RGB分量
    r = (color >> 11) & 0x1F
    g = (color >> 5) & 0x3F
    b = color & 0x1F
    # 调整亮度
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    # 重新组装颜色
    return (r << 11) | (g << 5) | b

class Button(Label):
    """
    按钮控件类
    继承自Label，添加了状态和交互功能
    """
    
    def __init__(self,
                 text="",
                 font=None,
                 font_scale=1,
                 text_color=Label.WHITE, # 文字颜色默认白色
                 align=Label.ALIGN_CENTER,  # 按钮文字默认居中
                 padding=(5, 3, 5, 3),  # 按钮默认较大内边距
                 
                 abs_x=None, abs_y=None,
                 rel_x=None,rel_y=None,
                 width=None,height=None,
                 visibility=True, state=Label.STATE_DEFAULT,
                 background_color = Label.BLUE, # 默认蓝色背景
                 transparent_color = Label.PINK): 
        """
        初始化按钮控件
        
        继承Label的所有参数，额外添加：
            border_radius: 边框圆角半径
        """
        super().__init__(text = text,
                         font = font,
                         font_scale = font_scale,
                         text_color = text_color,
                         align = align,
                         padding = padding,

                         abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         background_color = background_color,
                         transparent_color = transparent_color)
        
        # 状态对应的样式
        self.styles = {
            self.STATE_DEFAULT: {
                'background_color': background_color,
                'text_color': text_color
            },
            self.STATE_PRESSED: {
                'background_color': _darken_color(background_color, 0.7),
                'text_color': text_color
            },
            self.STATE_DISABLED: {
                'background_color': 0x7BEF,  # 灰色
                'text_color': 0xC618  # 暗灰色
            }
        }
        
        self.event_listener = {EventType.CLICK:[self.press,self.release],
                               EventType.PRESS:[self.press],
                               EventType.RELEASE:[self.release],
                               EventType.LONG_PRESS:[self.press],
                               EventType.LONG_PRESS_RELEASE:[self.long_press_release],
                               EventType.DOUBLE_CLICK:[self.press,self.release]}
        
    
    
    @micropython.native
    def _create_bitmap(self):
        """
        创建按钮位图
        添加边框和状态效果
        """
        # 获取当前状态的样式
        style = self.styles[self.state]
        # 创建新的位图
        bitmap = Bitmap(self.width, self.height,transparent_color=self.transparent_color)
        # 填充背景
        bitmap.fill_rect(0, 0, self.width, self.height, style['background_color'])        
        # 绘制文本部分
        # 临时保存原来的颜色
        original_text_color = self.text_color
        self.text_color = style['text_color']
        # 创建文本位图
        self._text_bitmap = self._create_text_bitmap()
        # 计算文本位置（从Label类复用此逻辑）
        text_x, text_y = self._calculate_text_position()
        # 将文本bitmap绘制到背景
        bitmap.blit(self._text_bitmap, dx=text_x, dy=text_y)
        # 恢复原来的颜色
        self.text_color = original_text_color
        return bitmap
      
    def set_enabled(self, enabled):
        """设置按钮是否可用"""
        new_state = self.STATE_DEFAULT if enabled else self.STATE_DISABLED
        if new_state != self.state:
            self.enabled = enabled
            self.state = new_state
            self._content_dirty = True
            self.register_dirty()

    def set_state(self, state):
        if state in self.styles and self.state != state:
            self.state = state
            self._content_dirty = True
            self.register_dirty()

    def press(self,event):
        """
        按钮按下
        状态为STATE_PRESSED
        """
        self.set_state(self.STATE_PRESSED)
    def release(self,event):
        self.set_state(self.STATE_DEFAULT)
    
    def long_press_release(self,event):
        self.set_state(self.STATE_DEFAULT)
    

