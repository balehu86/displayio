# displayio 项目介绍
完全使用micropython完成，不依赖任何非官方库。

现在widget组件只支持label(标签)、button(按钮)，暂时没有增加其他组件的计划(新增组件不难，现在还在完成系统验证阶段，等完成动画功能再添加比如进度条等等新widget)

驱动程序目前也只支持st7789，原因如上所述(业余玩家，我手头上只有esp32s3 和 st7789 240*240)

此库的语法使用类似于 [Beeware Toga](https://github.com/beeware/toga.git) 项目。同时参考了部分kivy项目和css特性。

## 计划
- [ ] 将bitmap.py模块重写为C模块，用以提升大量性能
- [ ] 完善帧率的计算方法，当前采用动态刷新(只有需要刷新的时候才刷新屏幕)
- [ ] 统一方法和变量的命名风格
- [ ] 完成动画效果
- [ ] 添加更多的显示部件
- [ ] 添加更多的输入输出驱动
- [ ] 完善文档和说明
- [ ] 优化性能

### 支持的输入输出设备
* st7789显示 (仅240*240受测试)
* 旋转编码器
* 开关或按钮
* esp32芯片自带的触摸引脚TouchPad

### 支持的MCU
* ESP32 S3

### 支持的布局容器
* flex (弹性布局，分x方向和y方向两种，在某一方向容器尺寸确认后，子元素会平分弹性容器的尺寸)
* free (自由布局，可以在容器内任意位置放置子元素)
* grid (网格布局，类似于excel表格，一个格子一个坑，一个子元素可以占用多个坑，达到**合并网格**的效果)
* scroll (滚动窗口容器，最特殊的一个容器，此容器也是一个**可显示的元素(能被绘制并显示到屏幕上的元素)**，实现窗口滚动的效果用来显示远大于容器尺寸的显示区域)

the display is dynamical, so the show_fps is not correct.
you can specify the fps in init of display.

┌ └ ┐ ┘ ─ │ ├ ┤ ┬ ┴ ┼

# 项目文件介绍
```
displayio/┐
          ├ __init__.py  # None
          │
          ├ container/┐ # 放置布局用的容器类
          │           ├ __init__.py   # None
          │           ├ container.py  # 容器基类
          │           ├ flex_box.py   # 弹性布局
          │           ├ free_box.py   # 自由布局
          │           ├ grid_box.py   # 网格布局
          │           └ scroll_box.py # 滚动窗口
          │
          ├ core/┐ # 放置核心组件
          │      ├ __init__.py    # None
          │      ├ base_widget.py # 容器和可显示元素的基类
          │      ├ bitmap.py      # 包装了官方FrameBuffer类，并赋予了新功能
          │      ├ dirty.py       # 脏区域管理系统
          │      ├ event.py       # 定义了事件Evnet类和事件类型枚举类EventType
          │      ├ logging.py     # 测试用的模块的日志打印模块
          │      │                  简化自micropython_lib/logging.py
          │      └ style.py       # 定义了常用的颜色、布局样式、背景类
          │
          ├ input/┐ # 输入设备类
          │       ├ __init__.py    # None
          │       ├ base_input.py  # 输入设备的基本抽象类
          │       ├ encoder.py     # 旋转编码器类
          │       ├ switch.py      # 按钮或开关类
          │       └ touchpin.py    # esp32系列的TouchPad
          │
          ├ utils/┐ # 放置一些小工具函数
          │       ├ __init__.py   # None
          │       ├ decorator.py  # 一些可能有用的装饰器
          │       └ font_utils.py # 将字体点图二进制数据转换成bitmap实例，
          │                         在需要显示文字的元素中使用
          │
          ├ widget/┐ # 可显示元素类
          │        ├ __init__.py # None
          │        ├ button.py   # 按钮类
          │        ├ label.py    # 标签类
          │        └ widget.py   # 可显示元素的基类
          │
          └ display.py # 定义了显示程序的主体和主循环，
                         为显示程序的入口
```
# create your own widget
1. you need to import the base widget file  
   `import displayio.widget.widget`
2. rewrite the func called `widget.draw`, you can find the example in label.py or button.py
3. the `widget.draw` is aim to draw `widget._bitmap` and wait for render system to blit it to screen or gloable `root._bitmap`

