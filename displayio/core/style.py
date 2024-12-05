# ./core/style.py

class Style:
    RED   = 0xf800
    GREEN = 0x07e0
    BLUE  = 0x001f
    PINK  = 0xf81f
    WHITE = 0xffff
    def __init__(self, abs_x = None, abs_y = None,
                 rel_x = None, rel_y = None,
                 width = None, height = None,
                 visibility = True, enabled = True,
                 background_color = 0xffff,
                 transparent_color = PINK):
        pass