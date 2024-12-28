# ./core/style.py
from .bitmap import Bitmap

class Color:
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
    HORIZONTAL = 0
    VERTICAL = 1
