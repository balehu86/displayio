from .widget import Widget

class Char(Widget):
    """
    字符控件类
    用于显示单个字符，支持自定义颜色、对齐方式等
    """
    __slots__ = ('font', 'font_scale', 'font_width', 'font_height', 'font_default', 'font_rle',
                 'text','text_width','text_height', 'text_color',
                 'align', 'padding','_text_bitmap')

    def __init__(self, 
                 text="",
                 font=None,  # 字体字典数据
                 font_scale=1, # 字体放大系数
                 text_color=Widget.RED,  # 文字颜色（默认红色）
                 align=Widget.ALIGN_LEFT,  # 文本对齐方式
                 padding=(2, 2, 2, 2),  # 文字边距,(左,上,右,下)
    ):
        self.text = text
        self.font = font

    def draw(self):
        pass