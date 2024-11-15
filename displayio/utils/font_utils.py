def hex_font_to_bitmap(hex_data, width=8, height=8, foreground=0xffff, rle=False):
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
        
    bytes_per_row = width // 8 # 每行需要的字节数
    expected_data_length = height * bytes_per_row
    bitmap = Bitmap(width, height, format=Bitmap.RGB565)
    
    if not rle:
        # 原始数据模式
        if not isinstance(hex_data, (list, tuple)) or len(hex_data) != expected_data_length:
            raise ValueError(f"hex_data必须是长度为{expected_data_length}的一维列表，每行需要{bytes_per_row}个字节表示{width}个像素")
            
        for y in range(height):
            row_start = y * bytes_per_row
            row_end = row_start + bytes_per_row
            row_bytes = hex_data[row_start:row_end]
            
            for byte_index, byte_value in enumerate(row_bytes):
                if byte_value:  # 只处理非零值
                    for bit_pos in range(8):
                        if byte_value & (0x80 >> bit_pos):
                            x = byte_index * 8 + bit_pos
                            bitmap.pixel(x, y, foreground, transparent=False)
        return bitmap
    else:
        # RLE压缩数据模式
        current_row = 0
        row_byte = 0
        
        for item in hex_data:
            if isinstance(item, list):  # 压缩的连续0: [count, 0]
                # 计算跳过的行数和位置
                count = item[0]
                rows_to_skip = count // bytes_per_row
                current_row += rows_to_skip
                remaining_bytes = count % bytes_per_row
                row_byte = (row_byte + remaining_bytes) % bytes_per_row
                if row_byte == 0 and remaining_bytes > 0:
                    current_row += 1
            else:  # 直接存储的值（0或非0）
                if current_row < height:
                    if item:  # 只处理非零值
                        base_x = row_byte * 8
                        byte_value = item
                        # 一次性处理一个字节的所有位
                        for bit_pos in range(8):
                            if byte_value & (0x80 >> bit_pos):
                                x = base_x + bit_pos
                                if x < width:
                                    bitmap.pixel(x, current_row, foreground, transparent=False)
                
                    row_byte += 1
                if row_byte >= bytes_per_row:
                    row_byte = 0
                    current_row += 1

            if current_row >= height:
                return bitmap

    return bitmap


    