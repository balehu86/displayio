import time
from micropython import const # type: ignore
import ustruct as struct # type: ignore

# commands
ST77XX_NOP = const(0x00)        # 无操作指令,通常用于测试或占位。
ST77XX_SWRESET = const(0x01)    # 软件复位,清空内部寄存器。
ST77XX_RDDID = const(0x04)      # 读取设备 ID
ST77XX_RDDST = const(0x09)      # 读取显示状态

ST77XX_SLPIN = const(0x10)      # 进入睡眠模式
ST77XX_SLPOUT = const(0x11)     # 退出睡眠模式,需要重新初始化设置
ST77XX_PTLON = const(0x12)      # 进入部分显示模式,只刷新设置的显示区域
ST77XX_NORON = const(0x13)      # 进入正常显示模式

ST77XX_INVOFF = const(0x20)     # 关闭颜色反转
ST77XX_INVON = const(0x21)      # 开启颜色反转
ST77XX_DISPOFF = const(0x28)    # 关闭显示内容（像素熄灭）。但不影响显示内容的内存。
ST77XX_DISPON = const(0x29)     # 打开显示内容，使像素再次可见
ST77XX_CASET = const(0x2A)      # 设置列地址, 设置要操作的列地址范围（水平坐标范围）。发送 4 字节数据：第 1、2 字节表示起始列，第 3、4 字节表示结束列。
ST77XX_RASET = const(0x2B)      # 设置行地址, 设置要操作的行地址范围（垂直坐标范围）。发送 4 字节数据：第 1、2 字节表示起始行，第 3、4 字节表示结束行。
ST77XX_RAMWR = const(0x2C)      # 写入显示内存, 向指定的显示内存区域写入像素数据。通常在调用 CASET 和 RASET 指定的区域内进行操作
ST77XX_RAMRD = const(0x2E)      # 读取显示内存, 从显示内存中读取数据。通常用于调试或校验显示内容。

ST77XX_PTLAR = const(0x30)
ST7789_VSCRDEF = const(0x33)
ST7789_MADCTL = const(0x36)     # 设置屏幕显示方向, 控制图像的旋转和镜像，定义显示方向。包括水平、垂直、RGB 顺序等参数。
ST7789_VSCSAD = const(0x37)
ST77XX_COLMOD = const(0x3A)     # 设置颜色模式, 设置像素格式（颜色深度）。可以选择 RGB 16 位（RGB565）、18 位（RGB666）等模式。

ST7789_MADCTL_MY = const(0x80)  # MADCTL_MY：垂直镜像（上下翻转）                         
ST7789_MADCTL_MX = const(0x40)  # MADCTL_MX：水平镜像（左右翻转）          
ST7789_MADCTL_MV = const(0x20)  # MADCTL_MV：旋转显示（90 度旋转）
ST7789_MADCTL_ML = const(0x10)  # 
ST7789_MADCTL_MH = const(0x04)          
ST7789_MADCTL_RGB = const(0x00)
ST7789_MADCTL_BGR = const(0x08) # MADCTL_RGB：RGB 顺序（默认，RGB 顺序不变）

ST7789_RAMCTL = const(0xb0)

ST7789_RDID1 = const(0xDA)
ST7789_RDID2 = const(0xDB)
ST7789_RDID3 = const(0xDC)
ST7789_RDID4 = const(0xDD)

ColorMode_65K = const(0x50)
ColorMode_262K = const(0x60)
ColorMode_12bit = const(0x03)
ColorMode_16bit = const(0x05)
ColorMode_18bit = const(0x06)
ColorMode_16M = const(0x07)

# Color definitions
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

_ENCODE_PIXEL = ">H"     # 大端模式
_ENCODE_PIXEL_SWAPPED = const("<H")# 小端模式
_ENCODE_POS = ">HH"
_ENCODE_POS_SWAPPED = "<HH"
# _DECODE_PIXEL = ">BBB"

# must be at least 128 for 8 bit wide fonts
# must be at least 256 for 16 bit wide fonts
_BUFFER_SIZE = const(256)

def delay_ms(ms):
    time.sleep_ms(ms)

def color565(r, g=0, b=0):
    """Convert red, green and blue values (0-255) into a 16-bit 565 encoding.  As
    a convenience this is also available in the parent adafruit_rgb_display
    package namespace."""
    try:
        r, g, b = r  # see if the first var is a tuple/list
    except TypeError:
        pass
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

