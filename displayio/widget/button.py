# ./widget/button.py
from .label import Label
from ..core.event import EventType

import micropython # type: ignore

class Button(Label):
    """
    按钮控件类
    继承自Label,添加了状态和交互功能
    """
    __slots__ = ('styles',)

    def __init__(self,
                 
                 text="",
                 font=None,
                 font_scale=1,
                 text_color=Label.WHITE, # 文字颜色默认白色
                 background_color=Label.Button_BLUE, # 背景颜色默认蓝色
                 align=Label.ALIGN_CENTER,  # 按钮文字默认居中
                 padding=(5, 3, 5, 3),  # 按钮默认较大内边距
                 
                 abs_x=None, abs_y=None,
                 rel_x=0,rel_y=0, dz=0,
                 width=None,height=None,
                 visibility=True, state=Label.STATE_DEFAULT,
                 default_color= Label.WHITE,
                 transparent_color=Label.PINK,
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
                         background_color = background_color,
                         align = align,
                         padding = padding,

                         abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         default_color = default_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        
        # 设置状态对应色彩样式
        self.set_styles()
        
        self.event_listener = {EventType.CLICK:[self.release],
                               EventType.PRESS:[self.press],
                               EventType.RELEASE:[self.release],
                            #    EventType.LONG_PRESS:[self.press],
                               EventType.LONG_PRESS_RELEASE:[self.long_press_release],
                               EventType.DOUBLE_CLICK:[self.release],
                               }
        
    @micropython.native
    def _create_bitmap(self) -> None:
        """
        创建按钮位图
        添加边框和状态效果
        """
        # 获取当前状态的样式
        style = self.styles[self.state]
        # 创建和填充新的位图
        self._bitmap.init(dx=self.dx,dy=self.dy,color=style['background_color'])
        # 绘制文本部分
        # 临时保存原来的颜色
        original_text_color = self.text_color
        self.text_color = style['text_color']
        # 创建文本位图
        if self._text_dirty:
            self._create_text_bitmap()
        # 计算文本位置（从Label类复用此逻辑）
        text_x, text_y = self._calculate_text_position()
        # 将文本bitmap绘制到背景
        self._bitmap.blit(self._text_bitmap, dx=text_x, dy=text_y)
        # 恢复原来的颜色
        self.text_color = original_text_color

        if not self.layout_changed: # 如果布局未改变则直接返回self._bitmap
            return self._bitmap
        # 计算当前的dx, dy, width, height
        current_dx, current_dy, current_width, current_height = self.dx, self.dy, self.width, self.height
        # 计算原始的dx, dy, width, height
        original_dx = self.dx_cache if self.dx_cache is not None else current_dx
        original_dy = self.dy_cache if self.dy_cache is not None else current_dy
        original_width = self.width_cache if self.width_cache is not None else current_width
        original_height = self.height_cache if self.height_cache is not None else current_height
        # 计算包围盒bitmap的起始左上角坐标
        bitmap_min_x = min(original_dx, current_dx)
        bitmap_min_y = min(original_dy, current_dy)
        # 计算原始位置的边界坐标
        original_x_max, original_y_max = original_dx + original_width - 1, original_dy + original_height - 1
        # 计算当前位置的边界坐标
        current_x_max, current_y_max = current_dx + current_width - 1, current_dy + current_height - 1
        # 计算包围盒bitmap的宽高
        bitmap_width = max(original_x_max, current_x_max) - bitmap_min_x +1
        bitmap_height = max(original_y_max, current_y_max) - bitmap_min_y + 1
        # 创建包围盒bitmap
        self._bond_bitmap.init(dx=bitmap_min_x, dy=bitmap_min_y, width=bitmap_width, height=bitmap_height, transparent_color=0x0000)
        # 将当前self._bitmap复制到包围盒bitmap
        self._bond_bitmap.blit(self._bitmap, dx=current_dx-bitmap_min_x, dy=current_dy-bitmap_min_y)
        # 恢复缓存的原始dx, dy, width, height
        self.dx_cache, self.dy_cache, self.width_cache, self.height_cache = None, None, None, None
        self.layout_changed = False
        # 返回包围盒bitmap
        # print(f'bond_bitmap, dx={bitmap_min_x}, dy={bitmap_min_y}, width={bitmap_width}, height={bitmap_height}\n\tcurrent_dx={current_dx}, current_dy={current_dy}, current_width={current_width}, current_height={current_height}')
        return self._bond_bitmap
      
    def set_enabled(self, enabled:bool) -> None:
        """设置按钮是否可用"""
        new_state = self.STATE_DEFAULT if enabled else self.STATE_DISABLED
        if new_state != self.state:
            self.enabled = enabled
            self.state = new_state
            self._dirty = True
            self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    def set_state(self, state) -> None:
        if state in self.styles and self.state != state:
            self.state = state
            self._dirty = True
            self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    def press(self,widget,event) -> None:
        """按钮按下,状态为STATE_PRESSED"""
        self.set_state(self.STATE_PRESSED)

    def release(self,widget,event) -> None:
        self.set_state(self.STATE_DEFAULT)
    
    def long_press_release(self,widget,event) -> None:
        self.set_state(self.STATE_DEFAULT)

    def set_color(self, text_color=None, background_color=None) -> None:
        """设置文本和背景颜色"""
        if text_color is not None:
            self.text_color = text_color
        if background_color is not None:
            self.background_color = background_color
        self.set_styles()
        self._dirty = True
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    def set_styles(self):
        # 状态对应的样式
        self.styles = {
            self.STATE_DEFAULT: {'background_color': self.background_color,
                                 'text_color':       self.text_color},
            self.STATE_PRESSED: {'background_color': self._darken_color(self.background_color, 0.7),
                                 'text_color':       self.text_color},
            self.STATE_DISABLED: {'background_color': Label.GREY,
                                  'text_color':       Label.DARK_GREY}}