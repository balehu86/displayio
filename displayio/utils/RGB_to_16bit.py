def rgb(r, g, b):
    """将RGB值(0-255)转换为16位色"""
    r = (r >> 3) & 0x1F
    g = (g >> 2) & 0x3F
    b = (b >> 3) & 0x1F
    return (r << 11) | (g << 5) | b