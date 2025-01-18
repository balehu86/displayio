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
    __slots__ = ('widget', 'dx', 'dy', 'width', 'height', 'transparent_color', 'color_format',
                 'size_changed', 'buffer', 'fb')
    
    # 支持的颜色格式
    MONO_VLSB = framebuf.MONO_VLSB
    MONO_HLSB = framebuf.MONO_HLSB
    MONO_HMSB = framebuf.MONO_HMSB
    RGB565 = framebuf.RGB565
    GS2_HMSB = framebuf.GS2_HMSB
    GS4_HMSB = framebuf.GS4_HMSB
    GS8 = framebuf.GS8

    def __init__(self, widget=None, transparent_color=None):
        self.widget = widget
        self.dx = None
        self.dy = None
        self.width = None
        self.height = None
        self.transparent_color = transparent_color if transparent_color is not None else 0xf81f # trans color 可能为0x0000
        self.color_format = widget.color_format if widget else self.RGB565

        self.size_changed = False
        self.buffer = None
        self.fb = None
    
    def init(self, dx=0, dy=0, width=0, height=0, color=None, transparent_color=None):
        """bitmap初始化
        Args:
            dx: bitmap的目标位置
            dy: bitmap的目标位置
            width: 宽度
            height: 高度
            transparent_color: 透明色
        """
        self.dx = dx
        self.dy = dy

        new_width = width or (self.widget.width if self.widget else 0)
        if self.width != new_width:
            self.width = new_width
            self.size_changed = True

        new_height = height or (self.widget.height if self.widget else 0)
        if self.height != new_height:
            self.height = new_height
            self.size_changed = True

        if transparent_color is not None: # 设置透明色
            self.transparent_color = transparent_color
        
        if self.size_changed: # 尺寸变化
            buffer_size = self.width * self.height
            if self.color_format == self.RGB565:
                buffer_size *= 2
            self.buffer = bytearray(buffer_size)
            self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, self.color_format)
            # self.fb = FrameBuffer(self.buffer, self.width, self.height, self.color_format)
            self.size_changed = False
            # 初始化颜色填充，跳过纯黑色填充
            if color is not None and color != 0x0000:
                self.fill(color)
        elif color is not None: # 尺寸未变，传递了color，只需填充颜色
            # if self.fb:  # 确保已初始化FrameBuffer
            self.fill(color)
            return

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


class FrameBuffer:
    def __init__(self, buffer, width, height, color_format):
        self.buffer = buffer
        self.width = width
        self.height = height
        self.color_format = color_format

    @micropython.native
    def pixel(self, x, y, color=None):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return  # Ignore pixels out of bounds

        byte_index = (y * self.width + x) * 2

        if color is None:
            # Get pixel value
            # return (self.buffer[byte_index] << 8) | self.buffer[byte_index + 1]
            return self.buffer[byte_index] | (self.buffer[byte_index + 1] << 8)
        else:
            # Set pixel value
            # self.buffer[byte_index] = (color >> 8) & 0xFF
            # self.buffer[byte_index + 1] = color & 0xFF
            self.buffer[byte_index] = color & 0xFF
            self.buffer[byte_index + 1] = (color >> 8) & 0xFF

    @micropython.native
    def fill(self, color):
        for byte_index in range(0, len(self.buffer), 2):
            # self.buffer[byte_index] = (color >> 8) & 0xFF
            # self.buffer[byte_index + 1] = color & 0xFF
            self.buffer[byte_index] = color & 0xFF
            self.buffer[byte_index + 1] = (color >> 8) & 0xFF

    @micropython.native
    def fill_rect(self, x, y, width, height, color):
        for j in range(height):
            for i in range(width):
                if 0 <= x + i < self.width and 0 <= y + j < self.height:  # 边界检查
                    byte_index = ((y + j) * self.width + (x + i)) * 2
                    # self.buffer[byte_index] = (color >> 8) & 0xFF
                    # self.buffer[byte_index + 1] = color & 0xFF
                    self.buffer[byte_index] = color & 0xFF
                    self.buffer[byte_index + 1] = (color >> 8) & 0xFF

    @micropython.native
    def blit(self, source, dx=0, dy=0, key=-1):
        for j in range(source.height):
            for i in range(source.width):
                if 0 <= dx + i < self.width and 0 <= dy + j < self.height:  # 边界检查
                    color = source.pixel(i, j)  # 获取颜色值
                    if color != key:  # 非透明色
                        self.pixel(dx + i, dy + j, color)
                        byte_index = ((dy+j) * self.width + (dx+i)) * 2
                        # self.buffer[byte_index] = (color >> 8) & 0xFF
                        # self.buffer[byte_index + 1] = color & 0xFF
                        self.buffer[byte_index] = color & 0xFF
                        self.buffer[byte_index + 1] = (color >> 8) & 0xFF
