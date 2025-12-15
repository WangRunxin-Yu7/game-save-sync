"""
日志管理器 - 单例模式
"""
import threading
from config_util import get_logging
from .logger import Logger

_LOGGER = None
_LOCK = threading.Lock()


def _init():
    global _LOGGER
    with _LOCK:
        if _LOGGER is None:
            cfg = get_logging()
            _LOGGER = Logger(log_dir=cfg.get("log_dir", "./logs"), max_logs=cfg.get("max_logs", 1000))


def reload_logger():
    """
    重新加载日志配置并重建日志器（下次写入按新配置）
    """
    global _LOGGER
    with _LOCK:
        cfg = get_logging()
        _LOGGER = Logger(log_dir=cfg.get("log_dir", "./logs"), max_logs=cfg.get("max_logs", 1000))


def _ensure():
    if _LOGGER is None:
        _init()


def log(template: str, **kwargs):
    """
    简单外部接口：
    - 传入字符串与参数，按 str.format(**kwargs) 格式化
    - 写入一条包含时间戳的日志
    """
    _ensure()
    msg = template
    if kwargs:
        try:
            msg = template.format(**kwargs)
        except Exception:
            # 若格式化失败，附加原始参数
            msg = f"{template} | {kwargs}"
    _LOGGER.write(msg)
