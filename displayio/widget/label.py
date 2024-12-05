# ./widget/label.py
from ..core.widget import Widget
from ..core.bitmap import Bitmap

from ..utils.font_utils import hex_font_to_bitmap

import micropython # type: ignore

class Label(Widget):
    """
    标签控件类
    用于显示文本内容，支持自定义颜色、对齐方式等
    """    
    def __init__(self, 
                 text="",
                 font=None,  # 字体字典数据
                 font_scale = 1, # 字体放大系数
                 text_color=Widget.RED,  # 文字颜色（默认红色）
                 align=Widget.ALIGN_LEFT,  # 文本对齐方式
                 padding=(2, 2, 2, 2),  # 文字边距,(左,上,右,下)

                 abs_x=None, abs_y=None,
                 rel_x=None,rel_y=None,
                 width=None,height=None,
                 visibility=True, enabled=True,
                 background_color=0x7f34, # 背景色（默认绿色）
                 transparent_color=Widget.PINK):
        """
        初始化标签控件
        
        参数:
            text: 显示的文本内容
            font: 字体数据对象，包含点阵信息
            text_color: 文字颜色（16位RGB颜色）
            background: 背景颜色（16位RGB颜色）
            align: 文本对齐方式
            padding: 内边距，格式为(左,上,右,下)
            corner_radius: 圆角半径
            corner_color: 圆角颜色，None表示使用背景色
            corner_transparent: 圆角是否透明
            visibility: 是否可见
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y,
                         width = width, height = height,
                         visibility = visibility, enabled = enabled,
                         background_color = background_color,
                         transparent_color = transparent_color)
        self.text = text
        if font is None:
            raise ValueError("label.font is not specified!")
        else:
            self.font = font
        self.font_scale = font_scale
        self.font_width = font[b'WIDTH'][0]
        self.font_height = font[b'HEIGHT'][0]
        self.font_default = font[b'DEFAULT']
        self.font_rle = font[b'RLE'][0]
        # 计算文本 总宽度 总高度
        self.text_width = self.font_width * len(text) * font_scale
        self.text_height = self.font_height * font_scale
            
        self.text_color = text_color
        self.background_color = background_color
        self.align = align
        self.padding = padding

        self._text_bitmap = None
        self._cache_bitmap = None

    @micropython.native
    def _create_text_bitmap(self):
        """
        创建控件文本渲染的位图
        """              
        if self.font:
            # 创建新的位图
            bitmap = Bitmap(self.text_width, self.text_height,
                            transparent_color=0,format=Bitmap.RGB565)
            # 渲染每个字符
            text_dx = 0
            for i, char in enumerate(self.text):
                if char in self.font:
                    char_bitmap = hex_font_to_bitmap(
                        self.font[bytes(char,'ascii')], self.font_width, self.font_height,
                        foreground=self.text_color, rle=self.font_rle, scale=self.font_scale)
                else:
                    char_bitmap = hex_font_to_bitmap(
                        self.font_default, self.font_width, self.font_height,
                        foreground=self.text_color, rle=self.font_rle, scale=self.font_scale)
                # 将字符位图复制到主位图
                x = text_dx + i * self.font_width * self.font_scale
                bitmap.blit(char_bitmap, dx=x, dy=0)
            return bitmap
        # 能到这步，说明没有给self.font，直接报错
        raise ValueError("未知的字体库")
    
    @micropython.native
    def _calculate_text_position(self):
        """
        根据文本对齐方式计算文本位图位置
        """ 
        text_x = self.padding[0]  # 默认左对齐
        text_y = (self.height - self.font_height) // 2  # 默认垂直居中
        
        if self.align == self.ALIGN_CENTER:
            text_x = (self.width - self.text_width) // 2
        elif self.align == self.ALIGN_RIGHT:
            text_x = self.width - self.text_width - self.padding[2]
            
        if self.align == self.ALIGH_TOP:
            text_y = self.padding[1]
        elif self.align == self.ALIGN_BOTTOM:
            text_y = self.height - self.text_height - self.padding[3]
        return text_x, text_y
    
    @micropython.native
    def _create_bitmap(self):
        """
        创建控件的位图
        包含背景和文本渲染
        """
        # 创建新的位图
        bitmap = Bitmap(self.width, self.height,
                        transparent_color=self.transparent_color,format=Bitmap.RGB565)
        # 填充背景
        bitmap.fill_rect(0, 0, self.width, self.height, self.background_color)
        # 绘制文字
        self._text_bitmap = self._create_text_bitmap()
        # 计算文本位置
        text_x, text_y = self._calculate_text_position()
        # 将文本bitmap绘制到背景
        bitmap.blit(self._text_bitmap, dx=text_x, dy=text_y)
        return bitmap
    
    # @timeit
    def get_bitmap(self):
        """
        获取控件的位图
        如果需要重绘，先创建新的位图
        """
        if self.visibility:
            if self._content_dirty:
                self._bitmap = self._create_bitmap()
                self._content_dirty = False
            return self._bitmap
        else:
            if self._cache_bitmap is None:
                self._cache_bitmap = Bitmap(self.width,self.height,
                                            transparent_color=self.transparent_color,
                                            format=Bitmap.RGB565)
                self._cache_bitmap.fill_rect(0,0,self.width,self.height,self.background_color)
            return self._cache_bitmap
    
    def set_text(self, text):
        """设置文本内容"""
        if self.text != text:
            self.text = text
            self.text_width = self.font_width * len(text) * self.font_scale
            self._content_dirty = True
            self.register_dirty()
    def set_color(self, text_color=None, background_color=None):
        """设置文本和背景颜色"""
        if text_color is not None:
            self.text_color = text_color
        if background_color is not None:
            self.background_color = background_color
        self._content_dirty = True
        self.register_dirty()
    def set_font(self,font):
        """设置字体"""
        self.font = font
        self.font_width = font[b'WIDTH'][0]
        self.font_height = font[b'HEIGHT'][0]
        self.font_default = font[b'DEFAULT']
        self.font_rle = font[b'RLE'][0]
        self.text_width = self.font_width * len(self.text) * self.font_scale
        self.text_height = self.font_height * self.font_scale
        self._content_dirty = True
        self.register_dirty()
    def set_align(self,align):
        """设置文本对齐"""
        self.align = align
        self._content_dirty = True
        self.register_dirty()
    def set_padding(self,padding):
        """设置文本边距"""
        self.padding = padding
        self._content_dirty = True
        self.register_dirty()
