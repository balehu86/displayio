# core/bitmap.py
class Bitmap:
    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height
        self.buffer = bytearray(width * height * 2)  # 16-bit color
        self._alpha_mask = bytearray(width * height)  # 8-bit alpha channel (0=transparent, 255=opaque)
    def pixel(self, x, y, color=None, alpha=None):
        """获取或设置像素点
        
        Args:
            x, y: 坐标
            color: 要设置的颜色值，None表示获取当前颜色
        Returns:
            获取模式下返回当前颜色值
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        pos = (y * self.width + x) * 2
        alpha_pos = y * self.width + x

        if color is None:
            if self._alpha_mask[alpha_pos] == 0:  # 如果是透明像素
                return None
            return (self.buffer[pos] << 8) | self.buffer[pos + 1]
        
        self.buffer[pos] = color >> 8
        self.buffer[pos + 1] = color & 0xFF
        if alpha is not None:
            self._alpha_mask[alpha_pos] = alpha

    def fill_rect(self, x, y, width, height, color, alpha=255):
        for dy in range(height):
            for dx in range(width):
                self.pixel(x + dx, y + dy, color, alpha)
                
    def blit(self, source, sx=0, sy=0, sw=None, sh=None, dx=0, dy=0):
        """将源bitmap复制到当前bitmap
        
        Args:
            source: 源Bitmap对象
            sx, sy: 源bitmap的起始坐标
            sw, sh: 要复制的宽度和高度
            dx, dy: 目标位置
        """
        if sw is None:
            sw = source.width
        if sh is None:
            sh = source.height
            
        for y in range(sh):
            for x in range(sw):
                color = source.pixel(sx + x, sy + y)
                if color is not None:  # 只复制非透明像素
                    alpha_pos = (sy + y) * source.width + (sx + x)
                    alpha = source._alpha_mask[alpha_pos]
                    self.pixel(dx + x, dy + y, color, alpha)