import time

def timeit(func):
    def new_func(*args, **kwargs):
        t = time.ticks_ms()
        result = func(*args, **kwargs)
        diff=time.ticks_diff(time.ticks_ms(), t)
        print("\033[32m"+func.__name__+"\033[0m"+" "*(20-len(func.__name__))+" executed in"+" "*(10-len(str(diff)))+"\033[31m"+str(diff)+" ms"+"\033[0m")
        return result
    return new_func
def fps(func):
    def new_func(*args, **kwargs):
        t = time.ticks_ms()
        result = func(*args, **kwargs)
        diff=time.ticks_diff(time.ticks_ms(), t)
        print("\033[32m"+func.__name__+"\033[0m"+" "*(20-len(func.__name__))+" executed in"+" "*(6-len(str(diff)))+"\033[31m"+str(diff)+" ms"+" fps:"+f"{1000/diff}"+"\033[0m")
        return result
    return new_func