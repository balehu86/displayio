import gc
gc.collect()
# core and decorator
from displayio.core.event import EventType, Event
from displayio.core.style import Style, Color
from displayio.display import Display

# widgets
from displayio.container.scroll_box import ScrollBox
from displayio.container.flex_box import FlexBox
from displayio.container.free_box import FreeBox
from displayio.widget.label import Label
from displayio.widget.button import Button

# font utils
import btree # type: ignore
f = open("/font_16x16.db", "r+b")
font=btree.open(f)


# driver
from displayio.output.st7789 import ST7789
from displayio.input.touchpin import TouchPin
from displayio.input.encoder import RotaryEncoder

import time
import machine # type: ignore
import random

# init SPI 接口
spi = machine.SPI(1, baudrate=80000000, phase=1, polarity=1, sck=machine.Pin(41), mosi=machine.Pin(40))#, miso=machine.Pin(6))
print("SPI 初始化成功")
# 初始化 ST7789 显示屏
output = ST7789(spi,
                reset = machine.Pin(39, machine.Pin.OUT),
                dc = machine.Pin(38, machine.Pin.OUT),)
print("ST7789 显示屏初始化")
# 初始化显示屏
output.init()
print('显示屏初始化完成')

# 测试驱动的颜色显示
# 红色
output.fill_rect(0,0,80,240,0xf800)
# 绿色
output.fill_rect(80,0,80,240,0x07e0)
# 蓝色
output.fill_rect(160,0,80,240,0x001f)
time.sleep(1)

"""演示标签和按钮的使用"""
# 创建显示器
display = Display(240, 240,output=output,
                  threaded=False,
                  fps = 30,
                  show_fps = False,
                  partly_refresh = False
)
# 创建垂直布局容器
main_box = FreeBox()
sbox = ScrollBox(width=100,height=100)
box1 = FlexBox(direction=Style.VERTICAL,width=300,height=300,spacing = 10)

# # 设置根控件并刷新
display.set_root(main_box)
# 创建标签

button1 = Button(
    text = 'butttt',
    font = font,
    font_scale = 1,
    align=Label.ALIGN_RIGHT
)
button2 = Button(
    text = 'butttt',
    font = font,
    font_scale = 1,
    align=Label.ALIGN_RIGHT
)
button = Button(
    abs_x = 150,
    width = 100,
    text = 'but',
    font = font,
    font_scale = 1,
    align=Label.ALIGN_LEFT
)
box1.add(button1,button2)
for w in range(10):
    box1.add(Label(text=str(w)*5,
                        height=15,
                        font=font,
                        background_color=random.getrandbits(16)))
    
touch1=TouchPin(12,target_widget=button)
touch2=TouchPin(13,target_widget=button2)
encoder = RotaryEncoder(pin_a=6, pin_b=5,strict=False,target_widget=sbox)
display.add_input_device(touch1,touch2,encoder)

main_box.add(sbox)
sbox.add(box1)
main_box.add(button)

def click_callback1(event):
    print('1 clicked!')

def click_callback2(event):
    print('2 clicked!')
def click(e):
    print('clicked!')
def press(e):
    print('pres')

button1.bind(EventType.CLICK, click_callback1)
button2.bind(EventType.CLICK, click_callback2)
button.bind(EventType.CLICK, click)

def main():
    pass

display.run(main)