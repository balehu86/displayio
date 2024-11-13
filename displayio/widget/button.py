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
                 text="",
                 font=None,
                 text_color=0xFFFF,
                 background=0x841F,  # 默认蓝色背景
                 align=Label.ALIGN_CENTER,  # 按钮文字默认居中
                 padding=(5, 3, 5, 3),  # 按钮默认较大内边距
                 border_radius=2):  # 圆角半径
        """
        初始化按钮控件
        
        继承Label的所有参数，额外添加：
            border_radius: 边框圆角半径
        """
        super().__init__(text, font, text_color, background, align, padding)
        
        self.border_radius = border_radius
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

        bitmap = Bitmap(self.width, self.height)
        
        # 获取当前状态的样式
        style = self.styles[self.state]
        
        # 绘制背景（带圆角）
        self._draw_rounded_rect(
            bitmap,
            0, 0,
            self.width, self.height,
            self.border_radius,
            style['background']
        )
        
        # 设置文本颜色并绘制文本
        self.text_color = style['text_color']
        
        # 调用父类的方法绘制文本
        text_bitmap = super()._create_bitmap()
        bitmap.blit(text_bitmap, 0, 0)
        
        return bitmap
    
    def _draw_rounded_rect(self, bitmap, x, y, width, height, radius, color):
        """
        绘制圆角矩形
        
        参数:
            bitmap: 目标位图
            x, y: 起始坐标
            width, height: 宽度和高度
            radius: 圆角半径
            color: 填充颜色
        """
        # 填充中心区域
        bitmap.fill_rect(
            x + radius, y,
            width - 2 * radius, height,
            color
        )
        bitmap.fill_rect(
            x, y + radius,
            width, height - 2 * radius,
            color
        )
        
        # 绘制四个圆角
        self._draw_circle(bitmap, x + radius, y + radius, radius, color)
        self._draw_circle(bitmap, x + width - radius, y + radius, radius, color)
        self._draw_circle(bitmap, x + radius, y + height - radius, radius, color)
        self._draw_circle(bitmap, x + width - radius, y + height - radius, radius, color)
    
    def _draw_circle(self, bitmap, cx, cy, radius, color):
        """
        绘制实心圆
        使用Bresenham算法
        """
        x = radius - 1
        y = 0
        dx = 1
        dy = 1
        err = dx - (radius << 1)
        
        while x >= y:
            # 填充每个八分之一圆的水平线
            bitmap.fill_rect(cx - x, cy + y, x << 1, 1, color)
            bitmap.fill_rect(cx - x, cy - y, x << 1, 1, color)
            bitmap.fill_rect(cx - y, cy + x, y << 1, 1, color)
            bitmap.fill_rect(cx - y, cy - x, y << 1, 1, color)
            
            if err <= 0:
                y += 1
                err += dy
                dy += 2
            if err > 0:
                x -= 1
                dx += 2
                err += dx - (radius << 1)
    
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
        if (self.x <= x < self.x + self.width and 
            self.y <= y < self.y + self.height):
            if event_type == 'press':
                self.state = self.STATE_PRESSED
                self.dirty = True
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

