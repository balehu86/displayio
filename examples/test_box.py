# core and decorator
from displayio.core.event import EventType, Event
from displayio.display import Display

# widgets
from displayio.container.flex_box import FlexBox
from displayio.container.free_box import FreeBox
from displayio.widget.label import Label
from displayio.widget.button import Button

# font utils
from displayio.utils import font_utils
import btree # type: ignore
f = open("/displayio/utils/font_16x16.db", "r+b")
font=btree.open(f)


# output
from displayio.output.st7789 import ST7789
from displayio.input.touchpin import TouchPin

import time
import machine # type: ignore

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
touchs=TouchPin(12,target_position=[140,60])
# 创建显示器
display = Display(240, 240,output=output,inputs=[touchs],
                  threaded=False,
                  fps = 30,
                  show_fps = False
)
# 创建垂直布局容器
main_box = FlexBox(direction='h')

vbox = FlexBox(direction='v',width=120,spacing = 10)
main_box.add(vbox)

hbox = FlexBox(direction='h',spacing = 10,reverse = True)
vbox.add(hbox)

fbox = FreeBox(height= 90)
main_box.add(fbox)

vbox_in_f=FlexBox(direction='v',rel_x = 10, rel_y = 20, align='center')
fbox.add(vbox_in_f)

# # 设置根控件并刷新
display.set_root(main_box)
# 创建标签
label1 = Label(
    text="1",
    text_color=0x0001,
    font=font,
    align=Label.ALIGN_CENTER,
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
    background_color=0x0099,
    rel_x=20,
    rel_y=20
)
label4 = Label(
    text="4",
    font=font,
    align=Label.ALIGN_RIGHT,
    width=40,
    background_color=0x0000,
)

button = Button(
    text = 'b',
    font = font,
)

hbox.add(label1)
hbox.add(label2)
vbox.add(label3)
vbox_in_f.add(label4)
vbox_in_f.add(button)

def click_callback(event):
    print('clicked!')
    
#     if box1 in main_box.children:
#         label1.set_text('in')
#         main_box.remove(box1)
#     else:
#         label1.set_text('#')
#         main_box.add(box1)
def double_click_callback(event):
#     if button.state==2:
#         button.set_enabled(True)
#     else:
#         button.set_enabled(False)
    print('double click!')
def long_press_callback(event):
    print('long press!')
    
#     if label3.visibility:
#         label3.hide()
#     else:
#         label3.unhide()

def release_callback(event):
    print('release!')
button.bind(EventType.CLICK, click_callback)
button.bind(EventType.DOUBLE_CLICK, double_click_callback)
button.bind(EventType.LONG_PRESS, long_press_callback)
button.bind(EventType.RELEASE, release_callback)


def main():
    pass

display.run(main)