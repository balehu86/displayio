# ./core/style.py
from .bitmap import Bitmap

class Background:
    def __init__(self, color=None, pic=None):
        if color is None and pic is None:
            raise ValueError('Background 类初始化错误, color 和 pic 参数必须二选一')
        self.color = color
        self.pic = pic

class Color:
    __slots__ = ()
    RED   = 0xf800
    GREEN = 0x07e0
    BLUE  = 0x001f
    PINK  = 0xf81f
    WHITE = 0xffff
    DARK  = 0x0000
    Label_GREEN = 0x7f34
    Button_BLUE = 0x001f
    GREY = 0x7BEF
    DARK_GREY = 0xC618

class Style:
    """
    样式枚举
    """
    __slots__ = ()
    # 支持的颜色格式
    MONO_VLSB = Bitmap.MONO_VLSB
    MONO_HLSB = Bitmap.MONO_HLSB
    MONO_HMSB = Bitmap.MONO_HMSB
    RGB565 = Bitmap.RGB565
    GS2_HMSB = Bitmap.GS2_HMSB
    GS4_HMSB = Bitmap.GS4_HMSB
    GS8 = Bitmap.GS8

    # 文本对齐方式常量
    ALIGN_LEFT = 'left'
    ALIGN_CENTER = 'center'
    ALIGN_RIGHT = 'right'
    ALIGN_TOP = 'top'
    ALIGN_BOTTOM = 'bottom'
    ALIGN_START = 'start'
    ALIGN_END = 'end'

    # 方向
    HORIZONTAL = 'horizontal'
    VERTICAL = 'vertical'
