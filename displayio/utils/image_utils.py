def hex_to_bitmap(hex_data, fg_color=0xFFFF, bg_color=0x0000, width=None):
    """将16进制数据转换为Bitmap"""
    from core import Bitmap
    
    if width is None:
        # 假设每行数据是完整的字节
        width = len(hex_data[0].replace(" ", "").replace("0x", "")) * 4
    
    height = len(hex_data)
    bitmap = Bitmap(width, height)
    bitmap.fill_rect(0, 0, width, height, bg_color)
    
    for y, hex_row in enumerate(hex_data):
        # 清理数据
        hex_row = hex_row.replace(" ", "").replace("0x", "")
        
        # 处理每个16进制字符
        for x, hex_char in enumerate(hex_row):
            bits = bin(int(hex_char, 16))[2:].zfill(4)
            for bit_pos, bit in enumerate(bits):
                if bit == '1':
                    pixel_x = x * 4 + bit_pos
                    if pixel_x < width:  # 确保不超出宽度
                        bitmap.pixel(pixel_x, y, fg_color)
    
    return bitmap