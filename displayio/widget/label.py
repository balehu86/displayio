# ./widget/label.py
from ..core.bitmap import Bitmap
from ..utils.font_utils import hex_font_to_bitmap

from .widget import Widget

import micropython # type: ignore

class Label(Widget):
    """
    标签控件类
    用于显示文本内容，支持自定义颜色、对齐方式等
    """
    __slots__ = ('font', 'font_scale', 'font_width', 'font_height', 'font_default', 'font_rle',
                 'text','text_width','text_height', 'text_color',
                 'align', 'padding','_text_bitmap')

    def __init__(self, 
                 text="",
                 font=None,  # 字体字典数据
                 font_scale=1, # 字体放大系数
                 text_color=Widget.RED,  # 文字颜色（默认红色）
                 align=Widget.ALIGN_LEFT,  # 文本对齐方式
                 padding=(2, 2, 2, 2),  # 文字边距,(左,上,右,下)

                 abs_x=None, abs_y=None,
                 rel_x=0,rel_y=0, dz=0,
                 width=None,height=None,
                 visibility=True, state=Widget.STATE_DEFAULT,
                 transparent_color=Widget.PINK,
                 background=Widget.GREEN, # 背景颜色（默认绿色）
                 color_format = Widget.RGB565):
        """
        初始化标签控件

        继承Widget所有参数,额外添加:
            text: 显示的文本内容
            font: 字体数据对象，包含点阵信息
            font_scale: 字体放大系数
            text_color: 文字颜色(16位RGB颜色)
            align: 文本对齐方式
            padding: 内边距，格式为(左,上,右,下)
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         transparent_color = transparent_color,
                         background = background,
                         color_format = color_format)

        # 字体数据
        if font is None:
            raise ValueError("label.font is not specified!")
        self.font = font
        self.font_scale = font_scale
        self.font_width = font[b'WIDTH'][0]
        self.font_height = font[b'HEIGHT'][0]
        self.font_default = font[b'DEFAULT']
        self.font_rle = font[b'RLE'][0]
        # 计算文本 总宽度 总高度
        self.text = text
        self.text_width = self.font_width * len(text) * font_scale
        self.text_height = self.font_height * font_scale
        self.text_color = text_color

        self.align = align
        self.padding = padding
        # 文字位图缓存
        self._text_bitmap = Bitmap(transparent_color=0x0000)
        self._text_dirty = True

    @micropython.native
    def _draw_text_bitmap(self) -> None:
        """
        创建控件文本渲染的位图
        """
        if self.font is None:
            # 没有self.font数据，直接报错
            raise ValueError("未知的字体库")

        # 创建新的位图
        self._text_bitmap.init(width=self.text_width,height=self.text_height)
        # 渲染每个字符
        text_dx = 0
        for i, char in enumerate(self.text):
            if char in self.font:
                char_bitmap = hex_font_to_bitmap(
                    self.font[bytes(char,'ascii')], self.font_width, self.font_height,
                    foreground=self.get_text_color, rle=self.font_rle, scale=self.font_scale)
            else:
                char_bitmap = hex_font_to_bitmap(
                    self.font_default, self.font_width, self.font_height,
                    foreground=self.get_text_color, rle=self.font_rle, scale=self.font_scale)
            # 将字符位图复制到主位图
            x = text_dx + i * self.font_width * self.font_scale
            self._text_bitmap.blit(char_bitmap, dx=x, dy=0)

    @micropython.native
    def _calculate_text_position(self) -> tuple[int, int]:
        """
        根据文本对齐方式计算文本位图位置
        """ 
        text_x = self.padding[0]  # 默认左对齐
        text_y = (self.height - self.text_height) // 2  # 默认垂直居中

        if self.align == self.ALIGN_CENTER:
            text_x = (self.width - self.text_width) // 2
        elif self.align == self.ALIGN_RIGHT:
            text_x = self.width - self.text_width - self.padding[2]

        if self.align == self.ALIGN_TOP:
            text_y = self.padding[1]
        elif self.align == self.ALIGN_BOTTOM:
            text_y = self.height - self.text_height - self.padding[3]
        return text_x, text_y

    @micropython.native
    def draw(self) -> None:
        """
        创建控件的位图
        包含背景和文本渲染
        """
        # 创建和填充新的位图
        if self.background.color is None:
            self._bitmap.init(dx=self.dx,dy=self.dy)
            self._bitmap.blit(self.background.pic, dx=0,dy=0)
        else:
            self._bitmap.init(dx=self.dx,dy=self.dy,color=self.get_background_color)
        # 绘制文字
        if self._text_dirty:
            self._draw_text_bitmap()
        # 计算文本位置
        text_x, text_y = self._calculate_text_position()
        # 将文本bitmap绘制到背景
        self._bitmap.blit(self._text_bitmap, dx=text_x, dy=text_y)

    def set_text(self, text=None, color=None, font=None, font_scale=None) -> None:
        """设置文本内容"""
        changed = False
        if text is not None and self.text != text:
            self.text = text
            changed = True
        if color is not None and self.text_color != color:
            self.text_color = color
            changed = True
        if font is not None and self.font is not font:
            self.font = font
            self.font_width = font[b'WIDTH'][0]
            self.font_height = font[b'HEIGHT'][0]
            self.font_default = font[b'DEFAULT']
            self.font_rle = font[b'RLE'][0]
            changed = True
        if font_scale is not None and font_scale != self.font_scale:
            self.font_scale = font_scale
            changed = True
        if changed:
            self._text_dirty = True
            self.text_width = self.font_width * len(self.text) * self.font_scale
            self.text_height = self.font_height * self.font_scale
            self.dirty_system.add_widget(self)
            self.dirty_system.add(self.dx,self.dy,self.width,self.height)
    def set_align(self, align) -> None:
        """设置文本对齐"""
        self.align = align
        self.dirty_system.add_widget(self)
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)
    def set_padding(self, padding) -> None:
        """设置文本边距"""
        self.padding = padding
        self.dirty_system.add_widget(self)
        self.dirty_system.add(self.dx,self.dy,self.width,self.height)

    @property
    def get_background_color(self):
        if self.state == self.STATE_FOCUSED:
            return self._darken_color(self.background.color, 0.7)
        if self.state == self.STATE_DISABLED:
            return Label.GREY
        return self.background.color

    @property
    def get_text_color(self):
        if self.state == self.STATE_DISABLED:
            return Label.DARK_GREY
        return self.text_color