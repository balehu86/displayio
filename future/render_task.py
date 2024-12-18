# ./core/render_task.py

import time
from heapq import heappush, heappop  # 用于优先级队列管理任务



class TaskScheduler:
    """任务调度器"""
    def __init__(self):
        self.task_queue = []  # 优先级队列存储任务

    def add_task(self, callback, period, priority=10):
        """添加一个新任务"""
        task = Task(callback, period, priority)
        heappush(self.task_queue, task)

    def run(self):
        """运行调度器"""
        while True:
            current_time = time.ticks_ms()
            if self.task_queue:
                task = self.task_queue[0]  # 查看队列中的最高优先级任务
                if time.ticks_diff(task.next_run, current_time) <= 0:
                    heappop(self.task_queue)  # 移除任务
                    task.callback()          # 执行任务
                    if not task.one_shot:    # 如果不是单次任务
                        task.next_run = current_time + task.period
                        heappush(self.task_queue, task)  # 重新放入队列
            time.sleep_ms(2)  # 短暂休眠以降低 CPU 占用率


class RenderTask:
    def __init__(self,chunk_size=10):
        """
        初始化渲染任务
        
        Args:
            task_func (callable): 需要执行的渲染任务函数
            chunk_size (int): 每次渲染的块大小，默认为10
        """
        self.chunk_size = chunk_size
        self.current_progress = 0
        self.total_items = None
        self.completed = False
        self._initialize_task()
        self.completed = False

    def new_task(self, task_func):
        pass

    def _initialize_task(self):
        """
        初始化任务，获取总数据量
        子类应该重写此方法来设置 self.total_items
        """
        pass

    def is_completed(self):
        if self.compiled():
            return True
        else:
            return False
    
    def __iter__(self):
        """迭代器接口"""
        return self
    
    def __next__(self):
        """
        迭代器的下一步方法，支持分块渲染
        
        Returns:
            float: 当前渲染进度 (0.0 - 1.0)
        """
        if self.completed:
            raise StopIteration
        
        # 执行一个渲染块
        start = self.current_progress
        end = min(start + self.chunk_size, self.total_items)
        
        try:
            self.task_func(start, end)
            self.current_progress = end
            
            # 检查是否完成
            if self.current_progress >= self.total_items:
                self.completed = True
            
            # 返回进度
            return self.current_progress / self.total_items
        
        except Exception as e:
            print(f"Render task failed: {e}")
            self.completed = True
            raise StopIteration
    

class RenderLoop:
    def __init__(self):
        self.render_queue=[]
    
    def render(self):
        current_task:RenderTask = None
        while True:
            if current_task.is_completed():
                current_task= self.render_queue.pop(0)
            try:
                next(current_task())
            except Exception as e:
                raise e

    def add_task(self, task):
        self.render_queue.append(task)