class ST7789:
    RGB = const(0x00)
    BGR = const(0x08)
    def __init__(self, spi, reset, dc, cs=None, backlight=None,
                 width=240, height=240, is_bgr=False, xstart=0, ystart=0):

        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight

        self.width = width
        self.height = height

        self.is_bgr = is_bgr
        self.xstart = xstart
        self.ystart = ystart

    def dc_low(self):
        self.dc.off()

    def dc_high(self):
        self.dc.on()

    def reset_low(self):
        if self.reset:
            self.reset.off()

    def reset_high(self):
        if self.reset:
            self.reset.on()

    def cs_low(self):
        if self.cs:
            self.cs.off()

    def cs_high(self):
        if self.cs:
            self.cs.on()

    def write(self, command=None, data=None):
        """SPI write to the device: commands and data"""
        self.cs_low()
        if command is not None:
            self.dc_low()
            self.spi.write(bytes([command]))
        if data is not None:
            self.dc_high()
            self.spi.write(data)
        self.cs_high()

    def write_cmd(self, cmd):
        """写命令"""
        self.dc_low()  # DC低电平表示命令
        self.cs_low()  # 选中芯片
        self.spi.write(bytes([cmd]))
        self.cs_high()  # 取消片选
        
    def write_data(self, data):
        """写数据"""
        self.dc_high()  # DC高电平表示数据
        self.cs_low()
        self.spi.write(data)
        self.cs_high()

    def hard_reset(self):
        self.cs_low()
        self.reset_high()
        delay_ms(50)
        self.reset_low()
        delay_ms(50)
        self.reset_high()
        delay_ms(150)
        self.cs_high()

    def soft_reset(self):
        self.write_cmd(ST77XX_SWRESET)
        delay_ms(150)

    def set_sleep_mode(self, value):
        if value:
            self.write_cmd(ST77XX_SLPIN)
        else:
            self.write_cmd(ST77XX_SLPOUT)

    def set_inversion_mode(self, value):
        if value:
            self.write_cmd(ST77XX_INVON)
        else:
            self.write_cmd(ST77XX_INVOFF)

    def set_color_mode(self, mode):
        self.write(ST77XX_COLMOD, bytes([mode & 0x77]))
    
    def set_mem_access_mode(self, rotation, vert_mirror, horz_mirror, is_bgr):
        rotation &= 7
        value = {
            0: 0,
            1: ST7789_MADCTL_MX,
            2: ST7789_MADCTL_MY,
            3: ST7789_MADCTL_MX | ST7789_MADCTL_MY,
            4: ST7789_MADCTL_MV,
            5: ST7789_MADCTL_MV | ST7789_MADCTL_MX,
            6: ST7789_MADCTL_MV | ST7789_MADCTL_MY,
            7: ST7789_MADCTL_MV | ST7789_MADCTL_MX | ST7789_MADCTL_MY,
        }[rotation]

        if vert_mirror:
            value = ST7789_MADCTL_ML
        elif horz_mirror:
            value = ST7789_MADCTL_MH

        if is_bgr:
            value |= ST7789_MADCTL_BGR
        self.write(ST7789_MADCTL, bytes([value]))

    def init(self,color_mode=ColorMode_65K | ColorMode_16bit):
        self.hard_reset()
        self.soft_reset()
        # 退出睡眠模式
        self.set_sleep_mode(False)
        time.sleep_ms(10)
        # 设置颜色模式
        self.set_color_mode(color_mode)
        delay_ms(50)

        # 设置显示方向和颜色顺序
        # 使用RGB顺序，不进行镜像
        rotation = 0  # 正常方向
        vert_mirror = False
        horz_mirror = False
        is_bgr = self.is_bgr
        self.set_mem_access_mode(rotation, vert_mirror, horz_mirror, is_bgr)

        # 设置颜色反转
        self.set_inversion_mode(True)
        delay_ms(10)

        # 进入正常显示模式
        self.write(ST77XX_NORON)
        delay_ms(10)

        self.fill(0)
        # 打开显示
        self.write(ST77XX_DISPON)
        delay_ms(50)

    def _encode_pos(self, x, y):
        """Encode a postion into bytes."""
        return struct.pack(_ENCODE_POS, x, y)

    def _encode_pixel(self, color):
        """Encode a pixel color into bytes."""
        return struct.pack(_ENCODE_PIXEL, color)

    def _set_columns(self, start, end):
        if start > end or end >= self.width:
            return
        start += self.xstart
        end += self.xstart
        self.write(ST77XX_CASET, self._encode_pos(start, end))

    def _set_rows(self, start, end):
        if start > end or end >= self.height:
            return
        start += self.ystart
        end += self.ystart
        self.write(ST77XX_RASET, self._encode_pos(start, end))

    def set_window(self, x0, y0, x1, y1):
        self._set_columns(x0, x1)
        self._set_rows(y0, y1)
        self.write_cmd(ST77XX_RAMWR)

    def fill_rect(self, x, y, width, height, color):
        self.set_window(x, y, x + width - 1, y + height - 1)
        chunks, rest = divmod(width * height, _BUFFER_SIZE)
        pixel = self._encode_pixel(color)
        if chunks:
            data = pixel * _BUFFER_SIZE
            for _ in range(chunks):
                self.write_data(data)
        if rest:
            self.write_data(pixel * rest)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def refresh(self, buffer, dx=0, dy=0, width=0, height=0):
        """将位图数据刷新到显示屏"""  
        self.set_window(dx, dy, dx + width - 1, dy + height - 1)     
        self.write_data(buffer)

    def _thread_refresh_wrapper(self, args, lock):
        """线程刷新的包装器，增加线程生命周期管理"""
        old_buffer = None
        try:
            while args['thread_running']:
                # 使用实例方法和实例属性
                if old_buffer != args['buffer']:
                    with lock:
                        self.set_window(
                            args['dx'], args['dy'], 
                            args['dx'] + args['width'] - 1, 
                            args['dy'] + args['height'] - 1)
                        self.write_data(args['buffer'])
                        old_buffer = args['buffer']
                time.sleep_ms(3)
        except Exception as e:
            print(f"Thread refresh error: {e}")
        finally:
            print("Display refresh thread terminated")
