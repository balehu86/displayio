def hex_font_to_bitmap(hex_data, width=8, height=8, foreground=0xFFFF):
    """将点阵数据转换为带透明背景的Bitmap
    
    Args:
        hex_data: 点阵数据（一维列表）。对于16*16的字体，每行需要2个字节表示16个像素；
                对于8*8的字体，每行需要1个字节表示8个像素。
        width: 字符宽度（像素），必须是8的倍数
        height: 字符高度（像素）
        foreground: 前景色
    
    Returns:
        Bitmap: 生成的位图对象
    """
    from ..core.bitmap import Bitmap
    
    # 验证输入参数
    bytes_per_row = width // 8  # 每行需要的字节数
    expected_data_length = height * bytes_per_row
    
    if not isinstance(hex_data, (list, tuple)) or len(hex_data) != expected_data_length:
        raise ValueError(f"hex_data必须是长度为{expected_data_length}的一维列表，每行需要{bytes_per_row}个字节表示{width}个像素")
    
    if width % 8 != 0:
        raise ValueError("宽度必须是8的倍数")
        
    bitmap = Bitmap(width, height)
    # 默认所有像素都是透明的（alpha=0）
    
    for y in range(height):
        # 获取这一行的所有字节
        row_start = y * bytes_per_row
        row_end = row_start + bytes_per_row
        row_bytes = hex_data[row_start:row_end]
        
        # 处理这一行的每个字节
        for byte_index, byte_value in enumerate(row_bytes):
            # 处理这个字节的8个位
            for bit_pos in range(8):
                x = byte_index * 8 + bit_pos  # 计算实际的x坐标
                if byte_value & (0x80 >> bit_pos):
                    bitmap.pixel(x, y, foreground, 255)
    
    return bitmap