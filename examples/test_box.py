# core and decorator
from displayio.core.event import EventType, Event
from displayio.core.style import Style, Color
from displayio.display import Display

# widgets
from displayio.container.flex_box import FlexBox
from displayio.container.free_box import FreeBox
from displayio.container.scroll_box import ScrollBox
from displayio.widget.label import Label
from displayio.widget.button import Button

# font utils
import btree # type: ignore
f = open("/font_16x16.db", "r+b")
font=btree.open(f)


# output
from displayio.output.st7789 import ST7789
from displayio.input.touchpin import TouchPin
from displayio.input.encoder import RotaryEncoder

import time
import machine # type: ignore
import random

# init SPI 接口
spi = machine.SPI(1, baudrate=80000000, phase=1, polarity=1,\
                  sck=machine.Pin(41), mosi=machine.Pin(40))
print("SPI 初始化成功")
# 初始化 ST7789 显示屏
output = ST7789(spi,
                reset = machine.Pin(39, machine.Pin.OUT),
                dc = machine.Pin(38, machine.Pin.OUT))
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
                  fps = 15,
                  show_fps = False,
                  partly_refresh = False
)
# 创建垂直布局容器
main_box = FlexBox(direction=Style.HORIZONTAL)

vbox = FlexBox(direction=Style.VERTICAL,width=120,spacing = 10)
main_box.add(vbox)

fbox = FreeBox()
main_box.add(fbox)

vbox_in_f=FlexBox(direction=Style.VERTICAL,rel_x = 10, rel_y = 20, align=Style.ALIGN_CENTER,height= 220)
fbox.add(vbox_in_f)

sbox=ScrollBox(background_color=0xffff)
vbox.add(sbox)

hbox = FlexBox(direction=Style.HORIZONTAL,spacing = 10,reverse = True,height=115,width=120)
vbox.add(hbox)

vbox_in_s=FlexBox(direction=Style.VERTICAL,width=110,
                    height=300,
                  spacing = 10)
sbox.add(vbox_in_s)
# vbox_in_s.visibility=True
# vbox_in_s.background_color = 0x4480

# sbox.visibility=False

# # 设置根控件并刷新
display.set_root(main_box)
# 创建标签
label1 = Label(
    text="1",
    text_color=0x0001,
    font=font,
    align=Label.ALIGN_TOP,
    background_color=0xcdb0,
#     width=40
)

label2 = Label(
    text="2",
    font=font,
    align=Label.ALIGN_CENTER,
#     width = 150,
#     height = 30,
    rel_x = 20,
    rel_y = 10
    # background=0xffc0
)
label3 = Label(
    text="3",
    font=font,
    font_scale = 3,
    background_color=0x0099,
    rel_x=20,
    rel_y=20
)
label4 = Label(
    text="4",
    font=font,
    font_scale = 3,
    align=Label.ALIGN_CENTER,
    width=40,
    background_color=0x4480,
)

label5 = Label(
    text="5",
    font=font,
    align=Label.ALIGN_CENTER,
    width = 50,
#     height = 30,
    rel_x = 60,
    rel_y = 10
    # background=0xffc0
)
button1 = Button(
    text = 'b1',
    font = font,
    font_scale = 2,
)
button2 = Button(
    text = 'b2',
    font = font,
    font_scale = 2,
)
hbox.add(label1, label2)

vbox_in_f.add(button1,label3, label4, button2)
fbox.add(label5)

for w in range(10):
    vbox_in_s.add(Button(text=str(w)*5,
                        height=10,
                        font=font,
                        background_color=random.getrandbits(16)))
# 添加输入设备   
touch=TouchPin(13,target_widget=vbox_in_s.children[0])
encoder = RotaryEncoder(pin_a=5, pin_b=6,strict=False,target_widget=sbox)
display.add_input_device(touch,encoder)

def click_callback(widget,event):
    print('clicked!')
    if label2 in hbox.children:
        hbox.remove(label2)
    else:
        hbox.add(label2)
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
    
# button1.bind(EventType.PRESS, press_callback)
vbox_in_s.children[0].bind(EventType.CLICK, click_callback)
# button1.bind(EventType.DOUBLE_CLICK, double_click_callback)
# button1.bind(EventType.LONG_PRESS, long_press_callback)
# button1.bind(EventType.RELEASE, release_callback)
# button1.bind(EventType.LONG_PRESS_RELEASE, long_press_release_callback)


def main():
    pass

display.run(main)