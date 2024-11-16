# ./widget/label.py

from ..core.widget import Widget
from ..core.bitmap import Bitmap

from ..utils.font_utils import hex_font_to_bitmap
from ..utils.decorator import timeit

class Label(Widget):
    """
    标签控件类
    用于显示文本内容，支持自定义颜色、对齐方式等
    """
    
    # 文本对齐方式常量
    ALIGN_LEFT = 'left'
    ALIGN_CENTER = 'center'
    ALIGN_RIGHT = 'right'
    ALIGH_TOP = 'top'
    ALIGN_BOTTOM = 'bottom'
    
    def __init__(self, 
                 text="",
                 font=None,  # 字体字典数据
                 text_color=0xf800,  # 文字颜色（默认红色）
                 background=0x7f34,  # 背景色（默认绿色）
                 align=ALIGN_LEFT,  # 文本对齐方式
                 padding=(2, 2, 2, 2),
                 x=0,y=0,width=None,height=None,visibility=True):  # 内边距 (左,上,右,下)
        """
        初始化标签控件
        
        参数:
            text: 显示的文本内容
            font: 字体数据对象，包含点阵信息
            text_color: 文字颜色（16位RGB颜色）
            background: 背景颜色（16位RGB颜色）
            align: 文本对齐方式
            padding: 内边距，格式为(左,上,右,下)
            visibility: 是否可见
        """
        super().__init__(x = x, y = y, width = width, height = height, visibility = visibility)
        self.text = text
        self.font = font
        if font is not None:
            self.font_width = font['WIDTH']
            self.font_height = font['HEIGHT']
            self.font_default = font['DEFAULT']
        self.text_color = text_color
        self.background = background
        self.align = align
        self.padding = padding
    
    def _create_bitmap(self):
        """
        创建控件的位图
        包含背景和文本渲染
        """
        
        # 创建新的位图
        bitmap = Bitmap(self.width, self.height)
        # cache字体的 大小 数据
        font_width = self.font_width
        font_height = self.font_height
        
        # 填充背景
        bitmap.fill_rect(0, 0, self.width, self.height, self.background)
        
        if self.text and self.font:
            # 计算文本总宽度
            text_total_width = len(self.text) * font_width
            text_total_height = font_height
            
            # 根据水平方向对齐方式计算起始x坐标
            if self.align == self.ALIGN_LEFT:
                text_x = self.padding[0]
            elif self.align == self.ALIGN_CENTER:
                text_x = (self.width - text_total_width) // 2
            else:  # ALIGN_RIGHT
                text_x = self.width - text_total_width - self.padding[2]
            
            # 根据垂直方向对齐方式计算起始y坐标
            if self.align == self.ALIGH_TOP:
                text_y = self.padding[1]
            elif self.align == self.ALIGN_BOTTOM:
                text_y = self.height - text_total_height - self.padding[3]
            else:  # ALIGN_CENTER
                text_y = (self.height - font_height) // 2
            
            # 渲染每个字符
            for i, char in enumerate(self.text):
                if char in self.font:
                    char_bitmap = hex_font_to_bitmap(
                        self.font[char], font_width, font_height,
                        foreground=self.text_color, rle=self.font['rle'])
                else:
                    char_bitmap = hex_font_to_bitmap(
                        self.font_default, font_width, font_height,
                        foreground=self.text_color, rle=self.font['rle'])
                # 将字符位图复制到主位图
                x = text_x + i * font_width
                bitmap.blit(char_bitmap, dx=x, dy=text_y)
        
        return bitmap
    
    # @timeit
    def get_bitmap(self):
        """
        获取控件的位图
        如果需要重绘，先创建新的位图
        """
        if self.visibility:
            self._bitmap = self._create_bitmap()
            self._dirty = False  # 绘制完成后清除脏标记
            return self._bitmap
        else:
            bitmap=Bitmap(self.width,self.height)
            bitmap.fill_rect(0,0,self.width,self.height,super().PINK)
            self._dirty = False  # 绘制完成后清除脏标记
            return bitmap          

    
    def set_text(self, text):
        """设置文本内容"""
        if self.text != text:
            self.text = text
            self.register_dirty()
    
    def set_color(self, text_color=None, background=None):
        """设置文本和背景颜色"""
        if text_color is not None:
            self.text_color = text_color
        if background is not None:
            self.background = background
        self.register_dirty()

    def set_font(self,font):
        """设置字体"""
        self.font = font
        self.font_width = font['WIDTH']
        self.font_height = font['HEIGHT']
        self.font_default = font['DEFAULT']
        self.register_dirty()
    def set_align(self,align):
        """设置文本对齐"""
        self.align = align
        self.register_dirty()
    def set_padding(self,padding):
        """设置文本边距"""
        self.padding = padding
        self.register_dirty()