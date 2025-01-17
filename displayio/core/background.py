class Background:
    def __init__(self, color=None, pic=None):
        if color is None and pic is None:
            raise ValueError('Background 类初始化错误, color 和 pic 参数必须二选一')
        self.color = color
        self.pic = pic