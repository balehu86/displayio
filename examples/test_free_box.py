# core and decorator
from displayio.core.event import EventType, Event
from displayio.core.style import Style, Color
from displayio.display import  Display

# widgets
from displayio.container.free_box import FreeBox
from displayio.widget.label import Label
# from displayio.widget.button import Button

# font utils
import btree # type: ignore
f = open("/font_16x16.db", "r+b")
font=btree.open(f)

# driver
from displayio.output.st7789 import ST7789
from displayio.input.touchpin import TouchPin

import time
import machine # type: ignore


# init SPI 接口
spi = machine.SPI(1, baudrate=80000000, phase=1, polarity=1, sck=machine.Pin(41), mosi=machine.Pin(40))#, miso=machine.Pin(6))
print("SPI 初始化成功")
# 初始化 ST7789 显示屏
output = ST7789(spi,
                reset = machine.Pin(39, machine.Pin.OUT),
                dc = machine.Pin(38, machine.Pin.OUT),
                )
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
output.fill(0)

"""演示标签和按钮的使用"""
touchs=TouchPin(12,target_position=[0,0])
# 创建显示器
display = Display(240, 240,output=output,inputs=[touchs],
                  fps = 30,
                  show_fps = False
)
# 创建垂直布局容器
main_box = FreeBox()

box1 = FreeBox(abs_y = 100,)
main_box.add(box1)

# 设置根控件并刷新
display.set_root(main_box)

# 创建标签
label1 = Label(
    text="label1 in",
    text_color=0x0001,
    font=font,
    align=Label.ALIGN_LEFT,
    background_color=0xcdb0,

    abs_y = 200,
    width = 170,
    height = 20,
)
main_box.add(label1)

label2 = Label(
    text="label2",
    font=font,
    align=Label.ALIGN_CENTER,
    # background_color=0xffc0
    rel_x = 50,
    rel_y = 50,
    width = 100,
    height = 20,
)
box1.add(label2)

label3 = Label(
    text="label3",
    font=font,
    background_color=0x0099,
    abs_x = 120,
    abs_y = 20,
    width = 100,
    height = 20,
)
main_box.add(label3)

label4 = Label(
    text="label4",
    font=font,
    align=Label.ALIGN_RIGHT,
    abs_x = 100,
    abs_y = 100,
    width = 120,
    height = 40,
    background_color=0x0000,
)
box1.add(label4)


def click_callback(event):
    print('clicked!')
#     if box1 in main_box.children:
#         label1.set_text('in')
#         main_box.remove(box1)
#     else:
#         label1.set_text('#')
#         main_box.add(box1)
        
    if label1.text == 'label1 in':
        label1.set_text('label1 out')
    else:
        label1.set_text('label1 in')

    if label3.visibility:
        label3.hide()
    else:
        label3.unhide()

label1.bind(EventType.CLICK, click_callback)

def main():

    pass

display.run(main)
