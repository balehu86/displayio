# ./core/bitmap.py
import framebuf

class Bitmap:
    # 支持的颜色格式
    MONO_VLSB = framebuf.MONO_VLSB
    MONO_HLSB = framebuf.MONO_HLSB
    MONO_HMSB = framebuf.MONO_HMSB
    RGB565 = framebuf.RGB565
    GS2_HMSB = framebuf.GS2_HMSB
    GS4_HMSB = framebuf.GS4_HMSB
    GS8 = framebuf.GS8

    def __init__(self, width=0, height=0, format=framebuf.RGB565):
        self.width = width
        self.height = height
        buffer_size = width * height
        if format == framebuf.RGB565:
            buffer_size *= 2
        self.buffer = bytearray(buffer_size)
        self.fb = framebuf.FrameBuffer(self.buffer, width, height, format)
        
        # 使用bytearray存储透明度信息，每个字节存储8个像素
        self._mask = bytearray((width * height + 7) // 8)
        # 缓存常用的掩码值
        self._bit_masks = [1 << i for i in range(8)]

    def _swap_bytes(self, color):
        """交换颜色值的高低字节"""
        return ((color >> 8) | (color << 8)) & 0xFFFF
        
    def _get_mask_index(self, x, y):
        """获取遮罩的字节索引和位索引"""
        pos = y * self.width + x
        return pos >> 3, pos & 0x07
    
    def pixel(self, x, y, color=None, transparent=False):
        """获取或设置像素点"""
        # 若超出位图范围，直接返回
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        
        byte_idx, bit_idx = self._get_mask_index(x, y)
        bit_mask = self._bit_masks[bit_idx]
        
        if color is None:
            if self._mask[byte_idx] & bit_mask:  # 不透明
                return self._swap_bytes(self.fb.pixel(x, y))
            return None
            
        self.fb.pixel(x, y, self._swap_bytes(color))
        if transparent:
            self._mask[byte_idx] &= ~bit_mask
        else:
            self._mask[byte_idx] |= bit_mask

    def fill_rect(self, x, y, width, height, color, transparent=False):
        """填充矩形区域"""
        # 使用FrameBuffer的原生fill_rect进行填充
        self.fb.fill_rect(x, y, width, height, self._swap_bytes(color))
        
        # 批量设置透明度
        start_x = max(0, x)
        start_y = max(0, y)
        end_x = min(self.width, x + width)
        end_y = min(self.height, y + height)
        
        if transparent:
            # 如果是透明的，直接将对应区域的位清零
            for cy in range(start_y, end_y):
                row_start = (cy * self.width + start_x) >> 3
                row_end = (cy * self.width + end_x - 1) >> 3
                start_bit = start_x & 0x07
                end_bit = (end_x - 1) & 0x07
                
                if row_start == row_end:
                    # 同一个字节内
                    mask = ((1 << (end_bit - start_bit + 1)) - 1) << start_bit
                    self._mask[row_start] &= ~mask
                else:
                    # 第一个字节
                    self._mask[row_start] &= ~(0xFF << start_bit)
                    # 中间的字节
                    for i in range(row_start + 1, row_end):
                        self._mask[i] = 0
                    # 最后一个字节
                    self._mask[row_end] &= ~((1 << (end_bit + 1)) - 1)
        else:
            # 如果是不透明的，直接将对应区域的位置1
            for cy in range(start_y, end_y):
                row_start = (cy * self.width + start_x) >> 3
                row_end = (cy * self.width + end_x - 1) >> 3
                start_bit = start_x & 0x07
                end_bit = (end_x - 1) & 0x07
                
                if row_start == row_end:
                    # 同一个字节内
                    mask = ((1 << (end_bit - start_bit + 1)) - 1) << start_bit
                    self._mask[row_start] |= mask
                else:
                    # 第一个字节
                    self._mask[row_start] |= (0xFF << start_bit)
                    # 中间的字节
                    for i in range(row_start + 1, row_end):
                        self._mask[i] = 0xFF
                    # 最后一个字节
                    self._mask[row_end] |= ((1 << (end_bit + 1)) - 1)

    def blit(self, source, sx=0, sy=0, sw=None, sh=None, dx=0, dy=0):
        """将源bitmap复制到当前bitmap"""
        if sw is None:
            sw = source.width
        if sh is None:
            sh = source.height
            
        # 计算有效的复制区域
        src_start_x = max(0, -sx)
        src_start_y = max(0, -sy)
        src_end_x = min(sw, source.width - sx)
        src_end_y = min(sh, source.height - sy)
        
        dst_start_x = max(0, dx)
        dst_start_y = max(0, dy)
        dst_end_x = min(self.width, dx + sw)
        dst_end_y = min(self.height, dy + sh)
        
        # 计算实际要复制的宽度和高度
        copy_width = min(src_end_x - src_start_x, dst_end_x - dst_start_x)
        copy_height = min(src_end_y - src_start_y, dst_end_y - dst_start_y)
        
        if copy_width <= 0 or copy_height <= 0:
            return
            
        # 按行复制像素和透明度信息
        for y in range(copy_height):
            src_y = sy + src_start_y + y
            dst_y = dy + y
            
            for x in range(copy_width):
                src_x = sx + src_start_x + x
                dst_x = dx + x
                
                # 检查源像素是否透明
                src_byte_idx, src_bit_idx = source._get_mask_index(src_x, src_y)
                if source._mask[src_byte_idx] & source._bit_masks[src_bit_idx]:
                    # 如果源像素不透明，则复制
                    color = source.fb.pixel(src_x, src_y)
                    self.fb.pixel(dst_x, dst_y, self._swap_bytes(self._swap_bytes(color)))
                    
                    # 设置目标像素为不透明
                    dst_byte_idx, dst_bit_idx = self._get_mask_index(dst_x, dst_y)
                    self._mask[dst_byte_idx] |= self._bit_masks[dst_bit_idx]
