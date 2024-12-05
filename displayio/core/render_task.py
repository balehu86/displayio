# ./core/render_task.py

class RenderTask:
    def __init__(self):
        self.completed = False
    def __iter__(self):
        return self
    def __next__(self):
        if self.completed:
            raise StopIteration
        return self.completed