import micropython # type: ignore
@micropython.native
def hex_font_to_bitmap(hex_data, width=16, height=16, scale=1,
                       foreground=0xffff, rle=False):
    """将点阵数据转换为带透明背景的Bitmap
    
    Args:
        hex_data: 点阵数据。
                 当rle=False时，为一维列表，每行需要width//8个字节表示width个像素
                 当rle=True时，为RLE压缩后的数据（[0,非0值,非0值,[3,0],非0值]格式）
        width: 字符宽度（像素），必须是8的倍数
        height: 字符高度（像素）
        foreground: 前景色
        rle: 是否为RLE压缩数据，默认False
    
    Returns:
        Bitmap: 生成的位图对象
    """
    from ..core.bitmap import Bitmap
    
    if width % 8 != 0:
        raise ValueError("宽度必须是8的倍数")
    
    if scale < 1:
        raise ValueError("缩放倍数必须大于等于1")
    
    if foreground==0x0000:
        raise ValueError("字体颜色不能为0x0000,因为无法和字符背景色区分")
    
    # 计算缩放后的宽度和高度
    scaled_width = width * scale
    scaled_height = height * scale    

    bytes_per_row = width // 8 # 每行需要的字节数
    expected_data_length = height * bytes_per_row
    bitmap = Bitmap(transparent_color=0x0000)
    bitmap.init(width=scaled_width, height=scaled_height)
    
    def draw_scaled_pixel(x, y, color):
        """在缩放后的位图上绘制像素块"""
        start_x = x * scale
        start_y = y * scale
        for dy in range(scale):
            for dx in range(scale):
                bitmap.pixel(start_x + dx, start_y + dy, color)

    if not rle:
        # 原始数据模式
        if len(hex_data) != expected_data_length:
            raise ValueError(f"hex_data必须是长度为{expected_data_length}的bytearray\
                             ,每行需要{bytes_per_row}个字节表示{width}个像素")
            
        for y in range(height):
            row_start = y * bytes_per_row
            row_end = row_start + bytes_per_row
            row_bytes = hex_data[row_start:row_end]
            
            for byte_index, byte_value in enumerate(row_bytes):
                if byte_value:  # 只处理非零值
                    for bit_pos in range(8):
                        if byte_value & (0x80 >> bit_pos):
                            x = byte_index * 8 + bit_pos
                            draw_scaled_pixel(x, y, foreground)
        return bitmap
    else:
        # RLE压缩数据模式
        current_row = 0
        row_byte = 0
        i = 0
        
        while i < len(hex_data) and current_row < height:
            byte_value = hex_data[i]
            
            if byte_value == 0:
                # 读取下一个字节作为连续0的数量
                zero_count = hex_data[i + 1]
                i += 2
                
                # 计算跳过的行数和字节位置
                bytes_to_skip = zero_count
                while bytes_to_skip > 0:
                    # 计算当前行还能放几个字节
                    bytes_remaining_in_row = bytes_per_row - row_byte
                    if bytes_to_skip >= bytes_remaining_in_row:
                        # 跳到下一行
                        bytes_to_skip -= bytes_remaining_in_row
                        current_row += 1
                        row_byte = 0
                    else:
                        # 在当前行前进
                        row_byte += bytes_to_skip
                        bytes_to_skip = 0
                        
                    if current_row >= height:
                        return bitmap
            else:
                # 处理非零字节
                if byte_value:  # 只处理非零值
                    base_x = row_byte * 8
                    for bit_pos in range(8):
                        if byte_value & (0x80 >> bit_pos):
                            x = base_x + bit_pos
                            if x < width:
                                draw_scaled_pixel(x, current_row, foreground)
                
                i += 1
                row_byte += 1
                if row_byte >= bytes_per_row:
                    row_byte = 0
                    current_row += 1

    return bitmap

    