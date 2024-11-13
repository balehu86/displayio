import time
from micropython import const
import ustruct as struct
def hex_font_to_bitmap(hex_data, width=8, height=8, foreground=0xFFFF):
    """将点阵数据转换为带透明背景的Bitmap
    
    Args:
        hex_data: 点阵数据（一维列表）。对于16*16的字体，每行需要2个字节表示16个像素；
                对于8*8的字体，每行需要1个字节表示8个像素。
        width: 字符宽度（像素），必须是8的倍数
        height: 字符高度（像素）
        foreground: 前景色
    
    Returns:
        Bitmap: 生成的位图对象
    """
    
    # 验证输入参数
    bytes_per_row = width // 8  # 每行需要的字节数
    expected_data_length = height * bytes_per_row
    
    if not isinstance(hex_data, (list, tuple)) or len(hex_data) != expected_data_length:
        raise ValueError(f"hex_data必须是长度为{expected_data_length}的一维列表，每行需要{bytes_per_row}个字节表示{width}个像素")
    
    if width % 8 != 0:
        raise ValueError("宽度必须是8的倍数")
        
    bitmap = Bitmap(width, height)
    # 默认所有像素都是透明的（alpha=0）
    
    for y in range(height):
        # 获取这一行的所有字节
        row_start = y * bytes_per_row
        row_end = row_start + bytes_per_row
        row_bytes = hex_data[row_start:row_end]
        
        # 处理这一行的每个字节
        for byte_index, byte_value in enumerate(row_bytes):
            # 处理这个字节的8个位
            for bit_pos in range(8):
                x = byte_index * 8 + bit_pos  # 计算实际的x坐标
                if byte_value & (0x80 >> bit_pos):
                    bitmap.pixel(x, y, foreground, 255)
    
    return bitmap

