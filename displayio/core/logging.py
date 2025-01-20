import io
import sys
import time

CRITICAL = 5
ERROR = 4
WARNING = 3
INFO = 2
DEBUG = 1
NOTSET = 0

_level_dict = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
    NOTSET: "NOTSET",
}

class Logger:

    CRITICAL = 5
    ERROR = 4
    WARNING = 3
    INFO = 2
    DEBUG = 1
    NOTSET = 0

    __slots__ = ('name', 'level', 'stream', 'fmt', '_initialized')
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name=None, level=None, stream=None):
        if hasattr(self, '_initialized'):  # 检查是否已初始化,避免覆盖参数
            return
        self.name = name or "root"
        self.level = level if level is not None else INFO
        self.stream = stream if stream else sys.stderr
        self.fmt = "%(levelname)s:%(name)s:%(message)s"
        self._initialized = True

    def setLevel(self, level):
        self.level = level

    def isEnabledFor(self, level):
        return level >= self.level

    def _format_message(self, level, msg):
        try:
            t = time.localtime()  # 获取本地时间元组
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])
            return f"{timestamp} {self.fmt}" % {
                "levelname": _level_dict.get(level, "UNKNOWN"),
                "name": self.name,
                "message": msg}
        except KeyError as e:
            return f"LOG FORMAT ERROR: {e}"

    def log(self, level, msg, *args):
        if self.isEnabledFor(level):
            if args:
                if isinstance(args[0], dict):
                    args = args[0]
                msg = msg % args
            formatted_msg = self._format_message(level, msg)
            self.stream.write(formatted_msg + "\n")

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exception(self, msg, *args, exc=None):
        self.error(msg, *args)  # 打印错误信息
        if exc:
            buf = io.StringIO()
            sys.print_exception(exc, buf)  # 使用MicroPython提供的方法输出堆栈信息
            self.error("%s", buf.getvalue())  # 将堆栈信息加入日志

# 创建全局logger实例
logger = Logger()
# 便捷的全局函数
def debug(msg, *args): logger.debug(msg, *args)
def info(msg, *args): logger.info(msg, *args)
def warning(msg, *args): logger.warning(msg, *args)
def error(msg, *args): logger.error(msg, *args)
def critical(msg, *args): logger.critical(msg, *args)
def exception(msg, *args, exc=None): logger.exception(msg, *args, exc=exc)