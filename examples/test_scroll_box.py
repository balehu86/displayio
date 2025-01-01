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
                  fps = 30,
                  show_fps = False,
                  partly_refresh = True
)
# 创建垂直布局容器
main_box = ScrollBox()
box1 = FlexBox(direction=Style.VERTICAL,width=240,height=400,spacing = 10)

# # 设置根控件并刷新
display.set_root(main_box)
# 创建标签

button1 = Button(
    text = 'butttt11',
    width = 120,
    font = font,
    font_scale = 1,
    align=Label.ALIGN_RIGHT
)
button2 = Button(
    text = 'butttt22',
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
box1.add(button1,button2,button)
# for w in range(3):
#     box1.add(Label(text=str(w)*5,
#                         height=15,
#                         font=font,
#                         background_color=random.getrandbits(16)))
    
touch1=TouchPin(4,target_widget=button1)
# touch2=TouchPin(13,target_widget=button2)
encoder = RotaryEncoder(pin_a=6, pin_b=7,strict=False,target_widget=main_box)
display.add_input_device(touch1,encoder)
main_box.add(box1)

def click_callback(widget,event):
    print('clicked!')
#     if label2 in hbox.children:
#         hbox.remove(label2)
#     else:
#         hbox.add(label2)
def double_click_callback(widget,event):
#     if button.state==2:
#         button.set_enabled(True)
#     else:
#         button.set_enabled(False)
    print('double click!')
def long_press_callback(widget,event):
    print('long press!')
#     if label3.visibility:
#         label3.hide()
#     else:
#         label3.unhide()
def long_press_release_callback(widget,event):
    print('long press released!')
def release_callback(widget,event):
    print('release!')
def press_callback(widget,event):
    print('press!')


button1.bind(EventType.PRESS, press_callback)
button1.bind(EventType.CLICK, click_callback)
button1.bind(EventType.DOUBLE_CLICK, double_click_callback)
button1.bind(EventType.LONG_PRESS, long_press_callback)
button1.bind(EventType.RELEASE, release_callback)
button1.bind(EventType.LONG_PRESS_RELEASE, long_press_release_callback)

def main():
    pass

display.run(main)