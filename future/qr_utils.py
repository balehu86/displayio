from ..core.bitmap import Bitmap

class QRGenerator:
    """简单的QR码生成器(仅支持数字模式,Version 1)"""
    
    def __init__(self):
        # QR码版本1的基本参数
        self.version = 1
        self.size = 21  # 版本1的矩阵大小为21x21
        self.matrix = [[False] * self.size for _ in range(self.size)]
        
    def _place_finder_pattern(self, x, y):
        """放置探测图案"""
        # 外部边框
        for i in range(7):
            self.matrix[y][x+i] = True
            self.matrix[y+6][x+i] = True
            self.matrix[y+i][x] = True
            self.matrix[y+i][x+6] = True
        
        # 内部实心方块
        for i in range(3):
            for j in range(3):
                self.matrix[y+2+i][x+2+j] = True

    def _place_timing_patterns(self):
        """放置定位图案"""
        # 水平定位图案
        for i in range(8, self.size-8):
            self.matrix[6][i] = i % 2 == 0
        
        # 垂直定位图案
        for i in range(8, self.size-8):
            self.matrix[i][6] = i % 2 == 0

    def _place_alignment_pattern(self):
        """放置校正图案(版本1不需要)"""
        pass  # Version 1 没有校正图案

    def _encode_numeric(self, data):
        """编码数字数据"""
        # 简化实现：仅支持数字，不包含纠错码
        bits = []
        
        # 模式指示符(数字模式: 0001)
        bits.extend([0, 0, 0, 1])
        
        # 字符计数指示符(版本1-数字模式: 10位)
        length = len(data)
        for i in range(9, -1, -1):
            bits.append((length >> i) & 1)
            
        # 数据编码
        groups = [data[i:i+3] for i in range(0, len(data), 3)]
        for group in groups:
            value = int(group)
            # 每3个数字用10位表示
            if len(group) == 3:
                for i in range(9, -1, -1):
                    bits.append((value >> i) & 1)
            # 最后2个数字用7位表示
            elif len(group) == 2:
                for i in range(6, -1, -1):
                    bits.append((value >> i) & 1)
            # 最后1个数字用4位表示
            else:
                for i in range(3, -1, -1):
                    bits.append((value >> i) & 1)
                    
        return bits

    def _apply_mask_pattern(self, mask_number=0):
        """应用掩码图案"""
        # 使用最简单的掩码模式：(row + column) mod 2 == 0
        for y in range(self.size):
            for x in range(self.size):
                if (x + y) % 2 == 0:  # 掩码条件
                    self.matrix[y][x] = not self.matrix[y][x]

    def generate(self, data):
        """生成QR码矩阵
        
        Args:
            data: 要编码的数字字符串
        """
        # 放置固定图案
        self._place_finder_pattern(0, 0)  # 左上
        self._place_finder_pattern(self.size-7, 0)  # 右上
        self._place_finder_pattern(0, self.size-7)  # 左下
        self._place_timing_patterns()
        
        # 编码数据
        bits = self._encode_numeric(data)
        
        # 放置数据位
        bit_index = 0
        for i in range(len(bits)):
            if bit_index < len(bits):
                x = self.size - 1 - (i // self.size)
                y = self.size - 1 - (i % self.size)
                if self.matrix[y][x] is False:  # 只在空位置放置数据
                    self.matrix[y][x] = bits[bit_index] == 1
                    bit_index += 1
        
        # 应用掩码
        self._apply_mask_pattern()
        
        return self.matrix

def generate_qr_bitmap(data, box_size=8, border=4, foreground=0xFFFF, background=0x0000):
    """生成QR码位图
    
    Args:
        data: 要编码的数字字符串
        box_size: 每个QR码方块的像素大小
        border: 边框宽度(方块数)
        foreground: 前景色(QR码颜色)
        background: 背景色
    
    Returns:
        Bitmap: 生成的QR码位图对象
    """
    # 生成QR码矩阵
    qr = QRGenerator()
    matrix = qr.generate(data)
    
    # 计算实际尺寸
    matrix_size = len(matrix)
    total_size = (matrix_size + border * 2) * box_size
    
    # 创建位图
    bitmap = Bitmap(total_size, total_size, format=Bitmap.RGB565)
    
    # 填充背景
    if background != 0x0000:
        bitmap.fill_rect(0, 0, total_size, total_size, background, transparent=False)
    
    # 绘制QR码
    for y in range(matrix_size):
        for x in range(matrix_size):
            if matrix[y][x]:
                pixel_x = (x + border) * box_size
                pixel_y = (y + border) * box_size
                bitmap.fill_rect(
                    pixel_x, pixel_y,
                    box_size, box_size,
                    foreground,
                    transparent=False
                )
    
    return bitmap