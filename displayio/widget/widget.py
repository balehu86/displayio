from ..core.base_widget import BaseWidget
from ..core.bitmap import Bitmap

class Widget(BaseWidget):
    """
    控件基类
    """
    __slots__ = ()
    
    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=0,rel_y=0, dz=0,
                 width=None,height=None,
                 visibility=True, state=BaseWidget.STATE_DEFAULT,
                 default_color=BaseWidget.WHITE,
                 transparent_color=BaseWidget.PINK,
                 color_format = BaseWidget.RGB565):
        """
        初始化控件基类
        
        继承BaseWidget所有参数,额外添加:
            pass
        """
        super().__init__(abs_x = abs_x, abs_y = abs_y,
                         rel_x = rel_x, rel_y = rel_y, dz = dz,
                         width = width, height = height,
                         visibility = visibility, state = state,
                         default_color = default_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        
        self._bitmap = Bitmap(self, transparent_color = transparent_color)
        self._bond_bitmap = Bitmap(self, transparent_color = transparent_color)
        self._empty_bitmap = Bitmap(self, transparent_color = transparent_color)

    def _create_bitmap(self):
        pass
        """
        创建控件的位图
        """

        """先这里绘制self._bitmap, 然后根据self.dx_cache, self.dy_cache, self.width_cache, self.height_cache决定是否返回中间bitmap"""
        
        
        if not self.layout_changed: # 如果布局未改变则直接返回self._bitmap
            return self._bitmap
        # 计算当前的dx, dy, width, height
        current_dx, current_dy, current_width, current_height = self.dx, self.dy, self.width, self.height
        # 计算原始的dx, dy, width, height
        original_dx = self.dx_cache if self.dx_cache is not None else current_dx
        original_dy = self.dy_cache if self.dy_cache is not None else current_dy
        original_width = self.width_cache if self.width_cache is not None else current_width
        original_height = self.height_cache if self.height_cache is not None else current_height
        # 计算包围盒bitmap的起始左上角坐标
        bitmap_min_x = min(original_dx, current_dx)
        bitmap_min_y = min(original_dy, current_dy)
        # 计算原始位置的边界坐标
        original_x_max, original_y_max = original_dx + original_width - 1, original_dy + original_height - 1
        # 计算当前位置的边界坐标
        current_x_max, current_y_max = current_dx + current_width - 1, current_dy + current_height - 1
        # 计算包围盒bitmap的宽高
        bitmap_width = max(original_x_max, current_x_max) - bitmap_min_x +1
        bitmap_height = max(original_y_max, current_y_max) - bitmap_min_y + 1
        # 创建包围盒bitmap
        self._bond_bitmap.init(dx=bitmap_min_x, dy=bitmap_min_y, width=bitmap_width, height=bitmap_height, transparent_color=0x0000)
        # 将当前self._bitmap复制到包围盒bitmap
        self._bond_bitmap.blit(self._bitmap, dx=current_dx-bitmap_min_x, dy=current_dy-bitmap_min_y)
        # 恢复缓存的原始dx, dy, width, height
        self.dx_cache, self.dy_cache, self.width_cache, self.height_cache = None, None, None, None
        self.layout_changed = False
        # 返回包围盒bitmap
        return self._bond_bitmap
    
    def get_bitmap(self):
        if self.visibility:
            bitmap = self._bitmap
            if self._dirty:
                bitmap = self._create_bitmap()
                self._dirty = False
            return bitmap
        else:
            self._empty_bitmap.init(dx=self.dx,dy=self.dy,color=0xffff)
            return self._empty_bitmap