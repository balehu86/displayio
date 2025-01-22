import framebuf
from framebuf import FrameBuffer as fb
# Mock widget class for testing
class Widget:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.color_format = framebuf.RGB565
def test():
    print('测试init')
    a=fb(widget=Widget(1,1))
    a.init(dx=10,dy=0,color=0xffff)
    assert a.buffer() == b'\xff\xff','buffer异常'

    print('测试color')
    print('测试blit')
    
    
test()
