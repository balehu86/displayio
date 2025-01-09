# animation.py
import time
import math

class Animation:
    def __init__(self, duration=1000, easing='linear'):
        self.duration = duration  # 动画持续时间(ms)
        self.start_time = None
        self.is_running = False
        self.easing = easing
        
    def start(self):
        self.start_time = time.ticks_ms()
        self.is_running = True
        self.on_start()
        
    def stop(self):
        self.is_running = False
        self.on_stop()
        
    def get_progress(self):
        if not self.is_running:
            return 1.0
        elapsed = time.ticks_diff(time.ticks_ms(), self.start_time)
        progress = min(1.0, elapsed / self.duration)
        
        if progress >= 1.0:
            self.stop()
            
        return self._apply_easing(progress)
    
    def _apply_easing(self, progress):
        if self.easing == 'linear':
            return progress
        elif self.easing == 'ease-in':
            return progress * progress
        elif self.easing == 'ease-out':
            return 1 - (1 - progress) * (1 - progress)
        elif self.easing == 'ease-in-out':
            if progress < 0.5:
                return 2 * progress * progress
            else:
                return 1 - math.pow(-2 * progress + 2, 2) / 2
        return progress
    
    def on_start(self):
        pass
        
    def on_stop(self):
        pass
        
class FadeAnimation(Animation):
    def __init__(self, widget, start_alpha=0, end_alpha=1, duration=500):
        super().__init__(duration)
        self.widget = widget
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
        
    def update(self):
        if not self.is_running:
            return
            
        progress = self.get_progress()
        current_alpha = self.start_alpha + (self.end_alpha - self.start_alpha) * progress
        self.widget.set_alpha(current_alpha)
        self.widget.mark_dirty()

class SlideAnimation(Animation):
    def __init__(self, widget, start_pos, end_pos, duration=500):
        super().__init__(duration)
        self.widget = widget
        self.start_x, self.start_y = start_pos
        self.end_x, self.end_y = end_pos
        
    def update(self):
        if not self.is_running:
            return
            
        progress = self.get_progress()
        current_x = self.start_x + (self.end_x - self.start_x) * progress
        current_y = self.start_y + (self.end_y - self.start_y) * progress
        self.widget.move_to(int(current_x), int(current_y))
        self.widget.mark_dirty()

class ScaleAnimation(Animation):
    def __init__(self, widget, start_scale=0.5, end_scale=1.0, duration=500):
        super().__init__(duration)
        self.widget = widget
        self.start_scale = start_scale
        self.end_scale = end_scale
        
    def update(self):
        if not self.is_running:
            return
            
        progress = self.get_progress()
        current_scale = self.start_scale + (self.end_scale - self.start_scale) * progress
        self.widget.set_scale(current_scale)
        self.widget.mark_dirty()

# 修改 Widget 类以支持动画
class Widget:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.parent = None
        self.children = []
        self.dirty = True
        self.alpha = 1.0
        self.scale = 1.0
        self.animations = []
        
    def add_animation(self, animation):
        self.animations.append(animation)
        animation.start()
        
    def update_animations(self):
        """更新所有动画"""
        still_running = []
        for anim in self.animations:
            if anim.is_running:
                anim.update()
                still_running.append(anim)
        self.animations = still_running
        
        # 递归更新子部件的动画
        for child in self.children:
            child.update_animations()
    
    def set_alpha(self, alpha):
        self.alpha = max(0.0, min(1.0, alpha))
        
    def set_scale(self, scale):
        self.scale = max(0.1, scale)
        
    def move_to(self, x, y):
        self.x = x
        self.y = y

# 修改 Bitmap 类以支持 alpha 和 scale
class Bitmap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buffer = bytearray(width * height * 2)
        
    def blend_pixel(self, x, y, color, alpha):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
            
        if alpha >= 1.0:
            self.pixel(x, y, color)
            return
            
        if alpha <= 0.0:
            return
            
        current = self.pixel(x, y)
        
        # 解析当前颜色和新颜色的RGB分量
        r1 = (current >> 11) & 0x1F
        g1 = (current >> 5) & 0x3F
        b1 = current & 0x1F
        
        r2 = (color >> 11) & 0x1F
        g2 = (color >> 5) & 0x3F
        b2 = color & 0x1F
        
        # 混合颜色
        r = int(r1 * (1 - alpha) + r2 * alpha)
        g = int(g1 * (1 - alpha) + g2 * alpha)
        b = int(b1 * (1 - alpha) + b2 * alpha)
        
        # 合成新颜色
        new_color = (r << 11) | (g << 5) | b
        self.pixel(x, y, new_color)

# 修改 Display 类以支持动画更新
class Display:
    def __init__(self, width, height, spi_bus, dc_pin, cs_pin, rst_pin):
        # ... 保持原有初始化代码 ...
        self.last_update = time.ticks_ms()
        
    def refresh(self):
        current_time = time.ticks_ms()
        if self.root:
            # 更新动画
            self.root.update_animations()
            
            # 清空位图
            self._bitmap.fill_rect(0, 0, self.width, self.height, 0x0000)
            
            # 重新渲染
            self.render_widget(self.root)
            
            # 刷新到显示屏
            self.driver.refresh(self._bitmap)
            
        self.last_update = current_time
        
    def render_widget(self, widget):
        if hasattr(widget, 'get_bitmap'):
            bitmap = widget.get_bitmap()
            
            # 应用缩放
            if widget.scale != 1.0:
                scaled_width = int(widget.width * widget.scale)
                scaled_height = int(widget.height * widget.scale)
                scaled_x = widget.x + (widget.width - scaled_width) // 2
                scaled_y = widget.y + (widget.height - scaled_height) // 2
                
                # 简单的最近邻缩放
                for dy in range(scaled_height):
                    for dx in range(scaled_width):
                        src_x = int(dx / widget.scale)
                        src_y = int(dy / widget.scale)
                        color = bitmap.pixel(src_x, src_y)
                        self._bitmap.blend_pixel(scaled_x + dx, scaled_y + dy, color, widget.alpha)
            else:
                # 正常绘制（带透明度）
                for dy in range(widget.height):
                    for dx in range(widget.width):
                        color = bitmap.pixel(dx, dy)
                        self._bitmap.blend_pixel(widget.x + dx, widget.y + dy, color, widget.alpha)
        
        for child in widget.children:
            self.render_widget(child)