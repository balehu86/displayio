# ./widget/bar.py

from ..displayio.core.widget import Widget
from ..displayio.core.bitmap import Bitmap

from ..displayio.utils.font_utils import hex_font_to_bitmap
from ..displayio.utils.decorator import timeit

class Bar(Widget):
    def __init__(self, 
                 max = 99,
                 value = 0,
                 background = 0xffff,
                 padding = (2, 2, 2, 2),
                 x=0, y=0, width=None, height=None, hidden=False):
        super().__init__(x, y, width, height, hidden)

        # 进度条表示的最大值
        self.max = max
        # 进度条的值
        self._value = value
        # 背景色
        self.background=background
        # 侧边边距
        self.padding = padding        

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._value != new_value:
            self._value = new_value
            self.register_dirty()

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
                        self.font[char], self.font['WIDTH'], self.font['HEIGHT'],
                        foreground=self.text_color, rle=self.font['rle'])
                else:
                    char_bitmap = hex_font_to_bitmap(
                        self.font["DEFAULT"], self.font['WIDTH'], self.font['HEIGHT'],
                        foreground=self.text_color, rle=self.font['rle'])
                # 将字符位图复制到主位图
                x = text_x + i * self.font["WIDTH"]
                    
                bitmap.blit(char_bitmap, dx=x, dy=text_y)
        
        return bitmap
    
    @timeit
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