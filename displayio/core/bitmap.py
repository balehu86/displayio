# ./core/bitmap.py
import framebuf # type: ignore
import micropython # type: ignore

@micropython.viper
def _swap_rgb565(color: int) -> int:
    """交换颜色值的高低字节
        因为framebuf.FrameBuffer的序列为小端序,
        而驱动一般采用大端序
        所以在这里先做个交换第一第二字节的处理，
        可使驱动直接将整个buffer一次性写入屏幕,而不需要使用迭代循环"""
    return ((color >> 8) | (color << 8)) & 0xFFFF

class Bitmap:
    __slots__ = ('widget', 'width', 'height', 'transparent_color', 'color_format',
                'color', 'size_changed', 'buffer', 'fb')
    
    # 支持的颜色格式
    MONO_VLSB = framebuf.MONO_VLSB
    MONO_HLSB = framebuf.MONO_HLSB
    MONO_HMSB = framebuf.MONO_HMSB
    RGB565 = framebuf.RGB565
    GS2_HMSB = framebuf.GS2_HMSB
    GS4_HMSB = framebuf.GS4_HMSB
    GS8 = framebuf.GS8

    def __init__(self, widget=None):
        self.widget = widget
        self.width = None
        self.height = None
        self.transparent_color = widget.transparent_color if widget else 0xf81f
        self.color_format = widget.color_format if widget else self.RGB565
        self.color = widget.background_color if widget else 0x0000

        self.size_changed = False
        self.buffer = None
        self.fb = None
    
    def init(self, width=0, height=0, transparent_color=None, color=None):
        """bitmap初始化
        Args:
            width: 宽度
            height: 高度
            transparent_color: 透明色
        """
        new_width = width or (self.widget.width if self.widget else 0)
        if self.width != new_width:
            self.width = new_width
            self.size_changed = True

        new_height = height or (self.widget.height if self.widget else 0)
        if self.height != new_height:
            self.height = new_height
            self.size_changed = True

        if transparent_color is not None:
            self.transparent_color = transparent_color
        
        # 检查颜色更新
        if color is not None and not self.size_changed:
            if self.color != color:  # 尺寸不变但颜色变化，直接填充
                self.color = color
                if self.fb:  # 确保已初始化FrameBuffer
                    self.fill(color)
            return
        
        # 尺寸变化或首次初始化时重新创建Framebuf
        if self.size_changed:
            buffer_size = self.width * self.height
            if self.color_format == self.RGB565:
                buffer_size *= 2
            self.buffer = bytearray(buffer_size)
            self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, self.color_format)
            self.size_changed = False
            # 初始化颜色填充，跳过纯黑色填充
            if color is not None and color != 0x0000:
                self.fill(color)
            elif self.color != 0x0000 and color is None:
                self.fill(self.color)

    @micropython.native
    def pixel(self, x:int, y:int, color:int|None=None):
        """获取或设置像素点"""
        # 若超出位图范围，直接返回
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        
        if color is None:
            value = self.fb.pixel(x, y)
            return _swap_rgb565(value) if self.color_format == self.RGB565 else value
        
        # 设置像素时转换颜色 
        if self.color_format == self.RGB565:
            color = _swap_rgb565(color)    
        self.fb.pixel(x, y, color)

    @micropython.native
    def fill_rect(self, x:int, y:int, width:int, height:int, color:int):
        """填充矩形区域"""
        # 使用FrameBuffer的原生fill_rect进行填充
        if self.color_format == self.RGB565:  
            color = _swap_rgb565(color)
        self.fb.fill_rect(x, y, width, height, color)

    @micropython.native
    def fill(self, color:int):
        """填充整个区域"""
        if self.color_format == self.RGB565:  
            color = _swap_rgb565(color)
        self.fb.fill(color)
 
    @micropython.native
    def blit(self, source:'Bitmap', dx:int=0, dy:int=0):
        """将源bitmap复制到当前bitmap,使用framebuf的透明色机制"""
        # 如果源和目标的颜色格式不同，转换颜色
        key = source.transparent_color
        if self.color_format == self.RGB565 and source.color_format != self.RGB565:
            key = _swap_rgb565(key) if source.transparent_color != -1 else -1
        elif self.color_format != self.RGB565 and source.color_format == self.RGB565:
            key = _swap_rgb565(key) if source.transparent_color != -1 else -1
        
        # 使用framebuf的blit方法，传入透明色键值
        self.fb.blit(source.fb, dx, dy, key)