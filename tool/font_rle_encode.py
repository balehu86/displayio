def compress(data:list) -> list:
    result = []
    zero_count = 0
    for byte in data:
        if byte == 0:
            zero_count += 1
            if zero_count == 255:  # 避免溢出
                result.extend([0, 255])
                zero_count = 0
        else:
            if zero_count > 0:
                result.extend([0, zero_count])
                zero_count = 0
            result.append(byte)
    
    # 处理结尾的零
    if zero_count > 0:
        result.extend([0, zero_count])
    
    return result


def decompress(compressed):
    result = bytearray()
    i = 0
    while i < len(compressed):
        if compressed[i] == 0:
            zero_count = compressed[i+1]
            result.extend([0] * zero_count)
            i += 2
        else:
            result.append(compressed[i])
            i += 1
    
    return result
