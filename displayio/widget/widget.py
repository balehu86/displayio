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
                 background_color=BaseWidget.Label_GREEN, # 背景色（默认绿色）
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
                         background_color = background_color,
                         transparent_color = transparent_color,
                         color_format = color_format)
        
        self._bitmap = Bitmap(self)
        self._empty_bitmap = Bitmap(self)

    def get_bitmap(self):
        pass
