# ./widget/button.py
from .label import Label
from ..core.bitmap import Bitmap

class Button(Label):
    """
    按钮控件类
    继承自Label，添加了状态和交互功能
    """
    
    # 按钮状态常量
    STATE_NORMAL = 0
    STATE_PRESSED = 1
    STATE_DISABLED = 2
    
    def __init__(self,
                 border_radius=2,  # 圆角半径

                 text="",
                 font=None,
                 text_color=0xFFFF,
                 background=0x841F,  # 默认蓝色背景
                 align=Label.ALIGN_CENTER,  # 按钮文字默认居中
                 padding=(5, 3, 5, 3),  # 按钮默认较大内边距
                 
                 abs_x=None, abs_y=None,
                 rel_x=None,rel_y=None,
                 width=None,height=None,
                 visibility=True): 
        """
        初始化按钮控件
        
        继承Label的所有参数，额外添加：
            border_radius: 边框圆角半径
        """
        super().__init__(text = text,
                         font = font,
                         text_color = text_color,
                         background = background,
                         align = align,
                         padding = padding,

                         abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility)

        self.state = self.STATE_NORMAL
        
        # 状态对应的样式
        self.styles = {
            self.STATE_NORMAL: {
                'background': background,
                'text_color': text_color
            },
            self.STATE_PRESSED: {
                'background': self._darken_color(background, 0.7),
                'text_color': text_color
            },
            self.STATE_DISABLED: {
                'background': 0x7BEF,  # 灰色
                'text_color': 0xC618  # 暗灰色
            }
        }
        
        # 事件回调
        self.on_press = None
        self.on_release = None
        # on_click == on_press + on_release
        self.on_click = None
        # on_hold == on_press + times + on_release
        self.on_hold = None
        
    
    def _darken_color(self, color, factor):
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
    
    def _create_bitmap(self):
        """
        创建按钮位图
        添加边框和状态效果
        """
        # 获取当前状态的样式
        style = self.styles[self.state]
        # 创建新的位图
        bitmap = Bitmap(self.width, self.height)
        # 填充背景
        bitmap.fill_rect(0, 0, self.width, self.height, style['background'])        
        # 绘制文本部分
        # 临时保存原来的颜色
        original_color = self.text_color
        self.text_color = style['text_color']
        # 创建文本位图
        self._text_bitmap = self._create_text_bitmap()
        # 计算文本位置（从Label类复用此逻辑）
        text_x, text_y = self._calculate_text_position()
        # 将文本bitmap绘制到背景
        bitmap.blit(self._text_bitmap, dx=text_x, dy=text_y)
        # 恢复原来的颜色
        self.text_color = original_color
            
        return bitmap
    def get_bitmap(self):
        """
        获取控件的位图
        如果需要重绘，先创建新的位图
        """
        if self.visibility:
            if self._content_dirty:
                self._bitmap = self._create_bitmap()
                self._content_dirty = False
            self._dirty = False
            return self._bitmap
        else:
            if self._cache_bitmap is None:
                self._cache_bitmap = Bitmap(self.width,self.height)
                self._cache_bitmap.fill_rect(0,0,self.width,self.height,super().PINK)
            self._dirty = False
            return self._cache_bitmap
    
    def handle_touch(self, event_type, x, y):
        """
        处理触摸事件
        
        参数:
            event_type: 事件类型（按下/释放）
            x, y: 触摸坐标
        """
        if self.state == self.STATE_DISABLED:
            return False
            
        # 检查坐标是否在按钮范围内
        if (self.dx <= x < self.dx + self.width and 
            self.dy <= y < self.dy + self.height):
            if event_type == 'press':
                self.state = self.STATE_PRESSED
                self.register_content_dirty()
                if self.on_press:
                    self.on_press()
                return True
            elif event_type == 'release':
                self.state = self.STATE_NORMAL
                self.dirty = True
                if self.on_release:
                    self.on_release()
                return True
        return False
    
    def set_enabled(self, enabled):
        """设置按钮是否可用"""
        new_state = self.STATE_NORMAL if enabled else self.STATE_DISABLED
        if new_state != self.state:
            self.state = new_state
            self.dirty = True
    def set_state(self, state):
        if state in self.styles and self.state != state:
            self.state = state
            self.register_content_dirty()
    def bind(self, event_type, callback):
        if event_type == 'press':
            self.on_press = callback
        elif event_type == 'release':
            self.on_release = callback
        elif event_type == 'click':
            self.on_click = callback
        elif event_type == 'hold':
            self.on_hold = callback

