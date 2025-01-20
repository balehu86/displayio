from ..core.base_widget import BaseWidget
from ..core.bitmap import Bitmap

class Widget(BaseWidget):
    """
    控件基类
    """
    __slots__ = ('_empty_bitmap',)

    def __init__(self,
                 abs_x=None, abs_y=None,
                 rel_x=0,rel_y=0, dz=0,
                 width=None,height=None,
                 visibility=True, state=BaseWidget.STATE_DEFAULT,
                 transparent_color=BaseWidget.PINK,
                 background=BaseWidget.WHITE,
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
                         transparent_color = transparent_color,
                         background = background,
                         color_format = color_format)

        self._bitmap = Bitmap(self, transparent_color = transparent_color)
        self._empty_bitmap = Bitmap(self, transparent_color = transparent_color)

    def draw(self):
        """创建控件的位图"""
        raise NotImplementedError("BaseWidget子类必须实现 _create_bitmap方法")

    def get_bitmap(self):
        # 返回bitmap
        if self.visibility:
            return self._bitmap
        else:
            self._empty_bitmap.init(dx=self.dx,dy=self.dy,color=0xffff)
            return self._empty_bitmap

    @property
    def get_background_color(self):
        if self.state == self.STATE_FOCUSED:
            return self._darken_color(self.background.color, 0.9)
        if self.state == self.STATE_DISABLED:
            return BaseWidget.GREY
        return self.background.color