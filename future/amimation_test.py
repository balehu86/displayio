# 1. 淡入效果
label = Label("Hello")
fade_in = FadeAnimation(label, start_alpha=0, end_alpha=1, duration=1000)
label.add_animation(fade_in)

# 2. 滑动效果
button = Button("Click Me")
slide_in = SlideAnimation(
    button,
    start_pos=(-100, 50),  # 从屏幕左侧滑入
    end_pos=(70, 50),      # 最终位置
    duration=800
)
button.add_animation(slide_in)

# 3. 缩放效果
icon = Label("☆")
scale_up = ScaleAnimation(
    icon,
    start_scale=0.1,
    end_scale=1.0,
    duration=500
)
icon.add_animation(scale_up)

# 4. 组合动画
def on_button_click(button):
    # 点击按钮时播放动画
    fade_out = FadeAnimation(button, start_alpha=1, end_alpha=0, duration=300)
    slide_out = SlideAnimation(
        button,
        start_pos=(button.x, button.y),
        end_pos=(display.width, button.y),
        duration=300
    )
    button.add_animation(fade_out)
    button.add_animation(slide_out)

# 5. 循环更新显示
while True:
    display.refresh()  # 这会更新所有动画并刷新屏幕
    time.sleep_ms(16) # 大约60fps的刷新率