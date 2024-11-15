def rle_encode(data):
    """
    优化的RLE压缩函数：
    - 单个0直接存储
    - 连续多个0使用[count,0]格式压缩
    - 非0值直接存储
    
    Args:
        data: 原始数据列表
    Returns:
        压缩后的数据列表，格式：[值,值,[连续0数量,0],值,...]
    """
    if not data:
        return []
        
    result = []
    i = 0
    length = len(data)
    
    while i < length:
        if data[i] != 0:  # 非0值直接存储
            result.append(data[i])
            i += 1
        else:  # 处理0值
            # 计算连续的0的数量
            count = 1
            j = i + 1
            while j < length and data[j] == 0:
                count += 1
                j += 1
            
            if count == 1:  # 单个0直接存储
                result.append(0)
            else:  # 多个0进行压缩
                result.append([count, 0])
            i = j
    
    return result

def rle_decode(rle_data):
    """
    RLE解压缩函数
    
    Args:
        rle_data: 压缩后的数据，格式：[值,值,[连续0数量,0],值,...]
    Returns:
        解压后的原始数据列表
    """
    result = []
    
    for item in rle_data:
        if isinstance(item, list):  # 压缩的连续0
            result.extend([0] * item[0])
        else:  # 直接存储的值
            result.append(item)
    
    return result
        