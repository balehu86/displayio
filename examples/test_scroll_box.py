# core and decorator
from displayio.core.event import EventType, Event
from displayio.core.style import Style, Color
from displayio.display import Display

# widgets
from displayio.container.scroll_box import ScrollBox
from displayio.container.flex_box import FlexBox
from displayio.widget.label import Label
from displayio.widget.button import Button

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
touch=TouchPin(12,target_position=[239,239])
# 创建显示器
display = Display(240, 240,output=output,inputs=[touch],
                  threaded=False,
                  fps = 30,
                  show_fps = True,
                  partly_refresh = True
)
# 创建垂直布局容器
main_box = ScrollBox()
box1 = FlexBox(direction=Style.VERTICAL,width=300,spacing = 10)

# # 设置根控件并刷新
display.set_root(main_box)
# 创建标签
label1 = Label(
    text="l1",
    text_color=0x0001,
    font=font,
    font_scale =2,
    align=Label.ALIGN_CENTER,
    background_color=0xcdb0,
    height=40
#     width=40
)

label2 = Label(
    text="l2",
    font=font,
    align=Label.ALIGN_CENTER,
    # background_color=0xffc0
)
label3 = Label(
    text="l3",
    font=font,
    background_color=0x0099,
    rel_x=20,
    rel_y=20
)
label4 = Label(
    text="l4",
    font=font,
    align=Label.ALIGN_RIGHT,
    width=40,
    background_color=0x0000,
)

button = Button(
    text = 'but',
    font = font,
    font_scale = 1,
    align=Label.ALIGN_LEFT
)

main_box.add(box1)
box1.add(label1)
box1.add(label2)
box1.add(button)
box1.add(label3)
box1.add(label4)

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
def long_press_release_callback(event):
    print('long press released!')

def release_callback(event):
    print('release!')
button.bind(EventType.CLICK, click_callback)
button.bind(EventType.DOUBLE_CLICK, double_click_callback)
button.bind(EventType.LONG_PRESS, long_press_callback)
button.bind(EventType.RELEASE, release_callback)
button.bind(EventType.LONG_PRESS_RELEASE, long_press_release_callback)

def main():
#     check_touch()
    pass

display.run(main)