# core/bitmap.py
class Bitmap:
    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height
        self.buffer = bytearray(width * height * 2)  # 16-bit color
        self._alpha_mask = bytearray(width * height)  # 8-bit alpha channel (0=transparent, 255=opaque)
    def pixel(self, x, y, color=None, alpha=None):
        """获取或设置像素点
        
        Args:
            x, y: 坐标
            color: 要设置的颜色值，None表示获取当前颜色
        Returns:
            获取模式下返回当前颜色值
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        pos = (y * self.width + x) * 2
        alpha_pos = y * self.width + x

        if color is None:
            if self._alpha_mask[alpha_pos] == 0:  # 如果是透明像素
                return None
            return (self.buffer[pos] << 8) | self.buffer[pos + 1]
        
        self.buffer[pos] = color >> 8
        self.buffer[pos + 1] = color & 0xFF
        if alpha is not None:
            self._alpha_mask[alpha_pos] = alpha

    def fill_rect(self, x, y, width, height, color, alpha=255):
        for dy in range(height):
            for dx in range(width):
                self.pixel(x + dx, y + dy, color, alpha)
                
    def blit(self, source, sx=0, sy=0, sw=None, sh=None, dx=0, dy=0):
        """将源bitmap复制到当前bitmap
        
        Args:
            source: 源Bitmap对象
            sx, sy: 源bitmap的起始坐标
            sw, sh: 要复制的宽度和高度
            dx, dy: 目标位置
        """
        if sw is None:
            sw = source.width
        if sh is None:
            sh = source.height
            
        for y in range(sh):
            for x in range(sw):
                color = source.pixel(sx + x, sy + y)
                if color is not None:  # 只复制非透明像素
                    alpha_pos = (sy + y) * source.width + (sx + x)
                    alpha = source._alpha_mask[alpha_pos]
                    self.pixel(dx + x, dy + y, color, alpha)

# core/widget.py
class Widget:
    def __init__(self,x = 0, y = 0, 
                 width = None, height = None, hidden = False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # 若已定义宽或高，则布局系统无法设置widget的大小
        self.width_resizable = True if width is None else False
        self.height_resizable = True if height is None else False
        # 缓存的位图对象
        self._bitmap = None
        # 脏标记，Ture则重绘bitmap，并刷新
        self._dirty = True
        self.parent = None
        self.children = []
        # widget 是否可见,_hidden是widget自己hide，hidden是parent让隐藏的
        self._hidden = hidden


    # 从子层，向上层一层层标脏
    def register_dirty(self):
        self._dirty = True
        if self.parent:
            self.parent.register_dirty()
    # 从父层，向下层一层层标脏
    def mark_dirty(self):
        def render_dirty(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    render_dirty(child)
            widget._dirty = True
        render_dirty(self)
        
     
            
    def layout(self, x = 0, y = 0, 
               width = None, height = None):
        """
        布局函数，设置控件的位置和大小
        如果位置或大小发生变化，标记需要重绘
        """
        self.x = x if self.x !=x else self.x
        self.y = y if self.y !=y else self.y
        self.width = width if self.width_resizable and self.width != width else self.width
        self.height = height if self.height_resizable and self.height != height else self.height
        self.register_dirty()

    def hide(self):
        def set_hide(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    set_hide(child)
            widget._hidden = True
        set_hide(self)
        self.register_dirty()
        self.mark_dirty()
        
    def unhide(self):
        def set_unhide(widget):
            if len(widget.children) != 0:
                for child in widget.children:
                    set_unhide(child)
            self._hidden = False
        set_unhide(self)
        self.register_dirty()
        self.mark_dirty()

    def move_to(self, x = 0, y = 0):
        self.x = x if self.x !=x else self.x
        self.y = y if self.y !=y else self.y
        self.register_dirty()

class Container(Widget):
    def __init__(self,x = 0, y = 0, width = None, height = None, hidden = False):
        super().__init__(x = x, y = y, width = width, height = height, hidden = hidden)

        self.children = []
        # self.dirty_children = []

    def add(self, child):
        child.parent = self
        self.children.append(child)
        self.mark_dirty()
        self.register_dirty()
    def remove(self,child):
        child.parent = None
        self.children.remove(child)
        self.mark_dirty()
        self.register_dirty()


class Box(Container):
    def __init__(self, direction='h', spacing=0, align='start',
                 x = 0, y = 0, width = None, height = None, hidden = False):
        """
        初始化Box容器
        :param direction: 布局方向，'h'为水平，'v'为垂直
        :param spacing: 子元素间距
        :param align: 对齐方式，'start'/'center'/'end'
        :param default_color: 默认填充颜色，用于隐藏元素的区域
        """
        super().__init__(x = x, y = y, width = width, height = height, hidden = hidden)
        self.direction = direction
        self.spacing = spacing
        self.align = align
        # 存储子元素的原始尺寸设置
        self.children_size = []

    def add(self, child):
        """
        添加子元素并更新布局
        :param child: 要添加的子元素(可以是容器或widget)
        """
        super().add(child)
        # 记录子元素的原始尺寸设置
        self.children_size.append([child.width, child.height,child.width_resizable, child.height_resizable])
        self.update_layout()
    def remove(self, child):
        """
        移除子元素并更新布局
        :param child: 要移除的子元素
        """
        # 获取子元素在children中的索引
        if child in self.children:
            index = self.children.index(child)
            # 同步删除children_size中对应的记录
            self.children_size.pop(index)
            super().remove(child)
            self.update_layout()

    def _calculate_flexible_size(self, total_size, fixed_size_sum, flexible_count):
        """
        计算可伸缩元素的尺寸
        :param total_size: 总可用空间
        :param fixed_size_sum: 固定尺寸之和
        :param flexible_count: 可伸缩元素数量
        :return: 每个可伸缩元素应得的尺寸
        """
        if flexible_count == 0:
            return 0
        # 计算剩余空间
        remaining = total_size - fixed_size_sum - self.spacing * (len(self.children) - 1)
        # 平均分配给每个可伸缩元素
        return max(0, remaining // flexible_count)

    def update_layout(self):
        """
        更新容器的布局
        根据方向调用相应的布局函数
        """
        if self.direction == 'h':
            self._layout_horizontal()
        else:
            self._layout_vertical()


    def _layout_horizontal(self):
        """
        水平方向的布局处理
        处理None值的情况，计算并分配空间
        """
        x = self.x
        max_height = 0
        fixed_width_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定宽度和可伸缩元素数量
        for i, child in enumerate(self.children):
            width, height, width_resizable, height_resizable = self.children_size[i]
            if width is not None:
                fixed_width_sum += width
            else:
                flexible_count += 1

        # 计算可伸缩元素的宽度
        flexible_width = self._calculate_flexible_size(
            self.width, fixed_width_sum, flexible_count)

        # 第二遍遍历：设置实际布局
        for i, child in enumerate(self.children):
            width, height, _, _= self.children_size[i]
            # 确定实际使用的宽度
            actual_width = flexible_width if width is None else width
            # 确定实际使用的高度
            actual_height = self.height if height is None else height

            # 根据对齐方式计算y坐标
            if self.align == 'start':
                y = self.y
            elif self.align == 'center':
                y = self.y + (self.height - actual_height) // 2
            else:  # end
                y = self.y + self.height - actual_height

            # 应用布局
            child.layout(x, y, actual_width, actual_height)
            x += actual_width + self.spacing
            max_height = max(max_height, actual_height)

    def _layout_vertical(self):
        """
        垂直方向的布局处理
        处理None值的情况，计算并分配空间
        """
        y = self.y
        max_width = 0
        fixed_height_sum = 0
        flexible_count = 0

        # 第一遍遍历：计算固定高度和可伸缩元素数量
        for i, child in enumerate(self.children):
            width, height, width_resizable, height_resizable = self.children_size[i]
            if height is not None:
                fixed_height_sum += height
            else:
                flexible_count += 1

        # 计算可伸缩元素的高度
        flexible_height = self._calculate_flexible_size(
            self.height, fixed_height_sum, flexible_count)

        # 第二遍遍历：设置实际布局
        for i, child in enumerate(self.children):
            width, height, _, _ = self.children_size[i]
            # 确定实际使用的宽度
            actual_width = self.width if width is None else width
            # 确定实际使用的高度
            actual_height = flexible_height if height is None else height

            # 根据对齐方式计算x坐标
            if self.align == 'start':
                x = self.x
            elif self.align == 'center':
                x = self.x + (self.width - actual_width) // 2
            else:  # end
                x = self.x + self.width - actual_width

            # 应用布局
            child.layout(x, y, actual_width, actual_height)
            y += actual_height + self.spacing
            max_width = max(max_width, actual_width)

class Label(Widget):
    """
    标签控件类
    用于显示文本内容，支持自定义颜色、对齐方式等
    """
    
    # 文本对齐方式常量
    ALIGN_LEFT = 'left'
    ALIGN_CENTER = 'center'
    ALIGN_RIGHT = 'right'
    
    def __init__(self, 
                 text="",
                 font=None,  # 字体字典数据
                 text_color=0xf800,  # 文字颜色（默认红色）
                 background=0x7f34,  # 背景色（默认绿色）
                 align=ALIGN_LEFT,  # 文本对齐方式
                 padding=(2, 2, 2, 2),
                 x=0,y=0,width=None,height=None,hidden=False):  # 内边距 (左,上,右,下)
        """
        初始化标签控件
        
        参数:
            text: 显示的文本内容
            font: 字体数据对象，包含点阵信息
            text_color: 文字颜色（16位RGB颜色）
            background: 背景颜色（16位RGB颜色）
            align: 文本对齐方式
            padding: 内边距，格式为(左,上,右,下)
        """
        super().__init__(x = x, y = y, width = width, height = height, hidden = hidden)
        self.text = text
        self.font = font
        if font is not None:
            self.font_width = font['WIDTH']
            self.font_height = font['HEIGHT']
        self.text_color = text_color
        self.background = background
        self.align = align
        self.padding = padding
        # 测试label类能否正常生成bitmap的接口，可直接用driver flash到屏幕
        # self.cache = None



    
    def _create_bitmap(self):
        """
        创建控件的位图
        包含背景和文本渲染
        """
        
        # 创建新的位图
        bitmap = Bitmap(self.width, self.height)
        
        # 填充背景
        bitmap.fill_rect(0, 0, self.width, self.height, self.background)
        
        if self.text and self.font:
            # 计算文本总宽度
            text_width = len(self.text) * self.font["WIDTH"]
            
            # 根据对齐方式计算起始x坐标
            if self.align == self.ALIGN_LEFT:
                text_x = self.padding[0]
            elif self.align == self.ALIGN_CENTER:
                text_x = (self.width - text_width) // 2
            else:  # ALIGN_RIGHT
                text_x = self.width - text_width - self.padding[2]
            
            # 垂直居中
            text_y = (self.height - self.font["HEIGHT"]) // 2
            
            # 渲染每个字符
            for i, char in enumerate(self.text):
                if char in self.font:
                    char_bitmap = hex_font_to_bitmap(
                        self.font[char],self.font['WIDTH'],self.font['HEIGHT'],
                        foreground=self.text_color)
                else:
                    char_bitmap = hex_font_to_bitmap(
                        self.font["DEFAULT"],self.font['WIDTH'],self.font['HEIGHT'],
                        foreground=self.text_color)
                # 将字符位图复制到主位图
                x = text_x + i * self.font["WIDTH"]
                    
                bitmap.blit(char_bitmap, dx=x, dy=text_y)
        
        return bitmap
    
    def get_bitmap(self):
        """
        获取控件的位图
        如果需要重绘，先创建新的位图
        """
        if self._hidden:
            bitmap=Bitmap(self.width,self.height)
            bitmap.fill_rect(0,0,self.width,self.height,0xf18f)
            return bitmap 
        else:
            self._bitmap = self._create_bitmap()
            return self._bitmap           

    
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
        self.register_dirty()
    def set_align(self,align):
        """设置文本对齐"""
        self.align = align
        self.register_dirty()
    def set_padding(self,padding):
        """设置文本边距"""
        self.padding = padding
        self.register_dirty()

def timeit(func):
    def new_func(*args, **kwargs):
        t = time.ticks_ms()
        result = func(*args, **kwargs)
        diff=time.ticks_diff(time.ticks_ms(), t)
        print("\033[32m"+func.__name__+"\033[0m"+" "*(20-len(func.__name__))+" executed in"+" "*(10-len(str(diff)))+"\033[31m"+str(diff)+" ms"+"\033[0m")
        return result
    return new_func

class Display:
    def __init__(self, width, height, driver=None,threaded=True):
        self.width = width
        self.height = height
        self.root = None
        self.driver = driver
        self.threaded = threaded
        if threaded and driver is not None:
            import _thread
            self.dx = 0
            self.dy = 0
            self.bitmap = Bitmap(0,0)
            self.bitmap_lock=_thread.allocate_lock()
            self.thread = _thread.start_new_thread(lambda: driver.thread_refresh(bitmap=self.bitmap,
                                                                          x=self.dx, y=self.dy,
                                                                          lock=self.bitmap_lock),())
        
    def set_root(self, widget):
        self.root = widget
        self.root.layout(0, 0, self.width, self.height)
    
    @timeit
    def check_dirty(self):
        if self.root:

            def render_widget(widget):
                if widget._dirty:  # 只有脏组件才需要重新绘制
                    if hasattr(widget, 'get_bitmap'):
                        # self._bitmap.fill_rect(widget.x,widget.y,widget.width,widget.height,color=0xffff)
                        # self._bitmap.blit(bitmap, dx=widget.x, dy=widget.y)
                        if self.threaded:
                            self.bitmap_lock.acquire()
                            try:
                                bitmap = widget.get_bitmap()
                                self.dx= widget.x
                                self.dy= widget.y
                            finally:self.bitmap_lock.release()
                        else:
                            bitmap = widget.get_bitmap()
                            self.driver.refresh(bitmap,x=widget.x,y=widget.y)
                    widget._dirty = False  # 绘制完成后清除脏标记

                for child in widget.children:
                    render_widget(child)  # 递归处理子组件
                    
            render_widget(self.root)
            
            # Here you would add display hardware update logic
            # self.driver.refresh(self._bitmap)
    def run(self):
        while True:
            self.check_dirty()

FontData={}










# 初始化 SPI 接口
spi = machine.SPI(1, baudrate=80000000, phase=1, polarity=1, sck=machine.Pin(41), mosi=machine.Pin(40))#, miso=machine.Pin(6))
print("SPI 初始化成功")
# 初始化 ST7789 显示屏
driver = ST7789(spi, 240, 240,
    reset=machine.Pin(39, machine.Pin.OUT),
    dc  = machine.Pin(38, machine.Pin.OUT))
print("ST7789 显示屏初始化")
# 初始化显示屏
driver.init()
print('显示屏初始化完成')



bitmap = font_utils.hex_font_to_bitmap(font_16x16.FontData['?'],font_16x16.FontData['WIDTH'],font_16x16.FontData['HEIGHT'])
driver.refresh(bitmap,200,200)


print('test driver ...')
# time.sleep(2)

"""演示标签和按钮的使用"""

# 创建显示器
display = Display(240, 240,driver=driver,threaded=False)
# 创建垂直布局容器
main_box = Box(direction='h')
box1 = Box(direction='v',width=200)
box2 = Box(direction='h')
# # 设置根控件并刷新
display.set_root(main_box)
# 创建标签
label1 = Label(
    text="ABCd",
    text_color=0x0000,
    font=font_16x16.FontData,
    align=Label.ALIGN_CENTER,
    background=0xcdb0
)

label2 = Label(
    text="test",
    font=font_16x16.FontData,
    align=Label.ALIGN_CENTER
    # background=0xffc0
)
label3 = Label(
    text="123",
    font=font_16x16.FontData,
    background=0x0099,
)
label4 = Label(
    text="456",
    font=font_16x16.FontData,
    align=Label.ALIGN_RIGHT,
    width=30,
    background=0x1040,
)

main_box.add(label1)
main_box.add(box1)
box1.add(label2)
box1.add(box2)
box2.add(label3)
box2.add(label4)
display.check_dirty()

time.sleep(1)

while True:
    if box1 in main_box.children:
        main_box.remove(box1)
    else:
        main_box.add(box1)
    display.check_dirty()
