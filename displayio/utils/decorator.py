import time

def timeit(func):
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = func(*args, **kwargs)
        diff=time.ticks_diff(time.ticks_us(), t)/1000
        print("\033[32m"+func.__name__+"\033[0m"+" "*(20-len(func.__name__))+" executed in"+" "*(6-len(str(diff)))+"\033[31m"+str(diff)+" ms"+"\033[0m")
        return result
    return new_func
def fps(func):
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = func(*args, **kwargs)
        diff=time.ticks_diff(time.ticks_us(), t)/1000
        print("\033[32m"+func.__name__+"\033[0m"+" "*(20-len(func.__name__))+" executed in"+" "*(6-len(str(diff)))+"\033[31m"+str(diff)+" ms"+" fps:"+f"{1000/diff}"+"\033[0m")
        return result
    return new_func

def measure_iterations(func):
    def wrapper(*args, **kwargs):
        iterations = 0
        start_time = time.ticks_ms()
        while True:
            func(*args, **kwargs)
            iterations += 1
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            if elapsed >= 1000:  # 每隔1秒输出一次
                print(f"FPS: {iterations}")
                iterations = 0
                start_time = time.ticks_ms()
    return wrapper